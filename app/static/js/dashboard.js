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

        // Show/hide refine button
        const refineBtn = document.getElementById('refine-btn');
        if (refineBtn) {
            refineBtn.style.display = (r.status === 'complete' || r.status === 'demo') ? 'inline-block' : 'none';
        }
        // Hide refine panel when switching agents
        toggleRefinePanel(false);

        if (r.status === 'complete' || r.status === 'demo') {
            let validationBadge = '';
            if (r.schema_validation && !r.schema_validation.valid) {
                const pct = Math.round((r.schema_validation.completeness || 0) * 100);
                validationBadge = `<div class="validation-badge" title="Missing: ${(r.schema_validation.missing || []).join(', ')}">Schema: ${pct}% complete</div>`;
            }
            output.innerHTML = `${validationBadge}<div class="agent-content">${marked.parse(r.content)}</div>`;
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
    document.getElementById('export-all-dropdown').style.display = 'inline-block';
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

// ============ REFINEMENT ============
function toggleRefinePanel(show) {
    const panel = document.getElementById('refine-panel');
    if (panel) {
        panel.style.display = show ? 'block' : 'none';
        if (show) {
            document.getElementById('refine-input').value = '';
            document.getElementById('refine-input').focus();
        }
    }
}

async function refineAgent() {
    if (!activeAgent || !results[activeAgent]) return;
    const feedback = document.getElementById('refine-input').value.trim();
    if (!feedback) return;

    const btn = document.getElementById('refine-btn-submit');
    btn.disabled = true;
    btn.textContent = 'Refining...';

    try {
        const response = await fetch('/api/refine-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: activeAgent,
                company_context: companyContext,
                previous_output: results[activeAgent].content,
                user_feedback: feedback,
            }),
        });

        const data = await response.json();
        results[activeAgent] = data;
        showAgent(activeAgent);
        toggleRefinePanel(false);
    } catch (err) {
        alert('Refinement failed: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Re-run with Feedback';
    }
}

// ============ EXPORT MENUS ============
function toggleExportMenu(type) {
    const menuId = `export-menu-${type}`;
    const menu = document.getElementById(menuId);
    if (!menu) return;
    const isVisible = menu.style.display !== 'none';
    // Close all menus first
    document.querySelectorAll('.export-menu').forEach(m => m.style.display = 'none');
    if (!isVisible) menu.style.display = 'block';
}

// Close menus on outside click
document.addEventListener('click', (e) => {
    if (!e.target.closest('.export-dropdown')) {
        document.querySelectorAll('.export-menu').forEach(m => m.style.display = 'none');
    }
});

// ============ CSV EXPORTS ============
async function exportCSVSingle() {
    if (!activeAgent || !results[activeAgent]) return;
    try {
        const response = await fetch('/api/export-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: activeAgent,
                content: results[activeAgent].content,
                company_name: input.company_name,
            }),
        });
        if (!response.ok) {
            const data = await response.json();
            showToast(data.message || 'No CSV data available', 'info');
            return;
        }
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('json')) {
            const data = await response.json();
            showToast(data.message || 'No CSV data available', 'info');
            return;
        }
        const blob = await response.blob();
        const disposition = response.headers.get('content-disposition') || '';
        const filenameMatch = disposition.match(/filename=(.+)/);
        const filename = filenameMatch ? filenameMatch[1] : `coldstart-${activeAgent}.csv`;
        downloadBlob(blob, filename);
        showToast('CSV exported!', 'success');
    } catch (err) {
        showToast('Export failed: ' + err.message, 'error');
    }
}

async function exportCSVAll() {
    try {
        const response = await fetch('/api/export-csv-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: input.company_name,
                results: results,
            }),
        });
        if (!response.ok) {
            const data = await response.json();
            showToast(data.message || 'No CSV data available', 'info');
            return;
        }
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('json')) {
            const data = await response.json();
            showToast(data.message || 'No CSV data available', 'info');
            return;
        }
        const blob = await response.blob();
        downloadBlob(blob, `coldstart-gtm-${slug(input.company_name)}.zip`);
        showToast('All CSVs exported!', 'success');
    } catch (err) {
        showToast('Export failed: ' + err.message, 'error');
    }
}

// ============ PLATFORM-FORMATTED EXPORTS ============
async function exportPlatformSingle(platform) {
    if (!activeAgent || !results[activeAgent]) return;
    try {
        const response = await fetch(`/api/export-formatted/${platform}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: activeAgent,
                content: results[activeAgent].content,
                company_name: input.company_name,
            }),
        });
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('json')) {
            const data = await response.json();
            showToast(data.message || `No ${platform} data available for this agent`, 'info');
            return;
        }
        const blob = await response.blob();
        const disposition = response.headers.get('content-disposition') || '';
        const filenameMatch = disposition.match(/filename=(.+)/);
        const filename = filenameMatch ? filenameMatch[1] : `coldstart-${platform}-${activeAgent}.csv`;
        downloadBlob(blob, filename);
        showToast(`${platform} CSV exported!`, 'success');
    } catch (err) {
        showToast('Export failed: ' + err.message, 'error');
    }
}

async function exportPlatformAll(platform) {
    // Export each agent that has platform support
    let exported = 0;
    for (const [agentId, agentData] of Object.entries(results)) {
        if (!agentData.content) continue;
        try {
            const response = await fetch(`/api/export-formatted/${platform}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    content: agentData.content,
                    company_name: input.company_name,
                }),
            });
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('json')) {
                const blob = await response.blob();
                const disposition = response.headers.get('content-disposition') || '';
                const filenameMatch = disposition.match(/filename=(.+)/);
                const filename = filenameMatch ? filenameMatch[1] : `coldstart-${platform}-${agentId}.csv`;
                downloadBlob(blob, filename);
                exported++;
            }
        } catch { /* skip agents with no platform data */ }
    }
    if (exported > 0) {
        showToast(`Exported ${exported} ${platform} CSV file(s)`, 'success');
    } else {
        showToast(`No ${platform}-formatted data available`, 'info');
    }
}

// ============ HUBSPOT LIVE PUSH ============
function showHubSpotModal() {
    document.getElementById('hubspot-modal').style.display = 'flex';
    const savedKey = sessionStorage.getItem('hubspot_api_key');
    if (savedKey) {
        document.getElementById('hubspot-api-key').value = savedKey;
        document.getElementById('hubspot-push-btn').disabled = false;
    }
}

function closeHubSpotModal() {
    document.getElementById('hubspot-modal').style.display = 'none';
    document.getElementById('hubspot-status').textContent = '';
}

async function testHubSpotConnection() {
    const apiKey = document.getElementById('hubspot-api-key').value.trim();
    if (!apiKey) return;

    const btn = document.getElementById('hubspot-test-btn');
    const status = document.getElementById('hubspot-status');
    btn.disabled = true;
    btn.textContent = 'Testing...';
    status.textContent = '';

    try {
        const response = await fetch('/api/test-connection/hubspot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credentials: { api_key: apiKey } }),
        });
        const data = await response.json();
        if (data.status === 'connected') {
            status.innerHTML = '<span style="color:#059669;">Connected successfully!</span>';
            sessionStorage.setItem('hubspot_api_key', apiKey);
            document.getElementById('hubspot-push-btn').disabled = false;
        } else {
            status.innerHTML = '<span style="color:#dc2626;">Connection failed. Check your API key.</span>';
        }
    } catch (err) {
        status.innerHTML = `<span style="color:#dc2626;">Error: ${err.message}</span>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Test Connection';
    }
}

async function pushToHubSpot() {
    if (!activeAgent || !results[activeAgent]) return;
    const apiKey = sessionStorage.getItem('hubspot_api_key') || document.getElementById('hubspot-api-key').value.trim();
    if (!apiKey) return;

    const btn = document.getElementById('hubspot-push-btn');
    btn.disabled = true;
    btn.textContent = 'Pushing...';

    try {
        const response = await fetch('/api/export-to/hubspot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: activeAgent,
                content: results[activeAgent].content,
                credentials: { api_key: apiKey },
            }),
        });
        const data = await response.json();
        closeHubSpotModal();

        if (data.status === 'success' || data.status === 'partial') {
            const created = (data.created || []).length;
            const errors = (data.errors || []).length;
            showToast(`HubSpot: ${created} items created${errors ? `, ${errors} errors` : ''}`, errors ? 'info' : 'success');
        } else {
            showToast(data.message || 'HubSpot export completed', 'info');
        }
    } catch (err) {
        showToast('HubSpot push failed: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Push Data';
    }
}

// ============ TOAST NOTIFICATIONS ============
function showToast(message, type = 'info') {
    const toast = document.getElementById('export-toast');
    toast.textContent = message;
    toast.className = `export-toast ${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 4000);
}

// Start based on mode
if (mode === 'pro') {
    runAgentsPro();
} else {
    runAgentsFree();
}
