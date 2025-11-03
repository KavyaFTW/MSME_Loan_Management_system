// Add this to your script.js

document.addEventListener('DOMContentLoaded', () => {

    // --- Keep your theme switcher code ---
    const themeSwitcher = document.querySelector('.theme-switcher');
    const body = document.body;

    if (themeSwitcher) {
        themeSwitcher.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });
    }

    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
    }
    // --- End of theme switcher code ---


    // --- New Tabbed Interface Code ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tabId = link.getAttribute('data-tab');

            // Deactivate all links and panels
            tabLinks.forEach(item => item.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));

            // Activate the clicked link and corresponding panel
            link.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    // --- End of tabbed interface code ---
});