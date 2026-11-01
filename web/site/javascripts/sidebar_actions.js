document.addEventListener("DOMContentLoaded", function() {
    const navList = document.querySelector('.md-nav--primary .md-nav__list');
    if (!navList || document.getElementById('custom-sidebar-actions')) return;

    const actionsContainer = document.createElement('div');
    actionsContainer.id = 'custom-sidebar-actions';
    actionsContainer.style.marginTop = '20px';
    actionsContainer.style.paddingTop = '20px';
    actionsContainer.style.borderTop = '1px solid rgba(255,255,255,0.1)';
    actionsContainer.innerHTML = '<h5 style="font-size: 0.7rem; font-weight: 700; color: #888; text-transform: uppercase; margin-bottom: 10px; padding-left: 12px;">Acciones</h5>';

    // 1. BÚSQUEDA
    const searchAction = document.createElement('div');
    searchAction.className = 'sidebar-action';
    searchAction.innerHTML = '🔍 Buscar';
    searchAction.onclick = () => {
        const searchLabel = document.querySelector('label[for="__search"]');
        if (searchLabel) searchLabel.click();
    };
    actionsContainer.appendChild(searchAction);

    // 2. MODO OSCURO/CLARO
    const themeAction = document.createElement('div');
    themeAction.className = 'sidebar-action';
    themeAction.innerHTML = '🌓 Cambiar Tema';
    themeAction.onclick = () => {
        const html = document.documentElement;
        const current = html.getAttribute('data-md-color-scheme');
        html.setAttribute('data-md-color-scheme', current === 'slate' ? 'default' : 'slate');
    };
    actionsContainer.appendChild(themeAction);

    // 3. IDIOMA (Lógica adaptada a GitHub Pages)
    const currentPath = window.location.pathname;
    // Detecta si estamos en la carpeta /en/
    const isEnglish = currentPath.includes('/en/');
    
    // Calcula la ruta base (sacando el /en/ si estamos en ella)
    let basePath = currentPath.replace(/\/en\/.*$/, '/');
    if (!basePath.endsWith('/')) basePath += '/';

    const langAction = document.createElement('a');
    langAction.className = 'sidebar-action';
    // Si estamos en inglés, volvemos a la raíz de la web (quitando /en/)
    // Si estamos en español, añadimos /en/
    langAction.href = isEnglish ? basePath : basePath + 'en/';
    langAction.innerHTML = isEnglish ? '🇪🇸 Español' : '🇬🇧 English';
    actionsContainer.appendChild(langAction);

    navList.appendChild(actionsContainer);
});
