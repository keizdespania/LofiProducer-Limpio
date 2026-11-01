// ═══ KEIZ OS · Analytics ═══
window.Views = window.Views || {};
window.Views.analytics = {
  onEnter: async function(){
    const v = document.getElementById('view-analytics');
    v.innerHTML = `
      <h1>📊 Analytics</h1>
      <p class="text-muted mt-2 mb-6">Métricas del ecosistema</p>
      <div id="analytics-content"><div class="empty-state"><div class="spinner"></div></div></div>
    `;
    try {
      const r = await App.api('/api/analytics').catch(()=>({}));
      const el = document.getElementById('analytics-content');
      const stats = [
        {label:'Vídeos totales', val:r.videos||0, icon:'🎬'},
        {label:'Posts generados', val:r.posts||0, icon:'📝'},
        {label:'Canales activos', val:r.canales||0, icon:'📺'},
        {label:'Tareas completadas', val:r.tareas||0, icon:'✅'},
      ];
      el.innerHTML = `<div class="grid-4 mb-6">${stats.map(s=>`<div class="card"><div class="stat"><div class="stat-value">${s.val}</div><div class="stat-label">${s.icon} ${s.label}</div></div></div>`).join('')}</div>
        <div class="card"><div class="card-header"><div class="card-title">📈 Detalles</div></div><pre class="text-xs" style="background:rgba(0,0,0,0.3);padding:12px;border-radius:8px;max-height:400px;overflow:auto">${JSON.stringify(r,null,2)}</pre></div>`;
    } catch(e){ document.getElementById('analytics-content').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
