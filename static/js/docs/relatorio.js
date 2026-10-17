/**
 * PIDOTS RELATORIO DE ESTUDOS - NAVEGACAO E PESQUISA CLIENT-SIDE
 * =====================================================================
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */
document.addEventListener('DOMContentLoaded', () => {
    const drawerToggleBtn = document.getElementById('drawerToggleBtn');
    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    const drawerBackdrop = document.getElementById('drawerBackdrop');
    const searchInput = document.getElementById('topicSearchInput');
    const navLinks = document.querySelectorAll('.nav-item-link');

    // Alternância do Drawer Lateral Direito com ScrollLockManager
    function toggleDrawer() {
        const isOpen = document.body.classList.toggle('drawer-open');
        if (window.innerWidth <= 900 && window.ScrollLockManager) {
            if (isOpen) {
                window.ScrollLockManager.bloquear();
            } else {
                window.ScrollLockManager.desbloquear();
            }
        }
    }

    // Exporta globalmente para compatibilidade de atalhos e inline onclick
    window.toggleDrawer = toggleDrawer;

    if (drawerToggleBtn) drawerToggleBtn.addEventListener('click', toggleDrawer);
    if (closeDrawerBtn) closeDrawerBtn.addEventListener('click', toggleDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener('click', toggleDrawer);

    // Filtro de Pesquisa em Tempo Real
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            navLinks.forEach(link => {
                const searchData = (link.getAttribute('data-title') + ' ' + link.textContent).toLowerCase();
                if (searchData.includes(term)) {
                    link.style.display = 'flex';
                } else {
                    link.style.display = 'none';
                }
            });
        });
    }

    // Smooth Scroll com fechamento gracioso do drawer em telas menores
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 900) {
                if (document.body.classList.contains('drawer-open')) {
                    document.body.classList.remove('drawer-open');
                    if (window.ScrollLockManager) {
                        window.ScrollLockManager.desbloquear();
                    }
                }
            }
        });
    });
});

