"""
Cold Start AI — GTM Execution Engine
Not a strategy generator. An operating system for launching products.

Two modes:
  FREE: All agents run independently (same base context)
  PRO:  Agents chain — each builds on the outputs before it + vertical intelligence
"""
import os
import json
import asyncio
import io
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from anthropic import AsyncAnthropic

from app.agents.registry import AGENTS, AGENT_ORDER, CATEGORIES
from app.agents.orchestrator import build_chained_prompt, get_execution_plan, AGENT_DEPENDENCIES
from app.agents.verticals import get_vertical_context

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


@app.post("/api/generate-single")
async def generate_single(request: Request):
    """
    FREE mode: Run a single agent with base context only.
    """
    body = await request.json()
    agent_id = body.get("agent_id", "")
    company_context = body.get("company_context", "")

    if agent_id not in AGENTS:
        return JSONResponse({"status": "error", "message": "Unknown agent"}, status_code=400)

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
        prompt = f"{agent['prompt']}\n\n---\n\nHere is the company information:\n{company_context}"

        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": message.content[0].text,
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
    body = await request.json()
    agent_id = body.get("agent_id", "")
    company_context = body.get("company_context", "")
    previous_outputs = body.get("previous_outputs", {})
    product_description = body.get("product_description", "")
    business_model = body.get("business_model", "")
    target_market = body.get("target_market", "")

    if agent_id not in AGENTS:
        return JSONResponse({"status": "error", "message": "Unknown agent"}, status_code=400)

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

    prompt = build_chained_prompt(agent_id, agent["prompt"], enriched_company_context, previous_outputs)

    try:
        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
            "deliverable": agent["deliverable"],
            "content": message.content[0].text,
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
    body = await request.json()
    company_name = body.get("company_name", "Company")
    results = body.get("results", {})
    mode = body.get("mode", "free")

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
    body = await request.json()
    agent_id = body.get("agent_id", "")
    content = body.get("content", "")
    company_name = body.get("company_name", "Company")

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
