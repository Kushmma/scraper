// ── NepCompare Admin Panel JavaScript ──

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadScrapingLogs();

    // Trigger Scraper
    const form = document.getElementById('scraper-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            triggerScrape();
        });
    }

    // Refresh logs button
    const refreshBtn = document.getElementById('btn-refresh-logs');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadScrapingLogs);
    }

    // Product search button
    const searchBtn = document.getElementById('admin-search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchAdminProducts);
    }
});

let pollInterval = null;

function loadDashboardStats(animate = false) {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            document.getElementById('admin-total-products').textContent = data.total_products || 0;
            document.getElementById('admin-total-stores').textContent = data.total_stores || 0;
            document.getElementById('admin-total-categories').textContent = data.total_categories || 0;
            document.getElementById('admin-avg-discount').textContent = (data.avg_discount || 0) + '%';

            if (animate) {
                const cards = document.querySelectorAll('.glass-card.p-3');
                cards.forEach(card => {
                    card.classList.remove('stats-card-pulse');
                    void card.offsetWidth; // Trigger reflow
                    card.classList.add('stats-card-pulse');
                });
            }
        })
        .catch(() => {});
}

function loadScrapingLogs() {
    const tbody = document.getElementById('logs-tbody');
    if (!tbody) return Promise.resolve(false);

    return fetch('/api/scrape/logs')
        .then(r => r.json())
        .then(data => {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No logs recorded yet.</td></tr>';
                return false;
            }
            tbody.innerHTML = data.map(log => {
                const badge = log.status === 'success' ? 'bg-success' :
                              log.status === 'failed' ? 'bg-danger' : 'bg-warning';
                return `
                    <tr>
                        <td><strong>${log.store}</strong></td>
                        <td><code>${log.query || '-'}</code></td>
                        <td><span class="badge ${badge}">${log.status}</span></td>
                        <td>+${log.products_found || 0}</td>
                        <td>${log.duration_seconds || 0}s</td>
                        <td class="text-muted">${new Date(log.created_at).toLocaleString()}</td>
                    </tr>
                `;
            }).join('');

            // Return true if any job is currently running
            return data.some(log => log.status === 'running');
        })
        .catch(() => false);
}

function triggerScrape() {
    const store = document.getElementById('scrape-store').value;
    const query = document.getElementById('scrape-query').value.trim();
    const btn = document.getElementById('btn-trigger-scrape');

    if (!query) {
        showToast('Please enter a search term', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Scraping...';

    fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ store: store || null, query: query })
    })
    .then(r => r.json())
    .then(data => {
        showToast(data.message || 'Scraping job started in the background.', 'success');
        
        if (pollInterval) clearInterval(pollInterval);
        
        // Wait 1.5 seconds so backend has started scraping and created the log entry
        setTimeout(() => {
            loadScrapingLogs(); // immediate update
            
            pollInterval = setInterval(() => {
                loadScrapingLogs().then(isRunning => {
                    if (!isRunning) {
                        clearInterval(pollInterval);
                        pollInterval = null;

                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-play-fill"></i> Trigger Scrape';

                        loadDashboardStats(true); // reload stats and animate

                        const searchInput = document.getElementById('admin-search-input');
                        if (searchInput) {
                            searchInput.value = query;
                            searchAdminProducts();
                        }

                        showToast('Scraping complete!', 'success');
                    }
                });
            }, 3000);
        }, 1500);
    })
    .catch(() => {
        showToast('Failed to start scraping job', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill"></i> Trigger Scrape';
    });
}

function searchAdminProducts() {
    const query = document.getElementById('admin-search-input').value.trim();
    const tbody = document.getElementById('products-tbody');
    if (!tbody) return;

    if (!query) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Please enter a search term.</td></tr>';
        return;
    }

    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-border spinner-border-sm text-accent" role="status"></div> Searching...</td></tr>';

    fetch(`/api/search?q=${encodeURIComponent(query)}&per_page=50`)
        .then(r => r.json())
        .then(data => {
            if (data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No products found.</td></tr>';
                return;
            }
            tbody.innerHTML = data.items.map(p => `
                <tr id="admin-prow-${p.id}">
                    <td>
                        <a href="/product/${p.id}" target="_blank" class="text-decoration-none fw-600">${p.name}</a>
                    </td>
                    <td><span class="badge bg-primary-subtle text-primary">${p.store}</span></td>
                    <td class="fw-700">Rs. ${p.price?.toLocaleString()}</td>
                    <td>${p.discount > 0 ? `<span class="badge bg-danger">-${p.discount}%</span>` : '-'}</td>
                    <td class="text-muted">${new Date(p.last_updated).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteProduct(${p.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(() => {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error fetching products</td></tr>';
        });
}

function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this product?')) return;

    fetch(`/api/products/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            showToast(data.message || 'Product deleted', 'success');
            const row = document.getElementById(`admin-prow-${id}`);
            if (row) row.remove();
            loadDashboardStats();
        })
        .catch(() => {
            showToast('Failed to delete product', 'error');
        });
}
