document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. Get Data from the 'window' object ---
    // This data is provided by a small script in index.html
    if (!window.chartData) {
        console.error('Chart data not found.');
        return;
    }

    const statusData = window.chartData.status;
    const sectorData = window.chartData.sector;
    
    // Check current theme for chart text color
    const isDarkMode = document.body.classList.contains('dark-mode') || 
                       (localStorage.getItem('theme') === 'dark');
    const chartTextColor = isDarkMode ? '#adbac7' : '#343a40';
    
    // Custom colors for charts
    const chartColors = [
        '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d', '#fd7e14'
    ];
    
    // --- 2. Draw "Loan by Status" Chart ---
    if (document.getElementById('statusChart') && statusData && statusData.labels.length > 0) {
        const ctxStatus = document.getElementById('statusChart').getContext('2d');
        new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: statusData.labels,
                datasets: [{
                    label: 'Loans',
                    data: statusData.data,
                    backgroundColor: chartColors,
                    borderColor: isDarkMode ? '#2d333b' : '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: chartTextColor // Set text color for theme
                        }
                    }
                }
            }
        });
    }
    
    // --- 3. Draw "Loan by Sector" Chart ---
    if (document.getElementById('sectorChart') && sectorData && sectorData.labels.length > 0) {
        const ctxSector = document.getElementById('sectorChart').getContext('2d');
        new Chart(ctxSector, {
            type: 'pie',
            data: {
                labels: sectorData.labels,
                datasets: [{
                    label: 'Loans',
                    data: sectorData.data,
                    backgroundColor: chartColors,
                    borderColor: isDarkMode ? '#2d333b' : '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: chartTextColor // Set text color for theme
                        }
                    }
                }
            }
        });
    }
});