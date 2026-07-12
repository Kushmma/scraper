// ── NepCompare Price History Chart Rendering ──

function renderPriceChart(canvasId, historyData, stats) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Parse labels and values
    const labels = historyData.map(h => new Date(h.recorded_at).toLocaleDateString());
    const prices = historyData.map(h => h.price);

    // If only one data point, duplicate it to show a line
    if (labels.length === 1) {
        labels.unshift('Initial');
        prices.unshift(prices[0]);
    }

    // Chart.js Configuration
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price (Rs.)',
                data: prices,
                borderColor: '#818cf8',
                backgroundColor: 'rgba(129, 140, 248, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#4f46e5',
                pointBorderColor: '#ffffff',
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Rs. ' + context.raw.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return 'Rs. ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}
