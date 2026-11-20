// ═══ KEIZ OS · Cola de Producción ═══
window.Views = window.Views || {};
window.Views.produccion = {
  onEnter: function(){
    const v = document.getElementById('view-produccion');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>📋 Producción</h1><p class="text-muted mt-2">Cola de tareas + logs worker</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.produccion.refresh()">🔄 Refresh</button>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">📋 Cola de tareas</div><span class="badge badge-purple" id="prod-count">0</span></div>
        <div id="prod-cola"><div class="skeleton" style="height:40px"></div></div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">📜 Worker log (últimas 200)</div></div>
        <pre id="prod-worker" class="text-xs" style="max-height:400px;overflow:auto;background:rgba(0,0,0,0.3);padding:12px;border-radius:8px;color:var(--muted);font-family:var(--mono)">Cargando...</pre>
      </div>
    `;
    Views.produccion.refresh();
  },
  refresh: function(){
    Views.produccion.cargarCola();
    Views.produccion.cargarWorker();
  },
  cargarCola: async function(){
    const el = document.getElementById('prod-cola');
    try {
      const r = await App.api('/api/cola_tareas').catch(()=>({tareas:[]}));
      const t = r.tareas||[];
      document.getElementById('prod-count').textContent = t.length;
      if(!t.length){ el.innerHTML = '<div class="empty-state"><p>Cola vacía</p></div>'; return; }
      el.innerHTML = t.slice(0,20).map(x=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">${(x.prompt||x.id||'').substring(0,80)}</div><div class="text-sm text-muted">${x.actualizada||x.creada||''}</div></div>
          <span class="badge badge-${x.estado==='done'?'green':x.estado==='error'?'red':'blue'}">${x.estado}</span>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  cargarWorker: async function(){
    const el = document.getElementById('prod-worker');
    try {
      const r = await App.api('/api/worker_log?lineas=200').catch(()=>({log:''}));
      el.textContent = r.log || '(sin log)';
    } catch(e){ el.textContent = e.message; }
  }
};
