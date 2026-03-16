/**
 * Cold Start AI — Intake Form Logic v3
 * Now with clarifying questions before dashboard redirect.
 */

function toggleAllAgents() {
    const checkboxes = document.querySelectorAll('.agent-card input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => { cb.checked = !allChecked; });
    document.querySelector('.select-all-btn').textContent = allChecked ? 'Select All' : 'Deselect All';
}

function getFormData() {
    const modeRadio = document.querySelector('input[name="mode"]:checked');
    const enrichment = (typeof scrapeEnrichment !== 'undefined') ? scrapeEnrichment : {};
    return {
        company_name: document.getElementById('company_name').value,
        company_url: document.getElementById('company_url')?.value || '',
        product_description: document.getElementById('product_description').value,
        target_market: document.getElementById('target_market').value,
        stage: document.getElementById('stage').value,
        business_model: document.getElementById('business_model').value,
        budget: document.getElementById('budget')?.value || '',
        gtm_motion: document.getElementById('gtm_motion')?.value || '',
        current_challenges: document.getElementById('current_challenges').value,
        agents: Array.from(document.querySelectorAll('.agent-card input:checked')).map(cb => cb.value),
        mode: modeRadio ? modeRadio.value : 'free',
        // Enrichment from scrape
        competitive_positioning: enrichment.competitive_positioning || '',
        pricing_signals: enrichment.pricing_signals || '',
        company_stage_signals: enrichment.company_stage_signals || '',
        tech_stack_signals: enrichment.tech_stack_signals || '',
        team_size_signals: enrichment.team_size_signals || '',
        key_integrations: enrichment.key_integrations || '',
        funding_signals: enrichment.funding_signals || '',
        hiring_signals: enrichment.hiring_signals || '',
        inferred_vertical: enrichment.inferred_vertical || '',
    };
}

function proceedToDashboard(formData) {
    sessionStorage.setItem('coldstart_input', JSON.stringify(formData));
    window.location.href = '/dashboard';
}

function showClarifySection(questions, variants, formData) {
    // Remove existing clarify section if any
    const existing = document.getElementById('clarify-section');
    if (existing) existing.remove();

    const section = document.createElement('div');
    section.id = 'clarify-section';
    section.className = 'clarify-section';

    let html = '<div class="clarify-header"><h3>Before we run your agents...</h3>';
    html += '<p>Stronger inputs = sharper outputs. Answer what you can.</p></div>';

    // Questions
    if (questions.length > 0) {
        html += '<div class="clarify-questions">';
        for (const q of questions) {
            const requiredTag = q.required ? ' <span class="required-tag">Required</span>' : '';
            html += `<div class="clarify-question">
                <label for="clarify-${q.id}">${q.question}${requiredTag}</label>
                <textarea id="clarify-${q.id}" data-field="${q.field}" rows="2" placeholder="Your answer..."></textarea>
            </div>`;
        }
        html += '</div>';
    }

    // Variants
    if (variants.length > 1) {
        html += '<div class="clarify-variants"><h4>Choose your plan focus:</h4>';
        for (const v of variants) {
            const checked = v.default ? 'checked' : '';
            html += `<label class="variant-option">
                <input type="radio" name="plan_variant" value="${v.id}" ${checked}>
                <span class="variant-name">${v.name}</span>
                <span class="variant-desc">${v.description}</span>
            </label>`;
        }
        html += '</div>';
    }

    html += '<div class="clarify-actions">';
    html += '<button class="btn-proceed" onclick="handleClarifySubmit()">Launch Agents</button>';
    html += '<button class="btn-skip" onclick="handleClarifySkip()">Skip — use my original input</button>';
    html += '</div>';

    section.innerHTML = html;

    // Insert after the form
    const form = document.getElementById('intake-form');
    form.parentNode.insertBefore(section, form.nextSibling);
    section.scrollIntoView({ behavior: 'smooth' });

    // Store formData for later
    window._pendingFormData = formData;
}

function handleClarifySubmit() {
    const formData = window._pendingFormData;
    if (!formData) return;

    // Merge clarified answers back into form data
    const textareas = document.querySelectorAll('#clarify-section textarea');
    for (const ta of textareas) {
        const field = ta.dataset.field;
        const value = ta.value.trim();
        if (value && field) {
            formData[field] = value;
        }
    }

    // Get selected variant
    const variantRadio = document.querySelector('input[name="plan_variant"]:checked');
    if (variantRadio) {
        formData.plan_variant = variantRadio.value;
    }

    proceedToDashboard(formData);
}

function handleClarifySkip() {
    const formData = window._pendingFormData;
    if (formData) {
        proceedToDashboard(formData);
    }
}

document.getElementById('intake-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.querySelector('.submit-btn');
    btn.classList.add('loading');
    btn.disabled = true;

    const formData = getFormData();

    try {
        // Check input quality and get clarifying questions
        const response = await fetch('/api/clarify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        const data = await response.json();

        // If there are required questions or score is low, show clarification
        const hasRequiredQuestions = data.questions.some(q => q.required);
        const scoreLow = data.score && data.score.score < 60;

        if (hasRequiredQuestions || scoreLow) {
            btn.classList.remove('loading');
            btn.disabled = false;
            showClarifySection(data.questions, data.variants, formData);
        } else {
            // Input is good enough — proceed directly
            proceedToDashboard(formData);
        }
    } catch {
        // If clarify endpoint fails, proceed anyway
        proceedToDashboard(formData);
    }
});
