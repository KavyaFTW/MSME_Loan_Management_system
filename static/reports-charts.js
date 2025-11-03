document.addEventListener('DOMContentLoaded', () => {

    if (!window.reportsData) {
        console.error('Reports data not found.');
        return;
    }

    // --- 1. Get Data ---
    const { status, sector, payments, disbursements } = window.reportsData;
    
    // Check theme
    const isDarkMode = document.body.classList.contains('dark-mode') || (localStorage.getItem('theme') === 'dark');
    const chartTextColor = isDarkMode ? '#adbac7' : '#343a40';
    const gridColor = isDarkMode ? '#444c56' : '#dee2e6';
    const chartColors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d'];

    // --- 2. Payment Collection (Line Chart) ---
    if (document.getElementById('paymentsChart') && payments.labels.length > 0) {
        const ctx = document.getElementById('paymentsChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: payments.labels,
                datasets: [{
                    label: 'Amount Collected',
                    data: payments.data,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                plugins: { legend: { labels: { color: chartTextColor } } },
                scales: {
                    y: { 
                        ticks: { color: chartTextColor },
                        grid: { color: gridColor }
                    },
                    x: { 
                        ticks: { color: chartTextColor },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    }

    // --- 3. Loan Disbursement (Line Chart) ---
    if (document.getElementById('disbursementsChart') && disbursements.labels.length > 0) {
        const ctx = document.getElementById('disbursementsChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: disbursements.labels,
                datasets: [{
                    label: 'Amount Disbursed',
                    data: disbursements.data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                plugins: { legend: { labels: { color: chartTextColor } } },
                scales: {
                    y: { 
                        ticks: { color: chartTextColor },
                        grid: { color: gridColor }
                    },
                    x: { 
                        ticks: { color: chartTextColor },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    }

    // --- 4. Loan Status (Doughnut Chart) ---
    if (document.getElementById('statusChart') && status.labels.length > 0) {
        const ctx = document.getElementById('statusChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: status.labels,
                datasets: [{
                    data: status.data,
                    backgroundColor: chartColors,
                    borderColor: isDarkMode ? '#2d333b' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top', labels: { color: chartTextColor } }
                }
            }
        });
    }

    // --- 5. Loan Sector (Pie Chart) ---
    if (document.getElementById('sectorChart') && sector.labels.length > 0) {
        const ctx = document.getElementById('sectorChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: sector.labels,
                datasets: [{
                    data: sector.data,
                    backgroundColor: chartColors,
                    borderColor: isDarkMode ? '#2d333b' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top', labels: { color: chartTextColor } }
                }
            }
        });
    }

});
