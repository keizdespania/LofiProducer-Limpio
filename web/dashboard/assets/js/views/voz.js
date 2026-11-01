// ═══ KEIZ OS · Voz Studio (Sherpa-ONNX) ═══
window.Views = window.Views || {};
window.Views.voz = {
  onEnter: function(){
    const v = document.getElementById('view-voz');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎙️ Voz Studio</h1><p class="text-muted mt-2">Sherpa-ONNX · 5 voces · 7 presets</p></div>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🗣 Voz</div></div>
        <select id="voz-voz" class="select">
          <option value="Davefx">Davefx</option>
          <option value="Sharvard">Sharvard</option>
          <option value="Claude">Claude</option>
          <option value="Lessac">Lessac</option>
          <option value="Ryan">Ryan</option>
        </select>
        <div class="grid-4 mt-4">
          ${['noticias','narracion_relajada','urgente','audiobook','publicidad','tutorial','sintesis_rapida'].map(p=>`<button class="btn btn-ghost btn-sm" onclick="document.getElementById('voz-preset').value='${p}';App.toast('Preset: ${p}','info',1000)">${p.replace('_',' ')}</button>`).join('')}
        </div>
        <input type="hidden" id="voz-preset" value="noticias">
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">✍️ Texto</div></div>
        <textarea id="voz-texto" class="textarea" placeholder="Escribe el texto a sintetizar..." rows="6"></textarea>
        <div class="flex gap-2 mt-2">
          <span class="text-sm text-muted" id="voz-count">0 caracteres</span>
        </div>
      </div>
      <div class="grid-2 mb-6">
        <div class="card">
          <div class="card-header"><div class="card-title">⚙️ Length scale</div></div>
          <input id="voz-length" class="input" type="number" value="1.1" min="0.5" max="2.0" step="0.05">
          <p class="text-sm text-muted mt-2">Natural: 1.1-1.25</p>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">🔊 Noise scale</div></div>
          <input id="voz-noise" class="input" type="number" value="0.667" min="0" max="1" step="0.01">
        </div>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🚀 Generar audio</div></div>
        <button class="btn btn-primary btn-lg" style="width:100%" onclick="Views.voz.generar()">🎙️ Generar voz</button>
        <div id="voz-status" class="mt-4"></div>
        <div id="voz-preview" class="mt-4"></div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">📜 Historial voces</div><button class="btn btn-ghost btn-sm" onclick="Views.voz.cargarHistorial()">Actualizar</button></div>
        <div id="voz-historial"></div>
      </div>
    `;
    document.getElementById('voz-texto').addEventListener('input', (e)=>{
      document.getElementById('voz-count').textContent = e.target.value.length + ' caracteres';
    });
    Views.voz.cargarHistorial();
  },
  generar: async function(){
    const texto = document.getElementById('voz-texto').value.trim();
    if(!texto){ App.toast('Escribe un texto','warning'); return; }
    const st = document.getElementById('voz-status');
    const prev = document.getElementById('voz-preview');
    st.innerHTML = '<div class="list-item"><span class="spinner"></span><span>Sintetizando voz...</span></div>';
    prev.innerHTML = '';
    try {
      const r = await App.api('/api/generar_voz',{method:'POST',body:{
        texto,
        voz: document.getElementById('voz-voz').value,
        preset: document.getElementById('voz-preset').value,
        length_scale: +document.getElementById('voz-length').value,
        noise_scale: +document.getElementById('voz-noise').value,
      }}).catch(async ()=>{
        // Fallback al endpoint viejo si /api/generar_voz no existe
        return await App.api('/api/voice_studio',{method:'POST',body:{texto,voz:document.getElementById('voz-voz').value}});
      });
      const url = r.url || r.path || r.audio || '';
      if(url){
        prev.innerHTML = `<div class="card" style="padding:12px"><audio controls src="${url}" style="width:100%"></audio><a href="${url}" target="_blank" class="btn btn-ghost btn-sm mt-2">🔗 Descargar</a></div>`;
        st.innerHTML = '<div class="list-item" style="border-left:3px solid var(--green)">✅ Voz generada</div>';
        App.toast('Voz lista 🎙️','success');
      } else {
        st.innerHTML = '<div class="list-item" style="border-left:3px solid var(--yellow)">⚠️ Sin URL de retorno</div>';
      }
    } catch(e){
      st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--red)">❌ ${e.message}</div>`;
    }
  },
  cargarHistorial: async function(){
    const el = document.getElementById('voz-historial');
    el.innerHTML = '<div class="skeleton" style="height:40px"></div>';
    try {
      const r = await App.api('/api/media?tipo=voz').catch(()=>({files:[]}));
      const files = (r.files||[]).slice(0,10);
      if(!files.length){ el.innerHTML = '<div class="empty-state"><p>Sin voces generadas</p></div>'; return; }
      el.innerHTML = files.map(f=>`
        <div class="list-item mb-2">
          <div style="flex:1">${f.name||f.filename}</div>
          <audio controls src="/media/${f.filename||f.name}" style="height:32px"></audio>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
