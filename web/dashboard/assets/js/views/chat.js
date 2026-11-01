// ═══ KEIZ OS · Dios (copiloto) ═══
window.Views = window.Views || {};
window.Views.chat = {
  onEnter: function(){
    const v = document.getElementById('view-chat');
    if(v.dataset.ready) return;
    v.innerHTML = `
      <h1>🤖 Dios</h1>
      <p class="text-muted mt-2 mb-6">Tu copiloto del ecosistema</p>
      <div class="grid-2 mb-6">
        <div class="card" style="cursor:pointer" onclick="Views.chat.enviar('¿Cómo va el pipeline hoy?')">
          <div class="card-title">📊 Estado del día</div><p class="text-sm">Pregúntale cómo va la producción</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.chat.enviar('Audita el ecosistema y dime si algo falla')">
          <div class="card-title">🔍 Auditar sistema</div><p class="text-sm">Revisión completa con autoreparación</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.chat.enviar('¿Qué puedo producir ahora?')">
          <div class="card-title">💡 Ideas de producción</div><p class="text-sm">Dios sugiere qué crear</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.chat.enviar('Revisa los logs y dime qué errores hay')">
          <div class="card-title">🩺 Diagnosticar errores</div><p class="text-sm">Lee logs y propone soluciones</p>
        </div>
      </div>
      <div class="card" style="display:flex;flex-direction:column;min-height:50vh;">
        <div id="chat-msgs" style="flex:1;overflow-y:auto;margin-bottom:16px;display:flex;flex-direction:column;gap:12px;">
          <div class="list-item" style="background:rgba(59,130,246,0.1);border-color:var(--blue)"><div><strong>Dios:</strong> Hola, Arquitecto. ¿En qué te ayudo?</div></div>
        </div>
        <div class="flex gap-2">
          <input id="chat-input" class="input" placeholder="Escribe a Dios o usa el micrófono..." onkeydown="if(event.key==='Enter')Views.chat.enviar()">
          <button class="btn btn-ghost btn-icon" onclick="Jarvis.toggle()" title="Voz">🎙️</button>
          <button class="btn btn-primary" onclick="Views.chat.enviar()">Enviar →</button>
        </div>
      </div>
    `;
    v.dataset.ready = '1';
  },
  enviar: async function(texto){
    const input = document.getElementById('chat-input');
    const t = texto || (input && input.value.trim());
    if(!t) return;
    if(input) input.value = '';
    const msgs = document.getElementById('chat-msgs');
    msgs.insertAdjacentHTML('beforeend', `<div class="list-item" style="background:rgba(139,92,246,0.1);border-color:var(--purple)"><div><strong>Tú:</strong> ${t}</div></div>`);
    msgs.insertAdjacentHTML('beforeend', `<div class="list-item" id="chat-pending"><div><strong>Dios:</strong> <span class="spinner"></span></div></div>`);
    msgs.scrollTop = msgs.scrollHeight;
    try {
      const r = await App.api('/api/dios_hablar', { method:'POST', body:{ texto:t } });
      const respuesta = r.respuesta || r.msg || 'Sin respuesta';
      document.getElementById('chat-pending').remove();
      msgs.insertAdjacentHTML('beforeend', `<div class="list-item" style="background:rgba(59,130,246,0.1);border-color:var(--blue)"><div><strong>Dios:</strong> ${respuesta}</div></div>`);
      msgs.scrollTop = msgs.scrollHeight;
    } catch(e){
      document.getElementById('chat-pending').remove();
      msgs.insertAdjacentHTML('beforeend', `<div class="list-item" style="background:rgba(239,68,68,0.1);border-color:var(--red)"><div><strong>Error:</strong> ${e.message}</div></div>`);
    }
  }
};
