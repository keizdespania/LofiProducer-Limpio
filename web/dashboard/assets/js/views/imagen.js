// ═══ KEIZ OS · Imagen Studio (Cloudflare SDXL) ═══
window.Views = window.Views || {};
window.Views.imagen = {
  onEnter: function(){
    const v = document.getElementById('view-imagen');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎨 Imagen Studio</h1><p class="text-muted mt-2">Genera imágenes con Cloudflare SDXL</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.imagen.cargarGaleria()">🖼 Galería</button>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎨 Estilos</div></div>
        <div class="grid-4" id="img-presets">
          ${['cinematic','anime','realistic','product','portrait','landscape','abstract','cartoon'].map(p=>`<button class="btn btn-ghost" onclick="document.getElementById('img-style').value='${p}';App.toast('Estilo: ${p}','info',1000)">${p}</button>`).join('')}
        </div>
        <input type="hidden" id="img-style" value="cinematic">
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">✍️ Prompt</div></div>
        <textarea id="img-prompt" class="textarea" placeholder="Ej: neon city at night, cyberpunk, purple rain, cinematic lighting..." rows="3"></textarea>
        <p class="text-sm text-muted mt-2">⚠️ No incluir texto en el prompt (SDXL no lo genera bien)</p>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">📐 Aspecto</div></div>
        <div class="grid-4">
          <button class="btn btn-ghost" onclick="document.getElementById('img-aspect').value='16:9';App.toast('16:9','info',1000)">16:9</button>
          <button class="btn btn-ghost" onclick="document.getElementById('img-aspect').value='9:16';App.toast('9:16','info',1000)">9:16</button>
          <button class="btn btn-ghost" onclick="document.getElementById('img-aspect').value='1:1';App.toast('1:1','info',1000)">1:1</button>
          <button class="btn btn-ghost" onclick="document.getElementById('img-aspect').value='21:9';App.toast('21:9','info',1000)">21:9</button>
        </div>
        <input type="hidden" id="img-aspect" value="1:1">
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🚀 Generar</div></div>
        <div class="flex gap-2">
          <button class="btn btn-primary btn-lg" style="flex:1" onclick="Views.imagen.generar(1)">🎨 Generar</button>
          <button class="btn btn-ghost" onclick="Views.imagen.generar(4)">×4</button>
        </div>
        <div id="img-status" class="mt-4"></div>
        <div id="img-preview" class="grid-2 mt-4"></div>
      </div>
      <div class="card" id="img-galeria-card" style="display:none">
        <div class="card-header"><div class="card-title">🖼 Galería</div></div>
        <div id="img-galeria" class="grid-4"></div>
      </div>
    `;
  },
  generar: async function(n=1){
    const prompt = document.getElementById('img-prompt').value.trim();
    const aspect = document.getElementById('img-aspect').value;
    const style = document.getElementById('img-style').value;
    if(!prompt){ App.toast('Escribe un prompt','warning'); return; }
    const st = document.getElementById('img-status');
    const prev = document.getElementById('img-preview');
    st.innerHTML = `<div class="list-item"><span class="spinner"></span><span>Generando ${n} imagen(es)... (30-60s)</span></div>`;
    prev.innerHTML = '';
    for(let i=0;i<n;i++){
      try {
        const r = await App.api('/api/generar_imagen',{method:'POST',body:{prompt, aspect_ratio:aspect, style}});
        const url = r.url || r.path || r.imagen || '';
        if(url){
          prev.insertAdjacentHTML('beforeend', `
            <div class="card" style="padding:8px">
              <img src="${url}" style="width:100%;border-radius:8px" onerror="this.style.display='none'">
              <div class="flex gap-2 mt-2">
                <a href="${url}" target="_blank" class="btn btn-ghost btn-sm" style="flex:1;text-decoration:none;text-align:center">🔗 Abrir</a>
                <button class="btn btn-ghost btn-sm" onclick="navigator.clipboard.writeText('${url}').then(()=>App.toast('URL copiada','success'))">📋</button>
              </div>
            </div>
          `);
          App.toast(`Imagen ${i+1}/${n} lista`,'success',1500);
        }
      } catch(e){ prev.insertAdjacentHTML('beforeend', `<div class="card" style="border-left:3px solid var(--red);padding:12px"><p class="text-sm">Error: ${e.message}</p></div>`); }
    }
    st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--green)">✅ ${n} imagen(es) completada(s)</div>`;
  },
  cargarGaleria: async function(){
    document.getElementById('img-galeria-card').style.display = 'block';
    const el = document.getElementById('img-galeria');
    el.innerHTML = '<div class="skeleton" style="height:120px"></div>';
    try {
      const r = await App.api('/api/media?tipo=imagen').catch(()=>({files:[]}));
      const files = (r.files||[]).slice(0,20);
      if(!files.length){ el.innerHTML = '<div class="empty-state"><p>No hay imágenes</p></div>'; return; }
      el.innerHTML = files.map(f=>`
        <div class="card" style="padding:6px;cursor:pointer" onclick="window.open('/media/${f.filename||f.name}','_blank')">
          <img src="/media/${f.filename||f.name}" style="width:100%;border-radius:6px;aspect-ratio:1;object-fit:cover">
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
