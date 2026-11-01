// ═══ KEIZ OS · Analytics (real) ═══
window.Views = window.Views || {};
window.Views.analytics = {
  onEnter: async function(){
    const v = document.getElementById('view-analytics');
    v.innerHTML = `<h1>📊 Analytics</h1><p class="text-muted mt-2 mb-6">Métricas del ecosistema en vivo</p><div id="analytics-content"><div class="empty-state"><div class="spinner"></div></div></div>`;
    try {
      const [dash, canales, cola] = await Promise.all([
        App.api('/api/dashboard').catch(()=>({})),
        App.api('/api/canales_web').catch(()=>({canales_creados:[]})),
        App.api('/api/cola_tareas').catch(()=>[]),
      ]);
      const stats = [
        {label:'Canales', val:(canales.canales_creados||[]).length, icon:'📺', color:'purple'},
        {label:'Tareas totales', val:(cola||[]).length, icon:'📋', color:'blue'},
        {label:'Salud Flask', val:(dash.salud?.flask==='ok')?'OK':'⚠️', icon:'✅', color:'green'},
        {label:'Repo', val:dash.salud?.repo||'?', icon:'💾', color:'yellow'},
      ];
      const tareas = (cola||[]).slice(0,10);
      const el = document.getElementById('analytics-content');
      el.innerHTML = `
        <div class="grid-4 mb-6">${stats.map(s=>`<div class="card"><div class="stat"><div class="stat-value" style="font-size:1.6em">${s.val}</div><div class="stat-label">${s.icon} ${s.label}</div></div></div>`).join('')}</div>
        <div class="card mb-6">
          <div class="card-header"><div class="card-title">🩺 Salud del sistema</div></div>
          ${Object.entries(dash.salud||{}).map(([k,v])=>`<div class="list-item mb-2"><span>${k}</span><span class="badge badge-${v==='ok'?'green':'yellow'}">${v}</span></div>`).join('')}
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">📋 Últimas tareas</div></div>
          ${tareas.length?tareas.map(t=>`<div class="list-item mb-2"><div style="flex:1"><div class="truncate">${(t.prompt||'').substring(0,80)}</div><div class="text-sm text-muted">${t.creada||''}</div></div><span class="badge badge-${t.estado==='done'?'green':t.estado==='error'?'red':'blue'}">${t.estado}</span></div>`).join(''):'<p class="text-muted">Sin tareas</p>'}
        </div>
      `;
    } catch(e){ document.getElementById('analytics-content').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
