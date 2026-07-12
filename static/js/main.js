// ── NepCompare General Javascript ──

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initAutocomplete('nav-search-input', 'nav-suggestions');
    initAutocomplete('hero-search-input', 'hero-suggestions');
});

// ── Theme Toggle (Dark/Light Mode) ──
function initTheme() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (!toggleBtn) return;

    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    if (theme === 'light') {
        btn.innerHTML = '<i class="bi bi-sun-fill text-warning"></i>';
    } else {
        btn.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
    }
}

// ── Search Suggestions (Autocomplete) ──
function initAutocomplete(inputId, dropdownId) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;

    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();

        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/suggestions?q=${encodeURIComponent(query)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.length === 0) {
                        dropdown.style.display = 'none';
                        return;
                    }
                    dropdown.innerHTML = data.map(item => `
                        <div class="suggestion-item" onclick="selectSuggestion('${inputId}', '${dropdownId}', \`${item.replace(/'/g, "\\'")}\`)">
                            <i class="bi bi-search me-2 text-muted"></i> ${item}
                        </div>
                    `).join('');
                    dropdown.style.display = 'block';
                })
                .catch(() => {});
        }, 300);
    });

    // Close dropdown on clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
}

function selectSuggestion(inputId, dropdownId, val) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (input) {
        input.value = val;
        // Submit nearest form
        input.closest('form').submit();
    }
    if (dropdown) dropdown.style.display = 'none';
}

// ── Product Card HTML Helper ──
function productCard(p) {
    const discountBadge = p.discount > 0 ? `<div class="discount-tag">-${p.discount}%</div>` : '';
    const origPrice = p.original_price ? `<div class="orig-price">Rs. ${p.original_price.toLocaleString()}</div>` : '';
    const ratingStars = p.rating ? `<div class="text-warning small mb-2">${'★'.repeat(Math.round(p.rating))} <span class="text-muted">(${p.reviews || 0})</span></div>` : '';

    return `
        <div class="col-6 col-md-4 col-lg-3">
            <div class="glass-card product-card">
                <div class="product-img-wrapper">
                    ${discountBadge}
                    <div class="store-badge-card">${p.store}</div>
                    <img src="${p.image_url || '/static/images/placeholder.svg'}" class="product-img" alt="${p.name}"
                         onerror="this.src='/static/images/placeholder.svg'">
                </div>
                <div class="product-card-body">
                    <a href="/product/${p.id}" class="product-title-link" title="${p.name}">${p.name}</a>
                    ${ratingStars}
                    <div class="product-price-row mt-auto">
                        ${origPrice}
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="fw-800 text-accent fs-5">Rs. ${p.price?.toLocaleString()}</span>
                            <a href="/product/${p.id}" class="btn btn-sm btn-outline-accent px-2 py-1"><i class="bi bi-eye"></i></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ── Toast Notifications ──
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const id = 'toast-' + Date.now();
    const iconClass = type === 'success' ? 'bi-check-circle-fill text-success' :
                      type === 'error' ? 'bi-exclamation-triangle-fill text-danger' :
                      'bi-info-circle-fill text-info';

    const toastHtml = `
        <div id="${id}" class="toast align-items-center bg-dark text-white border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${iconClass} me-2"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white m-auto me-2" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(id);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
