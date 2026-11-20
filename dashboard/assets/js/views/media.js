// ═══ KEIZ OS · Media Vault (real, formatos variados) ═══
window.Views = window.Views || {};
window.Views.media = {
  filtro: 'todos', archivos: [],
  onEnter: function(){
    const v = document.getElementById('view-media');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎞️ Media Vault</h1><p class="text-muted mt-2">Archivos reales del ecosistema</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.media.cargar()">🔄 Refresh</button>
      </div>
      <div class="card mb-6">
        <div class="flex gap-2" id="media-filtros">
          ${['todos','audio','video','imagen','tts'].map(f=>`<button class="btn btn-ghost btn-sm ${f==='todos'?'btn-primary':''}" data-f="${f}" onclick="Views.media.filtrar('${f}')">${f}</button>`).join('')}
        </div>
      </div>
      <div id="media-content"><div class="empty-state"><div class="spinner"></div></div></div>
      <div id="media-lightbox" class="modal" onclick="if(event.target.id==='media-lightbox')Views.media.cerrarLightbox()"><div class="modal-content" style="max-width:900px" id="media-lb-body"></div></div>
    `;
    Views.media.cargar();
  },
  filtrar: function(f){ Views.media.filtro = f; document.querySelectorAll('#media-filtros button').forEach(b=>b.classList.toggle('btn-primary', b.dataset.f===f)); Views.media.renderizar(); },
  cargar: async function(){
    const el = document.getElementById('media-content');
    try {
      const archivos = [];
      // 1) media_vault (formato: [{nombre,tipo,url,fecha,categoria}])
      const vault = await App.api('/api/media_vault').catch(()=>[]);
      const vaultArr = Array.isArray(vault) ? vault : (vault.archivos || vault.files || []);
      vaultArr.forEach(a => archivos.push({ nombre:a.nombre, tipo:a.tipo||'file', url:a.url, categoria:a.categoria, tamano:a.tamano, fecha:a.fecha }));

      // 2) media?tipo=musica (formato: {audio:[...]})
      const music = await App.api('/api/media?tipo=musica').catch(()=>null);
      if(music){
        (music.audio||music.files||[]).forEach(f => {
          const nombre = typeof f === 'string' ? f : (f.filename || f.name);
          archivos.push({ nombre, tipo:'audio', url:'/media/audios/'+nombre, categoria:'musica' });
        });
      }

      // Dedup por url
      const seen = new Set();
      Views.media.archivos = archivos.filter(a => { if(!a.url || seen.has(a.url)) return false; seen.add(a.url); return true; });
      Views.media.renderizar();
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  renderizar: function(){
    const el = document.getElementById('media-content');
    let arr = Views.media.archivos;
    if(Views.media.filtro !== 'todos') arr = arr.filter(a => (a.tipo||'').includes(Views.media.filtro) || (a.categoria||'').includes(Views.media.filtro));
    if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📦</div><p>Sin archivos en "'+Views.media.filtro+'" ('+Views.media.archivos.length+' total)</p></div>'; return; }
    const grupos = {};
    arr.forEach(a => {
      const fecha = (a.fecha || '').substring(0,10) || 'sin-fecha';
      grupos[fecha] = grupos[fecha] || []; grupos[fecha].push(a);
    });
    const fechas = Object.keys(grupos).sort().reverse();
    el.innerHTML = `<div class="text-sm text-muted mb-4">${arr.length} archivos · ${fechas.length} días</div>` + fechas.slice(0,10).map(f => `
      <div class="section">
        <div class="section-title">📅 ${f} <span class="badge badge-purple">${grupos[f].length}</span></div>
        <div class="grid-4">${grupos[f].slice(0,20).map(a => Views.media.tarjeta(a)).join('')}</div>
      </div>
    `).join('');
  },
  tarjeta: function(a){
    const url = a.url || '';
    const ext = (a.nombre||url).split('.').pop().toLowerCase();
    const tipo = a.tipo || '';
    const icono = tipo==='audio'||['mp3','wav'].includes(ext) ? '🎵' : tipo==='video'||['mp4','webm'].includes(ext) ? '🎬' : tipo==='imagen'||['png','jpg'].includes(ext) ? '🖼' : '📄';
    const isMedia = ['mp3','wav','mp4','webm','png','jpg','jpeg'].includes(ext);
    return `<div class="card" style="padding:8px;cursor:pointer" onclick="Views.media.lightbox('${url}','${icono==='🎵'?'audio':icono==='🎬'?'video':'image'}')">
      <div style="aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:2.5em;background:rgba(139,92,246,0.08);border-radius:8px">${icono}</div>
      <div class="text-sm mt-2 truncate" title="${a.nombre}">${a.nombre}</div>
      ${a.tamano?`<div class="text-xs text-muted">${(a.tamano/1048576).toFixed(1)} MB</div>`:''}
    </div>`;
  },
  lightbox: function(url, tipo){
    const lb = document.getElementById('media-lightbox'); const body = document.getElementById('media-lb-body');
    const inner = tipo==='video' ? `<video controls autoplay src="${url}" style="width:100%;border-radius:8px"></video>` : tipo==='audio' ? `<audio controls autoplay src="${url}" style="width:100%"></audio>` : `<img src="${url}" style="width:100%;border-radius:8px" onerror="this.style.display='none';this.parentNode.innerHTML+='<p class=&quot;text-muted&quot;>No preview disponible</p>'">`;
    body.innerHTML = `<div class="modal-header"><div class="card-title">${url.split('/').pop()}</div><button class="modal-close" onclick="Views.media.cerrarLightbox()">✕</button></div>${inner}<a href="${url}" target="_blank" class="btn btn-ghost mt-4">🔗 Abrir en pestaña</a>`;
    lb.classList.add('open');
  },
  cerrarLightbox: function(){ document.getElementById('media-lightbox').classList.remove('open'); }
};
