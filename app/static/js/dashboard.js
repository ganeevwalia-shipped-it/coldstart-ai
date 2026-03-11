/**
 * Cold Start AI — Dashboard v3
 * Two modes:
 *   FREE: Agents run independently (same context)
 *   PRO:  Agents chain — each builds on the last + vertical intelligence
 */

const input = JSON.parse(sessionStorage.getItem('coldstart_input') || '{}');
const results = {};
let activeAgent = null;
let completedCount = 0;
const mode = input.mode || 'free'; // 'free' or 'pro'

if (!input.company_name) {
    window.location.href = '/launch';
}

document.getElementById('company-badge').textContent = `GTM SYSTEM FOR: ${input.company_name.toUpperCase()}`;
document.getElementById('progress-total').textContent = input.agents ? input.agents.length : 0;

// Show mode indicator
const modeLabel = mode === 'pro' ? 'PRO — Chained Agents + Vertical Intelligence' : 'FREE — Independent Agents';
document.getElementById('active-agent-tagline').textContent = modeLabel;

const companyContext = `
COMPANY: ${input.company_name}
WEBSITE: ${input.company_url || 'Not provided'}
PRODUCT: ${input.product_description}
TARGET MARKET: ${input.target_market}
STAGE: ${input.stage}
BUSINESS MODEL: ${input.business_model}
MONTHLY GTM BUDGET: ${input.budget || 'Not specified'}
PRIMARY GTM MOTION: ${input.gtm_motion || 'Not specified'}
CURRENT CHALLENGES: ${input.current_challenges || 'Not specified'}
`;

function showAgent(agentId) {
    document.querySelectorAll('.agent-list-item').forEach(el => el.classList.remove('active'));
    const item = document.querySelector(`[data-agent="${agentId}"]`);
    if (item) item.classList.add('active');

    activeAgent = agentId;
    const output = document.getElementById('agent-output');

    if (results[agentId]) {
        const r = results[agentId];
        document.getElementById('active-agent-name').textContent = `${r.icon} ${r.name}`;
        document.getElementById('active-agent-tagline').textContent = r.deliverable || '';
        document.getElementById('header-actions').style.display = 'block';

        if (r.status === 'complete' || r.status === 'demo') {
            output.innerHTML = `<div class="agent-content">${marked.parse(r.content)}</div>`;
        } else if (r.status === 'error') {
            output.innerHTML = `<div class="agent-content" style="color: var(--error);">${r.content}</div>`;
        }
    } else {
        const name = item ? item.querySelector('.agent-list-name').textContent : agentId;
        const icon = item ? item.querySelector('.agent-list-icon').textContent : '';
        document.getElementById('active-agent-name').textContent = `${icon} ${name}`;
        document.getElementById('active-agent-tagline').textContent = 'Agent is building deliverables...';
        document.getElementById('header-actions').style.display = 'none';
        output.innerHTML = `
            <div class="loading-state">
                <div class="loader"><div class="loader-bar"></div></div>
                <p>Building deliverables...</p>
            </div>`;
    }
}

function setAgentStatus(agentId, status) {
    const el = document.getElementById(`status-${agentId}`);
    if (!el) return;
    const item = el.closest('.agent-list-item');

    if (status === 'running') {
        el.innerHTML = '<span class="status-running">◉</span>';
    } else if (status === 'complete' || status === 'demo') {
        el.innerHTML = '<span class="status-complete">✓</span>';
        if (item) item.classList.add('complete');
        completedCount++;
        document.getElementById('progress-count').textContent = completedCount;
    } else if (status === 'error') {
        el.innerHTML = '<span class="status-error">✗</span>';
        completedCount++;
        document.getElementById('progress-count').textContent = completedCount;
    }
}

// ============ FREE MODE: Sequential, no chaining ============
async function runAgentsFree() {
    const agents = input.agents || [];

    for (let i = 0; i < agents.length; i++) {
        const agentId = agents[i];
        setAgentStatus(agentId, 'running');

        if (i === 0 || activeAgent === null) {
            showAgent(agentId);
        }

        try {
            const response = await fetch('/api/generate-single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId, company_context: companyContext }),
            });

            const data = await response.json();
            results[agentId] = data;
            setAgentStatus(agentId, data.status);

            if (activeAgent === agentId) showAgent(agentId);
        } catch (err) {
            results[agentId] = {
                name: agentId, icon: '⚠️', status: 'error',
                content: `Network error: ${err.message}`,
            };
            setAgentStatus(agentId, 'error');
        }
    }

    onAllComplete();
}

// ============ PRO MODE: Chained, layered execution ============
async function runAgentsPro() {
    const agents = input.agents || [];

    // Get execution plan from server
    let plan;
    try {
        const planRes = await fetch(`/api/execution-plan?agents=${agents.join(',')}`);
        const planData = await planRes.json();
        plan = planData.plan;
    } catch {
        // Fallback to sequential
        plan = agents.map(a => [a]);
    }

    // Collect outputs for chaining
    const chainedOutputs = {};

    for (const layer of plan) {
        // Mark all agents in this layer as running
        layer.forEach(agentId => setAgentStatus(agentId, 'running'));

        if (!activeAgent || !results[activeAgent]) {
            showAgent(layer[0]);
        }

        // Run all agents in this layer in parallel
        const layerPromises = layer.map(async (agentId) => {
            try {
                const response = await fetch('/api/generate-chained', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_id: agentId,
                        company_context: companyContext,
                        previous_outputs: chainedOutputs,
                        product_description: input.product_description,
                        business_model: input.business_model,
                        target_market: input.target_market,
                    }),
                });

                const data = await response.json();
                results[agentId] = data;
                chainedOutputs[agentId] = data.content;
                setAgentStatus(agentId, data.status);

                if (activeAgent === agentId) showAgent(agentId);
            } catch (err) {
                results[agentId] = {
                    name: agentId, icon: '⚠️', status: 'error',
                    content: `Network error: ${err.message}`,
                };
                setAgentStatus(agentId, 'error');
            }
        });

        // Wait for entire layer to complete before moving to next
        await Promise.all(layerPromises);
    }

    onAllComplete();
}

function onAllComplete() {
    document.getElementById('status-text').textContent = `All ${completedCount} agents complete`;
    document.querySelector('#global-status .status-dot').classList.remove('running');
    document.getElementById('export-all-btn').style.display = 'block';
}

// Export functions
async function exportSingle() {
    if (!activeAgent || !results[activeAgent]) return;
    const response = await fetch('/api/export-single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            agent_id: activeAgent,
            content: results[activeAgent].content,
            company_name: input.company_name,
        }),
    });
    const blob = await response.blob();
    downloadBlob(blob, `coldstart-${activeAgent}-${slug(input.company_name)}.md`);
}

async function exportAll() {
    const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            company_name: input.company_name,
            results: results,
            mode: mode,
        }),
    });
    const blob = await response.blob();
    downloadBlob(blob, `coldstart-gtm-${slug(input.company_name)}.md`);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function slug(s) {
    return s.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}

// Start based on mode
if (mode === 'pro') {
    runAgentsPro();
} else {
    runAgentsFree();
}
