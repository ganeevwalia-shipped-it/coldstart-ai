/**
 * Cold Start AI — Intake Form Logic v2
 */

function toggleAllAgents() {
    const checkboxes = document.querySelectorAll('.agent-card input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => { cb.checked = !allChecked; });
    document.querySelector('.select-all-btn').textContent = allChecked ? 'Select All' : 'Deselect All';
}

document.getElementById('intake-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.querySelector('.submit-btn');
    btn.classList.add('loading');
    btn.disabled = true;

    const formData = {
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
    };

    sessionStorage.setItem('coldstart_input', JSON.stringify(formData));
    window.location.href = '/dashboard';
});
