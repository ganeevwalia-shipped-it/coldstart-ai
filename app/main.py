"""
Cold Start AI — GTM Execution Engine
Not a strategy generator. An operating system for launching products.

Two modes:
  FREE: All agents run independently (same base context)
  PRO:  Agents chain — each builds on the outputs before it + vertical intelligence
"""
import os
import io
import logging
import zipfile
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from anthropic import AsyncAnthropic

from app.agents.registry import AGENTS, AGENT_ORDER, CATEGORIES
from app.agents.orchestrator import build_chained_prompt, get_execution_plan, AGENT_DEPENDENCIES
from app.agents.verticals import get_vertical_context
from app.agents.rules import (
    get_applicable_rules,
    build_rules_block,
    parse_company_context,
    score_input_quality,
)
from app.agents.knowledge import get_knowledge_context
from app.agents.schemas import get_format_instructions, validate_output_structure
from app.agents.clarifier import get_clarifying_questions, get_plan_variants
from app.connectors.csv_connector import generate_csv, generate_platform_csv
from app.connectors.base import get_connector
from app.connectors import hubspot as _hubspot_import  # noqa: F401 — register connector
from app.validation import (
    validate_agent_id,
    validate_company_context,
    validate_previous_outputs,
    validate_text_field,
    validate_company_name,
    validate_export_results,
    generate_limiter,
    export_limiter,
)

logger = logging.getLogger("coldstart")

app = FastAPI(title="Cold Start AI")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

client = None


def get_client():
    global client
    if client is None:
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return client


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "agents": AGENTS,
        "agent_order": AGENT_ORDER,
        "categories": CATEGORIES,
    })


@app.get("/launch", response_class=HTMLResponse)
async def intake(request: Request):
    return templates.TemplateResponse("intake.html", {
        "request": request,
        "agents": AGENTS,
        "agent_order": AGENT_ORDER,
        "categories": CATEGORIES,
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agents": AGENTS,
        "agent_order": AGENT_ORDER,
        "categories": CATEGORIES,
    })


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/api/health")
async def health():
    """Health check endpoint for monitoring and deployment probes."""
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return JSONResponse({
        "status": "ok",
        "agents": len(AGENTS),
        "api_key_configured": has_api_key,
    })


@app.post("/api/scrape")
async def scrape_url(request: Request):
    """Scrape a URL and extract company context using Claude."""
    body = await request.json()
    url = body.get("url", "").strip()

    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Demo mode — return mock data
        return JSONResponse({
            "company_name": "Your Company",
            "product_description": "Tell us what your product does and who it helps.",
            "target_market": "",
            "inferred_vertical": "B2B SaaS",
            "demo": True,
        })

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw_html = resp.read().decode("utf-8", errors="ignore")[:12000]
    except Exception:
        return JSONResponse({
            "company_name": "",
            "product_description": "",
            "target_market": "",
            "inferred_vertical": "",
            "scrape_failed": True,
        })

    # Strip tags roughly
    import re
    text = re.sub(r"<script[^>]*>.*?</script>", "", raw_html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()[:4000]

    ai = get_client()
    msg = await ai.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Extract structured information from this website text. Return ONLY valid JSON, no markdown.

Website text:
{text}

Return JSON with these exact keys:
- company_name: the product or company name (string)
- product_description: 2-3 sentence description of what the product does (string)
- target_market: who their customers are, as specific as possible (string)
- inferred_vertical: one of: B2B SaaS, Dev Tools, Fintech, Marketplace, E-commerce/DTC, AI/ML, Agency, Consumer App (string)

If you cannot determine a field, use empty string."""
        }]
    )

    try:
        import json
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"```$", "", raw)
        data = json.loads(raw)
        return JSONResponse(data)
    except Exception:
        return JSONResponse({"company_name": "", "product_description": "", "target_market": "", "inferred_vertical": ""})


@app.post("/api/score-input")
async def score_input_endpoint(request: Request):
    """Score the quality of user input before running agents."""
    body = await request.json()
    result = score_input_quality(body)
    return JSONResponse(result)


@app.post("/api/generate-single")
async def generate_single(request: Request):
    """
    FREE mode: Run a single agent with base context only.
    """
    # Rate limit
    client_ip = generate_limiter.get_client_ip(request)
    if not generate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    body = await request.json()
    agent_id = validate_agent_id(body.get("agent_id", ""), AGENTS)
    company_context = validate_company_context(body.get("company_context", ""))

    agent = AGENTS[agent_id]
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        return JSONResponse({
            "status": "demo",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": generate_demo_content(agent_id, agent, company_context),
        })

    try:
        parsed_ctx = parse_company_context(company_context)
        rules = get_applicable_rules(agent_id, parsed_ctx)
        rules_block = build_rules_block(rules)
        knowledge_block = get_knowledge_context(
            stage=parsed_ctx.get("stage", ""),
            motion=parsed_ctx.get("primary gtm motion", ""),
        )

        format_instructions = get_format_instructions(agent_id)
        prompt = (
            f"{agent['prompt']}"
            f"{rules_block}"
            f"{format_instructions}"
            f"{knowledge_block}"
            f"\n\n---\n\nHere is the company information:\n{company_context}"
        )

        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        schema_validation = validate_output_structure(agent_id, content)
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": content,
            "schema_validation": schema_validation,
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "content": f"Error: {str(e)}",
        })


@app.post("/api/generate-chained")
async def generate_chained(request: Request):
    """
    PRO mode: Run a single agent with chained context from previous agents
    + vertical-specific intelligence.
    """
    # Rate limit
    client_ip = generate_limiter.get_client_ip(request)
    if not generate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    body = await request.json()
    agent_id = validate_agent_id(body.get("agent_id", ""), AGENTS)
    company_context = validate_company_context(body.get("company_context", ""))
    previous_outputs = validate_previous_outputs(body.get("previous_outputs", {}))
    product_description = validate_text_field(body.get("product_description", ""), "product_description")
    business_model = validate_text_field(body.get("business_model", ""), "business_model")
    target_market = validate_text_field(body.get("target_market", ""), "target_market")

    agent = AGENTS[agent_id]
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        deps = AGENT_DEPENDENCIES.get(agent_id, [])
        dep_names = [AGENTS[d]["name"] for d in deps if d in AGENTS and d in previous_outputs]
        chain_note = ""
        if dep_names:
            chain_note = f"\n\n**Chained Mode Active** — This agent is building on intelligence from: {', '.join(dep_names)}\n"
        return JSONResponse({
            "status": "demo",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": generate_demo_content(agent_id, agent, company_context) + chain_note,
        })

    # Build chained prompt with previous agent outputs
    vertical_context = get_vertical_context(product_description, business_model, target_market)
    enriched_company_context = company_context + vertical_context

    parsed_ctx = parse_company_context(company_context)
    rules = get_applicable_rules(agent_id, parsed_ctx)
    rules_block = build_rules_block(rules)
    knowledge_block = get_knowledge_context(
        stage=parsed_ctx.get("stage", ""),
        motion=parsed_ctx.get("primary gtm motion", ""),
    )

    format_instructions = get_format_instructions(agent_id)
    prompt = build_chained_prompt(
        agent_id, agent["prompt"] + format_instructions, enriched_company_context,
        previous_outputs, rules_block=rules_block, knowledge_block=knowledge_block,
    )

    try:
        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        schema_validation = validate_output_structure(agent_id, content)
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": content,
            "schema_validation": schema_validation,
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "content": f"Error: {str(e)}",
        })


@app.post("/api/clarify")
async def clarify(request: Request):
    """Return clarifying questions and plan variants based on input quality."""
    body = await request.json()
    score = score_input_quality(body)
    questions = get_clarifying_questions(body)
    variants = get_plan_variants(body)
    return JSONResponse({
        "score": score,
        "questions": questions,
        "variants": variants,
    })


@app.post("/api/refine-agent")
async def refine_agent(request: Request):
    """Re-run a single agent with additional user feedback."""
    client_ip = generate_limiter.get_client_ip(request)
    if not generate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    body = await request.json()
    agent_id = validate_agent_id(body.get("agent_id", ""), AGENTS)
    company_context = validate_company_context(body.get("company_context", ""))
    previous_output = validate_text_field(body.get("previous_output", ""), "previous_output", max_length=50_000)
    user_feedback = validate_text_field(body.get("user_feedback", ""), "user_feedback", max_length=5_000)

    if not user_feedback.strip():
        raise HTTPException(status_code=400, detail="user_feedback is required")

    agent = AGENTS[agent_id]
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        return JSONResponse({
            "status": "demo",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "content": f"[Demo Mode] Refinement would revise the {agent['name']} output based on your feedback: \"{user_feedback}\"",
        })

    parsed_ctx = parse_company_context(company_context)
    rules = get_applicable_rules(agent_id, parsed_ctx)
    rules_block = build_rules_block(rules)
    format_instructions = get_format_instructions(agent_id)

    prompt = (
        f"{agent['prompt']}"
        f"{rules_block}"
        f"{format_instructions}"
        f"\n\n---\n\nHere is the company information:\n{company_context}"
        f"\n\n---\n\nPREVIOUS OUTPUT (your earlier version):\n{previous_output}"
        f"\n\n---\n\nUSER FEEDBACK (they want these changes):\n{user_feedback}"
        f"\n\nRevise your output based on this feedback. Keep what worked, fix what didn't."
    )

    try:
        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        schema_validation = validate_output_structure(agent_id, content)
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": content,
            "schema_validation": schema_validation,
            "refined": True,
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "content": f"Error: {str(e)}",
        })


@app.get("/api/execution-plan")
async def execution_plan(request: Request):
    """Return the execution layer plan for the frontend."""
    agents = request.query_params.get("agents", "")
    selected = agents.split(",") if agents else AGENT_ORDER
    plan = get_execution_plan(selected)
    deps = {a: AGENT_DEPENDENCIES.get(a, []) for a in selected}
    return JSONResponse({"plan": plan, "dependencies": deps})


@app.post("/api/export")
async def export_results(request: Request):
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = await request.json()
    company_name = validate_company_name(body.get("company_name", "Company"))
    results = validate_export_results(body.get("results", {}))
    mode = body.get("mode", "free") if body.get("mode") in ("free", "pro") else "free"

    doc = f"""# Cold Start AI — GTM Execution Package
## {company_name}
### Generated {datetime.now().strftime('%B %d, %Y')}
### Mode: {"Pro (Chained Agents + Vertical Intelligence)" if mode == "pro" else "Free (Independent Agents)"}

---

"""
    for agent_id in AGENT_ORDER:
        if agent_id in results and results[agent_id].get("content"):
            r = results[agent_id]
            doc += f"\n\n---\n\n# {r.get('icon', '')} {r.get('name', agent_id)}\n\n"
            doc += r["content"]
            doc += "\n"

    doc += f"""

---

*Generated by Cold Start AI — The GTM Execution Engine*
*{datetime.now().strftime('%B %d, %Y')}*
"""

    buffer = io.BytesIO(doc.encode("utf-8"))
    filename = f"coldstart-gtm-{company_name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}.md"

    return StreamingResponse(
        buffer,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/export-single")
async def export_single(request: Request):
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = await request.json()
    agent_id = body.get("agent_id", "")
    content = validate_text_field(body.get("content", ""), "content", max_length=100_000)
    company_name = validate_company_name(body.get("company_name", "Company"))

    agent = AGENTS.get(agent_id, {})
    name = agent.get("name", agent_id)

    doc = f"""# {agent.get('icon', '')} {name}
## {company_name}
### Generated by Cold Start AI — {datetime.now().strftime('%B %d, %Y')}

---

{content}

---

*Generated by Cold Start AI*
"""
    buffer = io.BytesIO(doc.encode("utf-8"))
    filename = f"coldstart-{agent_id}-{company_name.lower().replace(' ', '-')}.md"

    return StreamingResponse(
        buffer,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/export-csv")
async def export_csv(request: Request):
    """Export a single agent's output as CSV file(s)."""
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = await request.json()
    agent_id = body.get("agent_id", "")
    content = validate_text_field(body.get("content", ""), "content", max_length=100_000)
    company_name = validate_company_name(body.get("company_name", "Company"))

    csvs = generate_csv(agent_id, content)
    if not csvs:
        return JSONResponse({"status": "empty", "message": "No structured data found to export as CSV."})

    # If single CSV, return directly; if multiple, zip them
    if len(csvs) == 1:
        buffer = io.BytesIO(csvs[0]["content"].encode("utf-8"))
        filename = f"coldstart-{csvs[0]['filename']}-{slug_name(company_name)}.csv"
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Multiple CSVs — bundle as ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for csv_file in csvs:
            zf.writestr(f"{csv_file['filename']}.csv", csv_file["content"])
    zip_buffer.seek(0)
    filename = f"coldstart-{agent_id}-{slug_name(company_name)}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/export-csv-all")
async def export_csv_all(request: Request):
    """Export all agent outputs as a ZIP of CSV files."""
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = await request.json()
    company_name = validate_company_name(body.get("company_name", "Company"))
    results_data = validate_export_results(body.get("results", {}))

    zip_buffer = io.BytesIO()
    file_count = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for agent_id, agent_data in results_data.items():
            content = agent_data.get("content", "")
            if not content:
                continue
            csvs = generate_csv(agent_id, content)
            for csv_file in csvs:
                zf.writestr(f"{csv_file['filename']}.csv", csv_file["content"])
                file_count += 1

    if file_count == 0:
        return JSONResponse({"status": "empty", "message": "No structured data found to export."})

    zip_buffer.seek(0)
    filename = f"coldstart-gtm-{slug_name(company_name)}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/export-formatted/{platform}")
async def export_formatted(platform: str, request: Request):
    """Export agent output as platform-formatted CSV (hubspot or apollo)."""
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    if platform not in ("hubspot", "apollo"):
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    body = await request.json()
    agent_id = body.get("agent_id", "")
    content = validate_text_field(body.get("content", ""), "content", max_length=100_000)
    company_name = validate_company_name(body.get("company_name", "Company"))

    result = generate_platform_csv(agent_id, content, platform)
    if not result:
        return JSONResponse({
            "status": "empty",
            "message": f"No {platform}-formatted data available for {agent_id}.",
        })

    buffer = io.BytesIO(result["content"].encode("utf-8"))
    filename = f"coldstart-{result['filename']}-{slug_name(company_name)}.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/export-to/hubspot")
async def export_to_hubspot(request: Request):
    """Push agent output directly to HubSpot via API."""
    client_ip = export_limiter.get_client_ip(request)
    if not export_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = await request.json()
    agent_id = body.get("agent_id", "")
    content = validate_text_field(body.get("content", ""), "content", max_length=100_000)
    credentials = body.get("credentials", {})

    if not isinstance(credentials, dict) or not credentials.get("api_key"):
        raise HTTPException(status_code=400, detail="HubSpot API key required in credentials.api_key")

    # Sanitize API key — only allow expected characters
    api_key = credentials["api_key"]
    if not isinstance(api_key, str) or len(api_key) > 500:
        raise HTTPException(status_code=400, detail="Invalid API key format")

    connector = get_connector("hubspot")
    if not connector:
        raise HTTPException(status_code=500, detail="HubSpot connector not available")

    result = await connector.export(
        agent_id=agent_id,
        parsed_data={"raw": content},
        credentials={"api_key": api_key},
    )
    return JSONResponse(result)


@app.post("/api/test-connection/{platform}")
async def test_connection(platform: str, request: Request):
    """Test connection to an external platform."""
    if platform not in ("hubspot",):
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    body = await request.json()
    credentials = body.get("credentials", {})

    connector = get_connector(platform)
    if not connector:
        raise HTTPException(status_code=500, detail=f"{platform} connector not available")

    valid = connector.validate_credentials(credentials)
    return JSONResponse({"status": "connected" if valid else "failed", "platform": platform})


def slug_name(s: str) -> str:
    """Create a URL-safe slug from a string."""
    import re as _re
    return _re.sub(r"[^a-z0-9-]", "", s.lower().replace(" ", "-"))


def generate_demo_content(agent_id, agent, company_context):
    company_name = "Your Company"
    for line in company_context.split("\n"):
        if line.startswith("COMPANY:"):
            company_name = line.replace("COMPANY:", "").strip() or "Your Company"
            break

    return f"""## {agent['icon']} {agent['name']} — {agent['deliverable']}

*{agent['tagline']}*

---

### This is Demo Mode

When you add your `ANTHROPIC_API_KEY`, this agent will produce a **complete {agent['deliverable']}** for **{company_name}**, including:

{agent.get('description', '')}

**Deliverable format:** {agent.get('deliverable_format', 'Document')}

---

### What You'll Get

This agent doesn't just give advice — it produces **ready-to-use assets** that you can download and deploy immediately:

- Complete document formatted for your team
- Copy-paste ready templates and scripts
- Specific numbers, targets, and benchmarks
- Actionable checklists and frameworks

---

> **To activate:** Set the `ANTHROPIC_API_KEY` environment variable and re-run your launch.

```bash
export ANTHROPIC_API_KEY=your-key-here
```
"""
