// ═══ KEIZ OS · Documentación ═══
window.Views = window.Views || {};
window.Views.docs = {
  onEnter: async function(){
    const v = document.getElementById('view-docs');
    v.innerHTML = `<h1>📚 Documentación</h1><p class="text-muted mt-2 mb-6">Manuales del ecosistema</p><div id="docs-content"><div class="empty-state"><div class="spinner"></div></div></div>`;
    try {
      const r = await App.api('/api/docs').catch(()=>({docs:[]}));
      const arr = r.docs || r.files || [];
      const el = document.getElementById('docs-content');
      if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📚</div><p>Sin docs disponibles</p></div>'; return; }
      el.innerHTML = `<div class="grid-2">${arr.map(d=>`<div class="card"><div class="card-title">📄 ${d.nombre||d.filename||d}</div>${d.resumen?`<p class="text-sm mt-2">${d.resumen}</p>`:''}</div>`).join('')}</div>`;
    } catch(e){ document.getElementById('docs-content').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
