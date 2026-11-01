// ═══ KEIZ OS · Tendencias (real) ═══
window.Views = window.Views || {};
window.Views.tendencias = {
  onEnter: function(){
    const v = document.getElementById('view-tendencias');
    v.innerHTML = `
      <h1>🕵️ Tendencias</h1>
      <p class="text-muted mt-2 mb-6">Detective multi-fuente</p>
      <div class="card mb-6">
        <div class="flex gap-2" style="flex-wrap:wrap">
          <select id="tend-nicho" class="select" style="flex:1;min-width:150px">
            <option value="ia_news">El Encuadre</option>
            <option value="lofi">KEIZ Productions</option>
            <option value="finanzas_barrio">Finanzas</option>
            <option value="boe">BOE</option>
          </select>
          <button class="btn btn-primary" onclick="Views.tendencias.cargar(false)">📦 Guardado</button>
          <button class="btn btn-ghost" onclick="Views.tendencias.cargar(true)">🔍 Investigar (60s)</button>
        </div>
        <div id="tend-status" class="mt-4"></div>
      </div>
      <div id="tend-resultado"></div>
    `;
    Views.tendencias.cargar(false);
  },
  cargar: async function(enVivo){
    const nicho = document.getElementById('tend-nicho').value;
    const st = document.getElementById('tend-status');
    const res = document.getElementById('tend-resultado');
    st.innerHTML = `<div class="list-item"><span class="spinner"></span><span>${enVivo?'Investigando 5 fuentes (60-90s)...':'Cargando guardado...'}</span></div>`;
    try {
      const url = enVivo ? '/api/investigar/'+nicho : '/api/investigacion_guardada/'+nicho;
      const r = await App.api(url);
      // Detectar formato: array directo, {temas:[...]}, o {hackernews:[...],youtube:[...]}
      let temas = [];
      if(Array.isArray(r)) temas = r;
      else if(r.temas) temas = r.temas;
      else if(r.items) temas = r.items;
      else {
        Object.values(r).forEach(v => { if(Array.isArray(v)) temas.push(...v); });
      }
      st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--green)">✅ ${temas.length} temas</div>`;
      if(!temas.length){ res.innerHTML = '<div class="empty-state"><p>Sin datos. Prueba "Investigar" en vivo.</p></div>'; return; }
      res.innerHTML = `<div class="grid-2">${temas.slice(0,20).map(t=>`
        <div class="card">
          <div class="card-title mb-2">${String(t.titulo||t.title||'Sin título').substring(0,80)}</div>
          <p class="text-sm mb-2">${String(t.descripcion||t.summary||t.desc||'').substring(0,120)}</p>
          <div class="flex gap-2">
            <span class="badge badge-blue">${t.fuente||t.source||'?'}</span>
            ${t.score?`<span class="badge badge-purple">score ${t.score}</span>`:''}
            ${t.url||t.link?`<a href="${t.url||t.link}" target="_blank" class="btn btn-ghost btn-sm">🔗</a>`:''}
          </div>
        </div>
      `).join('')}</div>`;
    } catch(e){
      st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--red)">❌ ${e.message}</div>`;
      res.innerHTML = '';
    }
  }
};
