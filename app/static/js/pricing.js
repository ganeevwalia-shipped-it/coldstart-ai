/* Cold Start AI — Pricing Page Interactions */

function setBilling(period) {
    document.querySelectorAll('.toggle-option').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.period === period);
    });
    document.querySelectorAll('.price-value').forEach(el => {
        el.textContent = el.dataset[period];
    });
    document.querySelectorAll('.period-monthly').forEach(el => {
        el.style.display = period === 'monthly' ? '' : 'none';
    });
    document.querySelectorAll('.period-annual').forEach(el => {
        el.style.display = period === 'annual' ? '' : 'none';
    });
    document.querySelectorAll('.price-mo').forEach(el => {
        el.style.display = period === 'monthly' ? '' : 'none';
    });
}

function toggleFaq(btn) {
    const item = btn.closest('.faq-item');
    item.classList.toggle('open');
}

function checkout(tier) {
    alert('Checkout for ' + tier + ' coming soon!');
}
