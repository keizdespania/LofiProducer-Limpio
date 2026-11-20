// ═══ KEIZ OS · Mis Canales (real) ═══
window.Views = window.Views || {};
window.Views.canales = {
  onEnter: async function(){
    const v = document.getElementById('view-canales');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>📺 Mis Canales</h1><p class="text-muted mt-2">Canales reales del ecosistema</p></div>
        <button class="btn btn-primary" onclick="Views.canales.modalCrear()">➕ Crear nicho</button>
      </div>
      <div id="canales-list"><div class="empty-state"><div class="spinner"></div></div></div>
      <div id="canal-modal" class="modal" onclick="if(event.target.id==='canal-modal')Views.canales.cerrarModal()">
        <div class="modal-content">
          <div class="modal-header"><div class="card-title">➕ Nuevo nicho</div><button class="modal-close" onclick="Views.canales.cerrarModal()">✕</button></div>
          <div class="flex flex-col gap-3">
            <input id="nic-id" class="input" placeholder="ID (ej: ia_news, lofi)">
            <input id="nic-nombre" class="input" placeholder="Nombre visible">
            <input id="nic-tono" class="input" placeholder="Tono (ej: intriga, thriller)">
            <input id="nic-queries" class="input" placeholder="Queries YouTube (coma separadas)">
            <input id="nic-subreddits" class="input" placeholder="Subreddits (coma separadas)">
            <button class="btn btn-primary btn-lg" onclick="Views.canales.crear()">✨ Crear nicho</button>
          </div>
        </div>
      </div>
    `;
    Views.canales.cargar();
    if(Views.canales._iv) clearInterval(Views.canales._iv);
    Views.canales._iv = setInterval(()=>Views.canales.cargar(), 30000);
  },
  cargar: async function(){
    const el = document.getElementById('canales-list');
    if(!el) return;
    try {
      const r = await App.api('/api/canales_web').catch(()=>({canales_creados:[],nichos_base:[]}));
      const canales = r.canales_creados || [];
      // También añadir los nichos_base que no estén como canal
      const existentes = new Set(canales.map(c=>c.id));
      const extras = (r.nichos_base||[]).filter(n=>!existentes.has(n)).map(n=>({id:n, nombre:n, icono:'📺', color:'#3b82f6'}));
      const todos = [...canales, ...extras];
      if(!todos.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📺</div><p>Sin canales</p></div>'; return; }
      el.innerHTML = `<div class="grid-2">${todos.map(c=>`
        <div class="card" style="border-left:4px solid ${c.color||'var(--purple)'}">
          <div class="flex between center mb-2">
            <div class="card-title" style="font-size:1.15em">${c.icono||'📺'} ${c.nombre||c.id}</div>
            <span class="badge badge-purple">${c.estado||'activo'}</span>
          </div>
          <p class="text-sm mb-2"><strong>${c.nombre_real||c.id}</strong></p>
          <p class="text-sm text-muted mb-4">${c.tono||'Sin tono'}</p>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm" style="flex:1" onclick="Views.canales.producir('${c.id}')">🎬 Producir</button>
            <button class="btn btn-ghost btn-sm" onclick="Views.canales.investigar('${c.id}')" title="Investigar">🕵️</button>
          </div>
        </div>
      `).join('')}</div>`;
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  modalCrear: function(){ document.getElementById('canal-modal').classList.add('open'); },
  cerrarModal: function(){ document.getElementById('canal-modal').classList.remove('open'); },
  crear: async function(){
    const id = document.getElementById('nic-id').value.trim();
    const nombre = document.getElementById('nic-nombre').value.trim();
    if(!id || !nombre){ App.toast('ID y nombre obligatorios','warning'); return; }
    try {
      await App.api('/api/crear_nicho',{method:'POST',body:{
        id, nombre,
        tono: document.getElementById('nic-tono').value,
        queries_youtube: document.getElementById('nic-queries').value.split(',').map(s=>s.trim()).filter(Boolean),
        subreddits: document.getElementById('nic-subreddits').value.split(',').map(s=>s.trim()).filter(Boolean),
      }});
      App.toast('Nicho creado ✅','success');
      Views.canales.cerrarModal();
      Views.canales.cargar();
    } catch(e){}
  },
  producir: async function(id){
    if(!confirm('¿Lanzar producción de nicho "'+id+'"?')) return;
    try { await App.api('/api/producir_nicho',{method:'POST',body:{nicho:id}}); App.toast('Producción lanzada 🚀','success'); } catch(e){}
  },
  investigar: async function(id){
    App.toast('Investigando '+id+'... (60s)','info');
    try { const r = await App.api('/api/investigar/'+id); App.toast(`${(r.temas||r.items||[]).length} temas encontrados`,'success'); } catch(e){}
  }
};
