// ═══ KEIZ OS · Papelera (virtual, sin 1600L inline) ═══
window.Views = window.Views || {};
window.Views.papelera = {
  onEnter: async function(){
    const v = document.getElementById('view-papelera');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🗑️ Papelera</h1><p class="text-muted mt-2">Recupera o vacía</p></div>
        <div class="flex gap-2">
          <button class="btn btn-ghost btn-sm" onclick="Views.papelera.cargar()">🔄 Refresh</button>
          <button class="btn btn-danger btn-sm" onclick="Views.papelera.vaciar()">🧹 Vaciar</button>
        </div>
      </div>
      <div id="pap-content"><div class="empty-state"><div class="spinner"></div></div></div>
    `;
    Views.papelera.cargar();
  },
  cargar: async function(){
    const el = document.getElementById('pap-content');
    try {
      const r = await App.api('/api/papelera/listar').catch(()=>({items:[]}));
      const arr = r.items || r.canales || [];
      if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">🗑️</div><p>Papelera vacía</p></div>'; return; }
      el.innerHTML = arr.map(i=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">${i.nombre||i.filename||i.id}</div><div class="text-sm text-muted">${i.fecha||''}</div></div>
          <button class="btn btn-ghost btn-sm" onclick="Views.papelera.restaurar('${i.nombre||i.id}')">↩ Restaurar</button>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  restaurar: async function(nombre){
    try { await App.api('/api/papelera/restaurar',{method:'POST',body:{nombre}}); App.toast('Restaurado','success'); Views.papelera.cargar(); } catch(e){}
  },
  vaciar: async function(){
    if(!confirm('¿Vaciar papelera? Esta acción no se puede deshacer.')) return;
    try { await App.api('/api/papelera/vaciar',{method:'POST'}); App.toast('Papelera vaciada','success'); Views.papelera.cargar(); } catch(e){}
  }
};
