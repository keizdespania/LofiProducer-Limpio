// ═══ KEIZ OS · Media Vault (real) ═══
window.Views = window.Views || {};
window.Views.media = {
  filtro: 'todos', archivos: [],
  onEnter: function(){
    const v = document.getElementById('view-media');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎞️ Media Vault</h1><p class="text-muted mt-2">Todo lo producido (últimos 50)</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.media.cargar()">🔄 Refresh</button>
      </div>
      <div class="card mb-6">
        <div class="flex gap-2" id="media-filtros">
          ${['todos','musica','video','imagen','voz'].map(f=>`<button class="btn btn-ghost btn-sm ${f==='todos'?'btn-primary':''}" data-f="${f}" onclick="Views.media.filtrar('${f}')">${f}</button>`).join('')}
        </div>
      </div>
      <div id="media-content"><div class="empty-state"><div class="spinner"></div><p class="mt-4">Cargando...</p></div></div>
      <div id="media-lightbox" class="modal" onclick="if(event.target.id==='media-lightbox')Views.media.cerrarLightbox()"><div class="modal-content" style="max-width:900px" id="media-lb-body"></div></div>
    `;
    Views.media.cargar();
  },
  filtrar: function(f){ Views.media.filtro = f; document.querySelectorAll('#media-filtros button').forEach(b=>b.classList.toggle('btn-primary', b.dataset.f===f)); Views.media.renderizar(); },
  cargar: async function(){
    const el = document.getElementById('media-content');
    try {
      // Buscar archivos reales en output/ por tipo
      const tipos = ['musica','videos','imagenes','voz','encuadre'];
      const archivos = [];
      for(const t of tipos){
        try {
          const r = await App.api('/api/media?tipo='+t).catch(()=>null);
          if(r && (r.files||r.archivos)) archivos.push(...(r.files||r.archivos).map(a=>({...a, tipo:t})));
        } catch(e){}
      }
      if(!archivos.length){
        // Fallback: usar media_vault
        const r = await App.api('/api/media_vault').catch(()=>({archivos:[]}));
        Views.media.archivos = r.archivos || r.files || [];
      } else {
        Views.media.archivos = archivos;
      }
      Views.media.renderizar();
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  renderizar: function(){
    const el = document.getElementById('media-content');
    let arr = Views.media.archivos;
    if(Views.media.filtro !== 'todos') arr = arr.filter(a => (a.tipo||'').includes(Views.media.filtro) || (a.filename||a.name||'').includes(Views.media.filtro));
    if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📦</div><p>Sin archivos ('+Views.media.archivos.length+' total)</p></div>'; return; }
    el.innerHTML = `<div class="text-sm text-muted mb-4">${arr.length} archivos</div><div class="grid-4">${arr.slice(0,50).map(a=>Views.media.tarjeta(a)).join('')}</div>`;
  },
  tarjeta: function(a){
    const ext = (a.filename||a.name||'').split('.').pop().toLowerCase();
    const url = a.url || ('/media/' + (a.filename||a.name||''));
    if(['mp4','webm','mov'].includes(ext)) return `<div class="card" style="padding:8px;cursor:pointer" onclick="Views.media.lightbox('${url}','video')"><video src="${url}" style="width:100%;border-radius:8px;aspect-ratio:16/9;object-fit:cover" muted preload="metadata"></video><div class="text-sm mt-2 truncate">🎬 ${a.filename||a.name}</div></div>`;
    if(['mp3','wav','ogg'].includes(ext)) return `<div class="card" style="padding:8px;cursor:pointer" onclick="Views.media.lightbox('${url}','audio')"><div style="aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:3em;background:rgba(139,92,246,0.1);border-radius:8px">🎵</div><div class="text-sm mt-2 truncate">${a.filename||a.name}</div></div>`;
    if(['png','jpg','jpeg','webp'].includes(ext)) return `<div class="card" style="padding:8px;cursor:pointer" onclick="Views.media.lightbox('${url}','image')"><img src="${url}" style="width:100%;border-radius:8px;aspect-ratio:1;object-fit:cover" loading="lazy"><div class="text-sm mt-2 truncate">🖼 ${a.filename||a.name}</div></div>`;
    return `<div class="card" style="padding:12px"><div style="font-size:2em">📄</div><div class="text-sm truncate mt-2">${a.filename||a.name}</div></div>`;
  },
  lightbox: function(url, tipo){
    const lb = document.getElementById('media-lightbox'); const body = document.getElementById('media-lb-body');
    const inner = tipo==='video' ? `<video controls autoplay src="${url}" style="width:100%;border-radius:8px"></video>` : tipo==='audio' ? `<audio controls autoplay src="${url}" style="width:100%"></audio>` : `<img src="${url}" style="width:100%;border-radius:8px">`;
    body.innerHTML = `<div class="modal-header"><div class="card-title">${url.split('/').pop()}</div><button class="modal-close" onclick="Views.media.cerrarLightbox()">✕</button></div>${inner}<a href="${url}" target="_blank" class="btn btn-ghost mt-4">🔗 Abrir</a>`;
    lb.classList.add('open');
  },
  cerrarLightbox: function(){ document.getElementById('media-lightbox').classList.remove('open'); }
};
