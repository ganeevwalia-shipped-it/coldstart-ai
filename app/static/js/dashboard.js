/**
 * Cold Start AI — Dashboard Logic
 * Runs agents one by one, updates UI in real-time.
 */

const input = JSON.parse(sessionStorage.getItem('coldstart_input') || '{}');
const results = {};
let activeAgent = null;
let completedCount = 0;

// Redirect if no input
if (!input.company_name) {
    window.location.href = '/';
}

// Set company badge
document.getElementById('company-badge').textContent = `STRATEGY FOR: ${input.company_name.toUpperCase()}`;
document.getElementById('progress-total').textContent = input.agents ? input.agents.length : 0;

// Build company context string
const companyContext = `
COMPANY: ${input.company_name}
PRODUCT: ${input.product_description}
TARGET MARKET: ${input.target_market}
STAGE: ${input.stage}
BUSINESS MODEL: ${input.business_model}
CURRENT CHALLENGES: ${input.current_challenges || 'Not specified'}
`;

// Show a specific agent's output
function showAgent(agentId) {
    // Update active states
    document.querySelectorAll('.agent-list-item').forEach(el => el.classList.remove('active'));
    const item = document.querySelector(`[data-agent="${agentId}"]`);
    if (item) item.classList.add('active');

    activeAgent = agentId;

    const output = document.getElementById('agent-output');
    const header = document.getElementById('dashboard-header');

    if (results[agentId]) {
        const r = results[agentId];
        document.getElementById('active-agent-name').textContent = `${r.icon} ${r.name}`;
        document.getElementById('active-agent-tagline').textContent = '';

        if (r.status === 'complete' || r.status === 'demo') {
            output.innerHTML = `<div class="agent-content">${marked.parse(r.content)}</div>`;
        } else if (r.status === 'error') {
            output.innerHTML = `<div class="agent-content" style="color: var(--error);">${r.content}</div>`;
        }
    } else {
        // Still loading
        const item = document.querySelector(`[data-agent="${agentId}"]`);
        const name = item ? item.querySelector('.agent-list-name').textContent : agentId;
        const icon = item ? item.querySelector('.agent-list-icon').textContent : '';
        document.getElementById('active-agent-name').textContent = `${icon} ${name}`;
        document.getElementById('active-agent-tagline').textContent = 'Agent is analyzing...';
        output.innerHTML = `
            <div class="loading-state">
                <div class="loader"><div class="loader-bar"></div></div>
                <p>Running analysis...</p>
            </div>`;
    }
}

// Update agent status in sidebar
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

// Run all agents sequentially (so user can watch progress)
async function runAgents() {
    const agents = input.agents || [];

    for (let i = 0; i < agents.length; i++) {
        const agentId = agents[i];

        // Mark as running
        setAgentStatus(agentId, 'running');

        // Auto-show first agent or currently running one
        if (i === 0 || activeAgent === null) {
            showAgent(agentId);
        }

        try {
            const response = await fetch('/api/generate-single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    company_context: companyContext,
                }),
            });

            const data = await response.json();
            results[agentId] = data;
            setAgentStatus(agentId, data.status);

            // If this is the active agent, update the display
            if (activeAgent === agentId) {
                showAgent(agentId);
            }

        } catch (err) {
            results[agentId] = {
                name: agentId,
                icon: '⚠️',
                status: 'error',
                content: `Network error: ${err.message}`,
            };
            setAgentStatus(agentId, 'error');
        }
    }

    // All done
    document.getElementById('status-text').textContent = `All ${completedCount} agents complete`;
    document.querySelector('#global-status .status-dot').classList.remove('running');
}

// Start
runAgents();
