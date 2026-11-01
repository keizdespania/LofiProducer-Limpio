// ═══ KEIZ OS · Vídeo Studio (Wan 2.2 + Ensamblado FFmpeg) ═══
window.Views = window.Views || {};
window.Views.video = {
  onEnter: function(){
    const v = document.getElementById('view-video');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🎬 Vídeo Studio</h1><p class="text-muted mt-2">Wan 2.2 · 6 presets · resolución múltiplo 32</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.video.cargarTareas()">🔄 Tareas</button>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎬 Presets</div></div>
        <div class="grid-3" id="vid-presets">
          ${['cinematic','anime','realistic','abstract','product','landscape'].map(p=>`<button class="btn btn-ghost" onclick="document.getElementById('vid-preset').value='${p}';App.toast('Preset: ${p}','info',1000)">${p}</button>`).join('')}
        </div>
        <input type="hidden" id="vid-preset" value="cinematic">
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">✍️ Prompt</div></div>
        <textarea id="vid-prompt" class="textarea" placeholder="Sujeto + Movimiento + Cámara + Iluminación. Ej: A woman dancing slowly, camera rotates around, warm golden hour light..." rows="4"></textarea>
      </div>
      <div class="grid-2 mb-6">
        <div class="card">
          <div class="card-header"><div class="card-title">📐 Resolución</div></div>
          <select id="vid-res" class="select">
            <option value="480p">480p (rápido, seguro T4)</option>
            <option value="576p">576p</option>
            <option value="720p" disabled>720p (requiere Kaggle)</option>
          </select>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">🎞 Frames</div></div>
          <input id="vid-frames" class="input" type="number" value="49" min="8" max="121" step="4">
          <p class="text-sm text-muted mt-2">Fórmula: 4n+1</p>
        </div>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🚀 Generar vídeo</div></div>
        <button class="btn btn-primary btn-lg" style="width:100%" onclick="Views.video.generar()">🎬 Generar</button>
        <div id="vid-status" class="mt-4"></div>
        <div id="vid-preview" class="mt-4"></div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">📋 Tareas recientes</div></div>
        <div id="vid-tareas"></div>
      </div>
    `;
    Views.video.cargarTareas();
  },
  generar: async function(){
    const prompt = document.getElementById('vid-prompt').value.trim();
    if(!prompt){ App.toast('Escribe un prompt','warning'); return; }
    const st = document.getElementById('vid-status');
    st.innerHTML = '<div class="list-item"><span class="spinner"></span><span>Enviando a cola... (Wan 2.2 tarda 2-5 min)</span></div>';
    try {
      const r = await App.api('/api/generar_video',{method:'POST',body:{
        prompt,
        preset: document.getElementById('vid-preset').value,
        resolucion: document.getElementById('vid-res').value,
        num_frames: +document.getElementById('vid-frames').value,
      }});
      const taskId = r.task_id || r.id;
      if(taskId){
        st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--blue)">📋 Tarea ${taskId} en cola. Polling cada 5s...</div>`;
        Views.video.polling(taskId);
      } else {
        st.innerHTML = '<div class="list-item" style="border-left:3px solid var(--yellow)">⚠️ Sin task_id</div>';
      }
    } catch(e){ st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--red)">❌ ${e.message}</div>`; }
  },
  polling: function(taskId){
    const st = document.getElementById('vid-status');
    const prev = document.getElementById('vid-preview');
    let intentos = 0;
    const iv = setInterval(async ()=>{
      intentos++;
      if(intentos > 60){ clearInterval(iv); st.innerHTML = '<div class="list-item" style="border-left:3px solid var(--yellow)">⏱ Timeout (5min)</div>'; return; }
      try {
        const r = await App.api('/api/estado_video/'+taskId);
        if(r.estado === 'completado' || r.estado === 'done'){
          clearInterval(iv);
          st.innerHTML = '<div class="list-item" style="border-left:3px solid var(--green)">✅ Vídeo completado</div>';
          const url = r.url || r.path || '';
          if(url) prev.innerHTML = `<div class="card" style="padding:8px"><video controls src="${url}" style="width:100%;border-radius:8px"></video><a href="${url}" target="_blank" class="btn btn-ghost btn-sm mt-2">🔗 Abrir</a></div>`;
          App.toast('Vídeo listo 🎬','success');
          Views.video.cargarTareas();
        } else if(r.estado === 'error'){
          clearInterval(iv);
          st.innerHTML = `<div class="list-item" style="border-left:3px solid var(--red)">❌ Error: ${r.mensaje||'desconocido'}</div>`;
        } else {
          st.innerHTML = `<div class="list-item"><span class="spinner"></span><span>${r.estado||'procesando'}... (${intentos*5}s)</span></div>`;
        }
      } catch(e){}
    }, 5000);
  },
  cargarTareas: async function(){
    const el = document.getElementById('vid-tareas');
    el.innerHTML = '<div class="skeleton" style="height:40px"></div>';
    try {
      const r = await App.api('/api/tareas_video').catch(()=>({tareas:[]}));
      const t = (r.tareas||[]).slice(0,10);
      if(!t.length){ el.innerHTML = '<div class="empty-state"><p>Sin tareas</p></div>'; return; }
      el.innerHTML = t.map(x=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">${x.prompt||x.id}</div><div class="text-sm text-muted">${x.estado} · ${new Date(x.creada||Date.now()).toLocaleString()}</div></div>
          <span class="badge badge-${x.estado==='completado'?'green':x.estado==='error'?'red':'blue'}">${x.estado}</span>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
