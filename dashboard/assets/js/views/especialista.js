// ═══ KEIZ OS · Especialistas (10 roles LLM) ═══
window.Views = window.Views || {};
window.Views.especialista = {
  onEnter: async function(){
    const v = document.getElementById('view-especialista');
    v.innerHTML = `
      <h1>🧠 Especialistas</h1>
      <p class="text-muted mt-2 mb-6">10 roles LLM del ecosistema</p>
      <div id="esp-list"><div class="empty-state"><div class="spinner"></div></div></div>
      <div class="card mt-6">
        <div class="card-header"><div class="card-title">💬 Consultar especialista</div></div>
        <select id="esp-select" class="select mb-4">
          <option>Cargando...</option>
        </select>
        <textarea id="esp-input" class="textarea mb-4" placeholder="Escribe tu pregunta..."></textarea>
        <button class="btn btn-primary" style="width:100%" onclick="Views.especialista.consultar()">💬 Enviar</button>
        <div id="esp-resp" class="mt-4"></div>
      </div>
    `;
    try {
      const r = await App.api('/api/especialistas').catch(()=>({especialistas:[]}));
      const arr = r.especialistas || [];
      const el = document.getElementById('esp-list');
      const sel = document.getElementById('esp-select');
      if(!arr.length){ el.innerHTML = '<div class="empty-state"><p>Sin especialistas</p></div>'; return; }
      el.innerHTML = `<div class="grid-2">${arr.map(e=>`<div class="card"><div class="card-title">${e.icono||'🧠'} ${e.nombre||e}</div><p class="text-sm mt-2">${e.descripcion||''}</p></div>`).join('')}</div>`;
      sel.innerHTML = arr.map(e=>`<option value="${e.id||e.nombre||e}">${e.nombre||e}</option>`).join('');
    } catch(e){ document.getElementById('esp-list').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  consultar: async function(){
    const esp = document.getElementById('esp-select').value;
    const texto = document.getElementById('esp-input').value.trim();
    if(!texto) return;
    const el = document.getElementById('esp-resp');
    el.innerHTML = '<div class="list-item"><span class="spinner"></span></div>';
    try {
      const r = await App.api('/api/especialista',{method:'POST',body:{especialista:esp,texto}});
      el.innerHTML = `<div class="card"><pre style="white-space:pre-wrap;font-family:var(--font)">${r.respuesta||r.msg||JSON.stringify(r)}</pre></div>`;
    } catch(e){ el.innerHTML = `<div class="card" style="border-left:3px solid var(--red)"><p>${e.message}</p></div>`; }
  }
};
