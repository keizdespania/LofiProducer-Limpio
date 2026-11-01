// ═══ KEIZ OS · Tendencias (Detective) ═══
window.Views = window.Views || {};
window.Views.tendencias = {
  onEnter: function(){
    const v = document.getElementById('view-tendencias');
    v.innerHTML = `
      <h1>🕵️ Tendencias</h1>
      <p class="text-muted mt-2 mb-6">Detective multi-fuente: YouTube, Reddit, HN, Trends</p>
      <div class="card mb-6">
        <div class="flex gap-2" style="flex-wrap:wrap">
          <select id="tend-nicho" class="select" style="flex:1;min-width:150px">
            <option value="ia_news">IA News</option>
            <option value="finanzas_barrio">Finanzas Barrio</option>
            <option value="boe">BOE</option>
            <option value="lofi">Lofi</option>
          </select>
          <button class="btn btn-primary" onclick="Views.tendencias.investigar(true)">🔍 Investigar ahora (60s)</button>
          <button class="btn btn-ghost" onclick="Views.tendencias.investigar(false)">📦 Guardado</button>
        </div>
        <div id="tend-status" class="mt-4"></div>
      </div>
      <div id="tend-resultado"></div>
    `;
  },
  investigar: async function(enVivo){
    const nicho = document.getElementById('tend-nicho').value;
    const st = document.getElementById('tend-status');
    const res = document.getElementById('tend-resultado');
    st.innerHTML = `<div class="list-item"><span class="spinner"></span><span>${enVivo?'Investigando 5 fuentes...':'Cargando guardado...'}</span></div>`;
    res.innerHTML = '';
    try {
      const url = enVivo ? '/api/investigar/'+nicho : '/api/investigacion_guardada/'+nicho;
      const r = await App.api(url);
      st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--green)">✅ ${(r.temas||r.items||[]).length} temas encontrados</div>`;
      const temas = r.temas || r.items || [];
      if(!temas.length){ res.innerHTML = '<div class="empty-state"><p>Sin temas</p></div>'; return; }
      res.innerHTML = `<div class="grid-2">${temas.map(t=>`
        <div class="card">
          <div class="card-title mb-2">${t.titulo||t.title||'Sin título'}</div>
          <p class="text-sm mb-2">${(t.descripcion||t.summary||'').substring(0,120)}</p>
          <div class="flex gap-2">
            <span class="badge badge-blue">${t.fuente||t.source||'?'}</span>
            ${t.url?`<a href="${t.url}" target="_blank" class="btn btn-ghost btn-sm">🔗 Ver</a>`:''}
            <button class="btn btn-primary btn-sm" onclick="Views.tendencias.producir('${(t.titulo||t.title||'').replace(/'/g,'')}')">🚀 Producir</button>
          </div>
        </div>
      `).join('')}</div>`;
    } catch(e){ st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--red)">❌ ${e.message}</div>`; }
  },
  producir: async function(tema){
    if(!confirm('¿Producir "'+tema+'"?')) return;
    try { await App.api('/api/producir_nicho',{method:'POST',body:{tema}}); App.toast('Producción lanzada 🚀','success'); } catch(e){}
  }
};
