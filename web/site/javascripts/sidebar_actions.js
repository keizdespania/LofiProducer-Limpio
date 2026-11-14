document.addEventListener("DOMContentLoaded", function() {
    const navList = document.querySelector('.md-nav--primary .md-nav__list');
    if (!navList || document.getElementById('custom-sidebar-actions')) return;

    const actionsContainer = document.createElement('div');
    actionsContainer.id = 'custom-sidebar-actions';
    actionsContainer.innerHTML = '<h5>Acciones</h5>';

    // 1. BÚSQUEDA
    const searchAction = document.createElement('div');
    searchAction.className = 'sidebar-action';
    searchAction.innerHTML = '🔍 Buscar';
    searchAction.onclick = () => {
        const searchLabel = document.querySelector('label[for="__search"]');
        if (searchLabel) searchLabel.click();
    };
    actionsContainer.appendChild(searchAction);

    // 2. MODO OSCURO/CLARO (disparar el checkbox real de Material)
    const themeAction = document.createElement('div');
    themeAction.className = 'sidebar-action';
    themeAction.innerHTML = '🌓 Cambiar tema';
    themeAction.onclick = () => {
        const scheme = document.documentElement.getAttribute('data-md-color-scheme');
        // Material escucha el media query del sistema + input checkbox
        const palette = document.querySelector('[data-md-component="palette"]');
        if (palette) {
            const current = palette.checked;
            palette.checked = !current;
            palette.dispatchEvent(new Event('change', { bubbles: true }));
            localStorage.setItem('__palette', !current ? 'slate' : 'default');
        } else {
            // Fallback: cambiar manualmente el atributo
            const newScheme = scheme === 'slate' ? 'default' : 'slate';
            document.documentElement.setAttribute('data-md-color-scheme', newScheme);
            localStorage.setItem('__palette', newScheme);
        }
    };
    actionsContainer.appendChild(themeAction);

    // 3. ENLACE A LA VERSIÓN EN INGLÉS (solo si existe, si no, aviso)
    const currentPath = window.location.pathname;
    const isEnglish = currentPath.includes('/en/');
    const langAction = document.createElement('a');
    langAction.className = 'sidebar-action';
    if (isEnglish) {
        langAction.href = '/';
        langAction.innerHTML = '🇪🇸 Español';
    } else {
        langAction.href = '/en/';
        langAction.innerHTML = '🇬🇧 English';
    }
    actionsContainer.appendChild(langAction);

    navList.appendChild(actionsContainer);
});
