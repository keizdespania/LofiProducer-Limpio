// ═══ KEIZ OS · Música Studio (ACE-Step) ═══
window.Views = window.Views || {};
window.Views.musica = {
  onEnter: async function(){
    const v = document.getElementById('view-musica');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎵 Música Studio</h1><p class="text-muted mt-2">Genera música con ACE-Step v11</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.musica.cargarHistorial()">📜 Historial</button>
      </div>

      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎼 Prompts rápidos</div></div>
        <div class="grid-3" id="mus-presets"><div class="skeleton" style="height:60px"></div><div class="skeleton" style="height:60px"></div><div class="skeleton" style="height:60px"></div></div>
      </div>

      <div class="card mb-6">
        <div class="card-header"><div class="card-title">✍️ Prompt</div></div>
        <textarea id="mus-prompt" class="textarea" placeholder="Ej: lofi chill beat, piano suave, vinilo, 80 bpm..." rows="3"></textarea>
        <div class="flex gap-2 mt-4">
          <button class="btn btn-ghost btn-sm" onclick="document.getElementById('mus-prompt').value='';App.toast('Prompt limpiado','info',1000)">🗑 Limpiar</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.musica.mejorar()">💡 Mejorar prompt</button>
        </div>
      </div>

      <div class="grid-2 mb-6">
        <div class="card">
          <div class="card-header"><div class="card-title">🎛 Preset</div></div>
          <select id="mus-preset" class="select">
            <option value="lofi">Lofi chill</option>
            <option value="cinematic">Cinematic</option>
            <option value="electronic">Electronic</option>
            <option value="orchestral">Orchestral</option>
            <option value="ambient">Ambient</option>
          </select>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">⏱ Duración</div></div>
          <div class="flex gap-2">
            <button class="btn btn-ghost" onclick="document.getElementById('mus-dur').value=30">30s</button>
            <button class="btn btn-ghost" onclick="document.getElementById('mus-dur').value=60">60s</button>
            <button class="btn btn-ghost" onclick="document.getElementById('mus-dur').value=180">3min</button>
          </div>
          <input id="mus-dur" class="input mt-2" type="number" value="60" min="10" max="300">
        </div>
      </div>

      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🚀 Generación</div></div>
        <div class="flex gap-2 mb-4">
          <button class="btn btn-primary btn-lg" style="flex:1" onclick="Views.musica.generar(1)">🎵 Generar</button>
          <button class="btn btn-ghost" onclick="Views.musica.generar(5)" title="Batch: 5 variaciones">×5</button>
        </div>
        <div id="mus-status"></div>
      </div>

      <div class="card" id="mus-historial-card" style="display:none">
        <div class="card-header"><div class="card-title">📜 Historial</div></div>
        <div id="mus-historial"></div>
      </div>
    `;
    Views.musica.cargarPresets();
  },

  cargarPresets: async function(){
    try {
      const r = await App.api('/api/user_presets/musica').catch(()=>({presets:{}}));
      const presets = r.presets || {};
      const el = document.getElementById('mus-presets');
      const defaults = [
        {name:'Lofi chill', prompt:'lofi chill beat, piano suave, vinilo, 80 bpm'},
        {name:'Cinematic', prompt:'cinematic orchestral, tension, epic drums'},
        {name:'Ambient', prompt:'ambient pads, ethereal, slow evolving'},
      ];
      const all = [...defaults, ...Object.entries(presets).map(([k,v])=>({name:k, prompt:v.prompt||v}))];
      el.innerHTML = all.slice(0,6).map(p=>`
        <div class="card" style="cursor:pointer;padding:12px" onclick="document.getElementById('mus-prompt').value=${JSON.stringify(p.prompt)}">
          <div style="font-weight:600;margin-bottom:4px">🎵 ${p.name}</div>
          <div class="text-sm text-muted truncate">${p.prompt}</div>
        </div>
      `).join('');
    } catch(e){}
  },

  mejorar: async function(){
    const p = document.getElementById('mus-prompt').value;
    if(!p){ App.toast('Escribe un prompt primero','warning'); return; }
    try {
      const r = await App.api('/api/prompt',{method:'POST',body:{tipo:'musica',idea:p}});
      if(r.prompt){ document.getElementById('mus-prompt').value = r.prompt; App.toast('Prompt mejorado','success'); }
    } catch(e){}
  },

  generar: async function(n=1){
    const prompt = document.getElementById('mus-prompt').value.trim();
    const dur = +document.getElementById('mus-dur').value;
    if(!prompt){ App.toast('Escribe un prompt','warning'); return; }
    const st = document.getElementById('mus-status');
    st.innerHTML = `<div class="list-item"><span class="spinner"></span><span>Generando ${n} pista(s) de ${dur}s... (2-3 min)</span></div>`;
    try {
      for(let i=0;i<n;i++){
        await App.api('/api/generar_musica_acestep',{method:'POST',body:{prompt, duration:dur, preset:document.getElementById('mus-preset').value}});
        st.innerHTML += `<div class="list-item mt-2" style="border-left:3px solid var(--green)"><div>✅ Pista ${i+1}/${n} completada</div></div>`;
      }
      App.toast(`${n} pista(s) generada(s) 🎵`,'success');
      setTimeout(()=>Views.musica.cargarHistorial(), 1000);
    } catch(e){
      st.innerHTML += `<div class="list-item mt-2" style="border-left:3px solid var(--red)"><div>❌ Error: ${e.message}</div></div>`;
    }
  },

  cargarHistorial: async function(){
    document.getElementById('mus-historial-card').style.display = 'block';
    const el = document.getElementById('mus-historial');
    el.innerHTML = '<div class="skeleton" style="height:40px"></div>';
    try {
      const r = await App.api('/api/media?tipo=musica').catch(()=>({files:[]}));
      const files = (r.files||[]).slice(0,20);
      if(!files.length){ el.innerHTML = '<div class="empty-state"><p>Aún no hay música generada</p></div>'; return; }
      el.innerHTML = files.map(f=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">${f.name || f.filename}</div><div class="text-sm text-muted">${(f.size/1048576).toFixed(1)} MB</div></div>
          <audio controls src="/media/${f.filename||f.name}" style="height:32px"></audio>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
