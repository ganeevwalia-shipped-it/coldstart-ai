"""
Cold Start AI — Main Application
The GTM war room. 12 specialist agents. Zero fluff.
"""
import os
import json
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from anthropic import AsyncAnthropic

from app.agents.registry import AGENTS, AGENT_ORDER

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
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "agents": AGENTS,
        "agent_order": AGENT_ORDER,
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agents": AGENTS,
        "agent_order": AGENT_ORDER,
    })


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    company_name = body.get("company_name", "")
    product_description = body.get("product_description", "")
    target_market = body.get("target_market", "")
    stage = body.get("stage", "")
    business_model = body.get("business_model", "")
    current_challenges = body.get("current_challenges", "")
    selected_agents = body.get("agents", AGENT_ORDER)

    company_context = f"""
COMPANY: {company_name}
PRODUCT: {product_description}
TARGET MARKET: {target_market}
STAGE: {stage}
BUSINESS MODEL: {business_model}
CURRENT CHALLENGES: {current_challenges}
"""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Demo mode — return structured placeholder results
        results = {}
        for agent_id in selected_agents:
            if agent_id in AGENTS:
                agent = AGENTS[agent_id]
                results[agent_id] = {
                    "name": agent["name"],
                    "icon": agent["icon"],
                    "status": "demo",
                    "content": f"## {agent['icon']} {agent['name']}\n\n"
                               f"*{agent['tagline']}*\n\n"
                               f"**Demo Mode** — Add your `ANTHROPIC_API_KEY` environment variable to get real AI-generated GTM strategy.\n\n"
                               f"This agent would analyze your company and produce a deep, specialized {agent['name'].lower()} strategy based on:\n\n"
                               f"- Company: {company_name}\n"
                               f"- Product: {product_description}\n"
                               f"- Market: {target_market}\n"
                               f"- Stage: {stage}\n"
                }
        return JSONResponse({"status": "demo", "results": results})

    # Run all selected agents concurrently
    async def run_agent(agent_id):
        agent = AGENTS[agent_id]
        try:
            message = await get_client().messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"{agent['prompt']}\n\n---\n\nHere is the company information:\n{company_context}"
                }]
            )
            content = message.content[0].text
            return agent_id, {
                "name": agent["name"],
                "icon": agent["icon"],
                "status": "complete",
                "content": content,
            }
        except Exception as e:
            return agent_id, {
                "name": agent["name"],
                "icon": agent["icon"],
                "status": "error",
                "content": f"Error: {str(e)}",
            }

    tasks = [run_agent(aid) for aid in selected_agents if aid in AGENTS]
    completed = await asyncio.gather(*tasks)
    results = {agent_id: result for agent_id, result in completed}

    return JSONResponse({"status": "complete", "results": results})


@app.post("/api/generate-single")
async def generate_single(request: Request):
    """Run a single agent — used for streaming one at a time."""
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
            "content": f"## {agent['icon']} {agent['name']}\n\n*{agent['tagline']}*\n\n**Demo Mode** — Add your ANTHROPIC_API_KEY to unlock real results."
        })

    try:
        message = await get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"{agent['prompt']}\n\n---\n\nHere is the company information:\n{company_context}"
            }]
        )
        return JSONResponse({
            "status": "complete",
            "agent_id": agent_id,
            "name": agent["name"],
            "icon": agent["icon"],
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
