// ═══ KEIZ OS · Dios (Jarvis Infinity copiloto) ═══
window.Views = window.Views || {};
window.Views.chat = {
  historial: [],
  onEnter: function(){
    const v = document.getElementById('view-chat');
    // Cargar historial persistente
    if(!Views.chat.historial.length){
      try { Views.chat.historial = JSON.parse(localStorage.getItem('jarvis_hist')||'[]'); } catch(e){}
    }
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🤖 Dios · Jarvis Infinity</h1><p class="text-muted mt-2">20 tools · 17 intenciones · voz continua</p></div>
        <button class="btn btn-ghost btn-sm" onclick="Views.chat.limpiar()">🗑 Limpiar</button>
      </div>

      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎯 Prueba rápido</div></div>
        <div class="grid-3">
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('diagnóstico del sistema')">🩺 Diagnóstico</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('ver canales')">📺 Canales</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('ver cola')">📋 Cola</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('genera música lofi chill')">🎵 Música</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('genera imagen neón cyberpunk')">🎨 Imagen</button>
          <button class="btn btn-ghost btn-sm" onclick="Views.chat.ejecutar('investiga tendencias ia_news')">🕵️ Investigar</button>
        </div>
      </div>

      <div class="card" style="display:flex;flex-direction:column;min-height:55vh;max-height:70vh;">
        <div id="chat-msgs" style="flex:1;overflow-y:auto;margin-bottom:16px;display:flex;flex-direction:column;gap:12px;">
          ${Views.chat.historial.length ? '' : '<div class="list-item" style="background:rgba(59,130,246,0.1);border-color:var(--blue)"><div><strong>🤖 Jarvis:</strong> Hola Arquitecto. Puedo generar música, imágenes, vídeos, producir nichos, lanzar pipeline, diagnosticar, ver canales, cola, media... Dime qué necesitas.</div></div>'}
        </div>
        <div class="flex gap-2">
          <input id="chat-input" class="input" placeholder="Ej: genera música lofi chill · ver canales · lanza pipeline..." onkeydown="if(event.key==='Enter')Views.chat.ejecutar()">
          <button class="btn btn-ghost btn-icon" onclick="Jarvis.toggle()" title="Voz">🎙️</button>
          <button class="btn btn-primary" onclick="Views.chat.ejecutar()">Enviar →</button>
        </div>
      </div>
    `;
    Views.chat.renderHistorial();
  },

  renderHistorial: function(){
    const msgs = document.getElementById('chat-msgs');
    if(!msgs) return;
    Views.chat.historial.forEach(m => Views.chat.burbuja(m.rol, m.texto, m.tool));
    msgs.scrollTop = msgs.scrollHeight;
  },

  burbuja: function(rol, texto, tool){
    const msgs = document.getElementById('chat-msgs');
    if(!msgs) return;
    const bg = rol === 'user' ? 'rgba(139,92,246,0.1)' : 'rgba(59,130,246,0.1)';
    const border = rol === 'user' ? 'var(--purple)' : 'var(--blue)';
    const icono = rol === 'user' ? '👤' : tool ? '⚡' : '🤖';
    const toolBadge = tool ? `<span class="badge badge-purple" style="margin-left:8px">${tool}</span>` : '';
    msgs.insertAdjacentHTML('beforeend', `
      <div class="list-item" style="background:${bg};border-color:${border}">
        <div style="flex:1"><strong>${icono} ${rol==='user'?'Tú':'Jarvis'}:</strong>${toolBadge} ${texto}</div>
      </div>
    `);
    msgs.scrollTop = msgs.scrollHeight;
  },

  guardar: function(rol, texto, tool){
    Views.chat.historial.push({ rol, texto, tool, ts: Date.now() });
    if(Views.chat.historial.length > 100) Views.chat.historial = Views.chat.historial.slice(-100);
    localStorage.setItem('jarvis_hist', JSON.stringify(Views.chat.historial));
  },

  limpiar: function(){
    if(!confirm('¿Limpiar historial?')) return;
    Views.chat.historial = [];
    localStorage.removeItem('jarvis_hist');
    document.getElementById('chat-msgs').innerHTML = '';
    App.toast('Historial limpiado','success');
  },

  ejecutar: async function(textoDirecto){
    const input = document.getElementById('chat-input');
    const texto = textoDirecto || (input && input.value.trim());
    if(!texto) return;
    if(input) input.value = '';
    Views.chat.burbuja('user', texto); Views.chat.guardar('user', texto);

    const intencion = Jarvis.detectarIntencion(texto);
    if(intencion){
      Views.chat.burbuja('system', `⚡ Ejecutando: <strong>${intencion.tool}</strong>...`, intencion.tool);
      try {
        const r = await App.api('/api/jarvis/execute', { method:'POST', body:{ tool:intencion.tool, params:intencion.params } });
        const res = r.result || {};
        let display = '';
        if(res.reporte) display = res.reporte.substring(0, 500);
        else if(res.result) display = JSON.stringify(res.result, null, 2).substring(0, 500);
        else if(Array.isArray(res)) display = `${res.length} items: ` + JSON.stringify(res.slice(0,3));
        else display = JSON.stringify(res, null, 2).substring(0, 500);
        Views.chat.burbuja('assistant', display, intencion.tool);
        Views.chat.guardar('assistant', display, intencion.tool);
      } catch(e){
        Views.chat.burbuja('assistant', '❌ Error: ' + e.message);
      }
    } else {
      // Fallback a Dios
      const pend = '⏳ Pensando...';
      Views.chat.burbuja('assistant', pend);
      try {
        const r = await App.api('/api/dios_hablar', { method:'POST', body:{ texto } });
        const resp = r.respuesta || r.msg || 'Sin respuesta';
        const msgs = document.getElementById('chat-msgs');
        msgs.lastElementChild.remove();
        Views.chat.burbuja('assistant', resp.substring(0, 800));
        Views.chat.guardar('assistant', resp.substring(0, 800));
        if('speechSynthesis' in window){
          const u = new SpeechSynthesisUtterance(resp.substring(0,300)); u.lang='es-ES'; speechSynthesis.speak(u);
        }
      } catch(e){
        const msgs = document.getElementById('chat-msgs');
        msgs.lastElementChild.remove();
        Views.chat.burbuja('assistant', '❌ ' + e.message);
      }
    }
  }
};
