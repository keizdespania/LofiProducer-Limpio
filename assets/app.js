/* ═══ KEIZ OS - LÓGICA ═══ */

// 1. NAVEGACIÓN
function nav(viewId, el = null) {
    // Ocultar todas las vistas
    document.querySelectorAll('main').forEach(v => v.classList.remove('active'));
    // Mostrar la seleccionada
    const target = document.getElementById('view-' + viewId);
    if (target) target.classList.add('active');
    
    // Actualizar barra inferior
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        // Si se llama desde una tarjeta, buscar el nav correspondiente
        const navItem = document.querySelector(`.nav-item[onclick*="'${viewId}'"]`);
        if (navItem) navItem.classList.add('active');
    }

    // Cargar datos según la vista
    if (viewId === 'inicio') cargarDashboard();
    if (viewId === 'media') loadVault();
}

// 2. DASHBOARD (Inicio)
async function cargarDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        
        // Estado
        const statusList = document.getElementById('dash-status-list');
        if (statusList && data.salud) {
            statusList.innerHTML = `
                <p>Flask: ${data.salud.flask === 'ok' ? '🟢' : '🔴'}</p>
                <p>OmniRoute: ${data.salud.omniroute === 'ok' ? '🟢' : '🔴'}</p>
                <p>Worker: ${data.salud.worker === 'ok' ? '🟢' : '🔴'}</p>
            `;
        }

        // Tareas
        const taskList = document.getElementById('dash-tasks-list');
        if (taskList && data.tareas) {
            if (data.tareas.length === 0) {
                taskList.innerHTML = '<p>Sin actividad reciente.</p>';
            } else {
                taskList.innerHTML = data.tareas.slice(0, 3).map(t => `
                    <p style="margin-bottom:4px;"><b>${t.estado === 'done' ? '✅' : '⏳'}</b> ${t.prompt.substring(0, 30)}...</p>
                `).join('');
            }
        }
    } catch(e) { console.error('Error dashboard:', e); }
}

// 3. MEDIA VAULT
async function loadVault() {
    const grid = document.getElementById('vault-grid');
    if (!grid) return;
    grid.innerHTML = '<p class="loading-text">Buscando archivos...</p>';
    
    try {
        const res = await fetch('/api/media_vault');
        const items = await res.json();
        
        if (items.length === 0) {
            grid.innerHTML = '<p class="loading-text">El Vault está vacío.</p>';
            return;
        }

        grid.innerHTML = items.map(item => `
            <div class="vault-item" onclick="openMedia('${item.url}', '${item.tipo}')">
                <div class="vault-thumb">
                    ${item.tipo === 'video' ? '🎬' : item.tipo === 'audio' ? '🎵' : '🖼️'}
                </div>
                <div class="vault-name">${item.nombre}</div>
                <div class="vault-meta">${item.fecha} · ${(item.tamano/1024/1024).toFixed(1)}MB</div>
            </div>
        `).join('');
    } catch(e) {
        grid.innerHTML = '<p class="loading-text">Error de conexión.</p>';
    }
}

// 4. MODAL (Lightbox)
function openMedia(url, tipo) {
    const modal = document.getElementById('media-modal');
    const container = document.getElementById('modal-media-container');
    
    if (tipo === 'video') container.innerHTML = `<video src="${url}" controls autoplay></video>`;
    else if (tipo === 'audio') container.innerHTML = `<audio src="${url}" controls autoplay></audio>`;
    else container.innerHTML = `<img src="${url}">`;
    
    modal.classList.add('open');
}

function closeModal() {
    const modal = document.getElementById('media-modal');
    const container = document.getElementById('modal-media-container');
    modal.classList.remove('open');
    // Parar reproducción al cerrar
    container.innerHTML = ''; 
}

// 5. EFECTO 3D EN LAS TARJETAS (Tilt)
document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', e => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = ((y - centerY) / centerY) * -5;
        const rotateY = ((x - centerX) / centerX) * 5;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
    });
});

// 6. INICIALIZACIÓN
document.addEventListener('DOMContentLoaded', () => {
    cargarDashboard();
});
