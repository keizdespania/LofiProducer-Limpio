// ═══ KEIZ OS · Mis Canales (nichos) ═══
window.Views = window.Views || {};
window.Views.canales = {
  onEnter: async function(){
    const v = document.getElementById('view-canales');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>📺 Mis Canales</h1><p class="text-muted mt-2">Crea y gestiona nichos</p></div>
        <button class="btn btn-primary" onclick="Views.canales.modalCrear()">➕ Crear nicho</button>
      </div>
      <div id="canales-list"><div class="empty-state"><div class="spinner"></div></div></div>
      <div id="canal-modal" class="modal" onclick="if(event.target.id==='canal-modal')Views.canales.cerrarModal()">
        <div class="modal-content">
          <div class="modal-header"><div class="card-title">➕ Nuevo nicho</div><button class="modal-close" onclick="Views.canales.cerrarModal()">✕</button></div>
          <div class="flex flex-col gap-3">
            <input id="nic-id" class="input" placeholder="ID (ej: ia_news, lofi)">
            <input id="nic-nombre" class="input" placeholder="Nombre (ej: IA News)">
            <input id="nic-tono" class="input" placeholder="Tono (ej: intriga, thriller tecnológico)">
            <input id="nic-queries" class="input" placeholder="Queries YouTube (coma separadas)">
            <input id="nic-subreddits" class="input" placeholder="Subreddits (coma separadas)">
            <button class="btn btn-primary btn-lg" onclick="Views.canales.crear()">✨ Crear nicho</button>
          </div>
        </div>
      </div>
    `;
    Views.canales.cargar();
  },
  cargar: async function(){
    const el = document.getElementById('canales-list');
    try {
      const r = await App.api('/api/canales_web').catch(()=>({canales:[]}));
      const arr = r.canales || [];
      if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📺</div><p>Aún no hay nichos. Crea el primero →</p></div>'; return; }
      el.innerHTML = `<div class="grid-2">${arr.map(c=>`
        <div class="card">
          <div class="flex between center mb-2">
            <div class="card-title">${c.icono||'📺'} ${c.nombre||c.id}</div>
            <span class="badge badge-purple">${c.id}</span>
          </div>
          <p class="text-sm mb-4">${c.tono||'Sin tono definido'}</p>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm" style="flex:1" onclick="Views.canales.producir('${c.id}')">🎬 Producir</button>
            <button class="btn btn-ghost btn-sm" onclick="Views.canales.investigar('${c.id}')">🕵️</button>
            <button class="btn btn-danger btn-sm" onclick="Views.canales.borrar('${c.id}','${c.nombre||c.id}')">🗑</button>
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
    if(!confirm('¿Lanzar producción de nicho '+id+'?')) return;
    try {
      await App.api('/api/producir_nicho',{method:'POST',body:{nicho:id}});
      App.toast('Producción lanzada 🎬','success');
    } catch(e){}
  },
  investigar: async function(id){
    App.toast('Investigando '+id+'... (60s)','info');
    try {
      const r = await App.api('/api/investigar/'+id);
      App.toast(`${(r.temas||[]).length} temas encontrados`,'success');
    } catch(e){}
  },
  borrar: async function(id, nombre){
    if(!confirm('¿Mover "'+nombre+'" a papelera?')) return;
    try {
      await App.api('/api/papelera/borrar_canal',{method:'POST',body:{id,nombre}});
      App.toast('Movido a papelera','success');
      Views.canales.cargar();
    } catch(e){}
  }
};
