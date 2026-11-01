// ═══ KEIZ OS · Vista Inicio (cockpit) ═══
window.Views = window.Views || {};
window.Views.inicio = {
  onEnter: async function(){
    if(Views.inicio._iv) clearInterval(Views.inicio._iv);
    Views.inicio._iv = setInterval(()=>{ if(location.hash === "#inicio" || location.hash === "") Views.inicio.onEnter(); }, 30000);
    const v = document.getElementById('view-inicio');
    v.innerHTML = `
      <h1>Buenas, Arquitecto 👋</h1>
      <p class="text-muted mt-2">Estado del ecosistema en tiempo real</p>
      <div class="grid-4 mt-6" id="inicio-stats">
        <div class="card"><div class="stat"><div class="stat-value skeleton"></div><div class="stat-label">Cargando...</div></div></div>
        <div class="card"><div class="stat"><div class="stat-value skeleton"></div><div class="stat-label">Cargando...</div></div></div>
        <div class="card"><div class="stat"><div class="stat-value skeleton"></div><div class="stat-label">Cargando...</div></div></div>
        <div class="card"><div class="stat"><div class="stat-value skeleton"></div><div class="stat-label">Cargando...</div></div></div>
      </div>
      <div class="section mt-6">
        <div class="section-title">⚡ Acciones rápidas</div>
        <div class="grid-3">
          <div class="card" style="cursor:pointer" onclick="App.api('/api/encuadre/run_pipeline',{method:'POST'}).then(()=>App.toast('Pipeline lanzado','success'))">
            <div style="font-size:2em">🚀</div><div class="card-title mt-2">Lanzar pipeline</div><p class="text-sm">Genera el contenido de hoy</p>
          </div>
          <div class="card" style="cursor:pointer" onclick="location.hash='factory';App.route()">
            <div style="font-size:2em">🏭</div><div class="card-title mt-2">Ir a Factory</div><p class="text-sm">Ver producción de hoy</p>
          </div>
          <div class="card" style="cursor:pointer" onclick="CommandPalette.open()">
            <div style="font-size:2em">🔍</div><div class="card-title mt-2">Buscar <span class="kbd">Ctrl K</span></div><p class="text-sm">Cualquier vista o acción</p>
          </div>
        </div>
      </div>
      <div class="section mt-6">
        <div class="section-title">📊 Estado del sistema</div>
        <div id="inicio-sistema" class="grid-4">
          <div class="card"><span class="skeleton" style="display:block;height:40px"></span></div>
          <div class="card"><span class="skeleton" style="display:block;height:40px"></span></div>
          <div class="card"><span class="skeleton" style="display:block;height:40px"></span></div>
          <div class="card"><span class="skeleton" style="display:block;height:40px"></span></div>
        </div>
      </div>
    `;
    try {
      const r = await App.api('/api/dashboard');
      const stats = document.getElementById('inicio-stats');
      if(stats && r){
        stats.innerHTML = `
          <div class="card"><div class="stat"><div class="stat-value">${r.total_canales||0}</div><div class="stat-label">Canales</div></div></div>
          <div class="card"><div class="stat"><div class="stat-value">${r.total_tareas||0}</div><div class="stat-label">Tareas</div></div></div>
          <div class="card"><div class="stat"><div class="stat-value">${r.cola_pendiente||0}</div><div class="stat-label">En cola</div></div></div>
          <div class="card"><div class="stat"><div class="stat-value">${r.completadas_hoy||0}</div><div class="stat-label">Hoy</div></div></div>
        `;
      }
      // Estado servicios (best-effort)
      const sis = document.getElementById('inicio-sistema');
      if(sis){
        sis.innerHTML = `
          <div class="card"><div class="badge badge-green">● Flask :8001</div></div>
          <div class="card"><div class="badge badge-yellow">● OmniRoute :20128</div></div>
          <div class="card"><div class="badge badge-blue">● Worker</div></div>
          <div class="card"><div class="badge badge-green">● Cron</div></div>
        `;
      }
    } catch(e){ console.warn('Inicio:', e); }
  }
};
