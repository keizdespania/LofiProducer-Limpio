// ═══ KEIZ OS · Analytics (real) ═══
window.Views = window.Views || {};
window.Views.analytics = {
  onEnter: async function(){
    const v = document.getElementById('view-analytics');
    v.innerHTML = `<h1>📊 Analytics</h1><p class="text-muted mt-2 mb-6">Métricas del ecosistema en vivo</p><div id="analytics-content"><div class="empty-state"><div class="spinner"></div></div></div>`;
    
    try {
      // 1. Cargar datos en paralelo (sistema + tráfico web)
      const [dash, canales, cola, cf] = await Promise.all([
        App.api('/api/dashboard').catch(()=>({})),
        App.api('/api/canales_web').catch(()=>({canales_creados:[]})),
        App.api('/api/cola_tareas').catch(()=>[]),
        App.api('/api/cloudflare/stats').catch(()=>({page_views:0, visitas:0, top_paginas:[], top_paises:[]}))
      ]);

      // 2. Tarjetas superiores (Sistema + Web)
      const stats = [
        {label:'Canales', val:(canales.canales_creados||[]).length, icon:'📺'},
        {label:'Tareas totales', val:(cola||[]).length, icon:'📋'},
        {label:'Page Views (7d)', val:cf.page_views || 0, icon:'🌐'},
        {label:'Visitas Únicas', val:cf.visitas || 0, icon:'👥'},
      ];
      
      const tareas = (cola||[]).slice(0,10);
      const topPais = cf.top_paises && cf.top_paises.length ? cf.top_paises[0][0] : '—';
      const topPag = cf.top_paginas && cf.top_paginas.length ? cf.top_paginas[0][0].replace(/\/$/, '').split('/').pop() : '—';
      
      const el = document.getElementById('analytics-content');
      el.innerHTML = `
        <!-- Grid superior de métricas -->
        <div class="grid-4 mb-6">
          ${stats.map(s=>`
            <div class="card">
              <div class="stat">
                <div class="stat-value" style="font-size:1.6em">${s.val}</div>
                <div class="stat-label">${s.icon} ${s.label}</div>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Tarjeta de tráfico web (Cloudflare) -->
        <div class="card mb-6">
          <div class="card-header">
            <div class="card-title">🌐 Tráfico Web (Cloudflare · 7d)</div>
            <span class="badge badge-blue">RUM Real</span>
          </div>
          <div class="flex gap-6 mt-4">
            <div style="flex:1">
              <div class="text-sm text-muted">Top País</div>
              <div class="card-title mt-1">${topPais}</div>
            </div>
            <div style="flex:1">
              <div class="text-sm text-muted">Top Página</div>
              <div class="card-title mt-1 truncate">${topPag}</div>
            </div>
          </div>
          ${cf.page_views === 0 ? '<div class="text-sm text-muted mt-4" style="text-align:center;">⏳ El beacon de Cloudflare se acaba de activar. Los datos aparecerán en unas horas.</div>' : ''}
        </div>

        <!-- Salud del sistema -->
        <div class="card mb-6">
          <div class="card-header"><div class="card-title">🩺 Salud del sistema</div></div>
          ${Object.entries(dash.salud||{}).map(([k,v])=>`<div class="list-item mb-2"><span>${k}</span><span class="badge badge-${v==='ok'?'green':'yellow'}">${v}</span></div>`).join('')}
        </div>

        <!-- Últimas tareas -->
        <div class="card">
          <div class="card-header"><div class="card-title">📋 Últimas tareas</div></div>
          ${tareas.length?tareas.map(t=>`<div class="list-item mb-2"><div style="flex:1"><div class="truncate">${(t.prompt||'').substring(0,80)}</div><div class="text-sm text-muted">${t.creada||''}</div></div><span class="badge badge-${t.estado==='done'?'green':t.estado==='error'?'red':'blue'}">${t.estado}</span></div>`).join(''):'<p class="text-muted">Sin tareas</p>'}
        </div>
      `;
    } catch(e){ document.getElementById('analytics-content').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
