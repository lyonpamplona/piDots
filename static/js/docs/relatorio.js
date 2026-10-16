/**
 * PIDOTS RELATORIO DE ESTUDOS - NAVEGACAO E PESQUISA CLIENT-SIDE
 * =====================================================================
 * ZERO EMOJIS // Vanilla JS Puro // Alta Performance ARM64
 * =====================================================================
 */
        document.addEventListener('DOMContentLoaded', () => {
            const drawerToggleBtn = document.getElementById('drawerToggleBtn');
            const closeDrawerBtn = document.getElementById('closeDrawerBtn');
            const searchInput = document.getElementById('topicSearchInput');
            const navLinks = document.querySelectorAll('.nav-item-link');

            // Alternância do Drawer Lateral Direito
            function toggleDrawer() {
                document.body.classList.toggle('drawer-open');
            }

            drawerToggleBtn.addEventListener('click', toggleDrawer);
            closeDrawerBtn.addEventListener('click', toggleDrawer);

            // Filtro de Pesquisa em Tempo Real
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

            // Smooth Scroll com ajuste do drawer em telas menores
            navLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    if (window.innerWidth <= 900) {
                        document.body.classList.remove('drawer-open');
                    }
                });
            });
        });

