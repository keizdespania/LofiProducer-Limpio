// ═══ KEIZ OS · Ajustes ═══
window.Views = window.Views || {};
window.Views.ajustes = {
  onEnter: function(){
    const v = document.getElementById('view-ajustes');
    v.innerHTML = `
      <h1>⚙️ Ajustes</h1>
      <p class="text-muted mt-2 mb-6">APIs, tema, voz del Dios</p>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎨 Tema</div></div>
        <div class="flex gap-2">
          <button class="btn btn-ghost" onclick="document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('keiz_theme','dark')">🌙 Oscuro</button>
          <button class="btn btn-ghost" onclick="document.documentElement.setAttribute('data-theme','light');localStorage.setItem('keiz_theme','light')">☀️ Claro</button>
        </div>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🔑 APIs</div></div>
        ${['youtube','pixabay','kaggle','groq','cloudflare'].map(a=>`<div class="list-item mb-2"><span>${a}</span><button class="btn btn-ghost btn-sm" onclick="App.toast('Editor API ${a} (en desarrollo)','info')">⚙️ Configurar</button></div>`).join('')}
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">🎙️ Voz de Dios</div></div>
        <select id="aj-voz" class="select mb-2">
          <option value="es-ES-AlvaroNeural">Álvaro (España)</option>
          <option value="es-MX-DaliaNeural">Dalia (México)</option>
        </select>
        <button class="btn btn-ghost" onclick="App.toast('Voz guardada','success')">💾 Guardar</button>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">🧹 Sistema</div></div>
        <div class="flex gap-2" style="flex-wrap:wrap">
          <button class="btn btn-ghost" onclick="Views.ajustes.limpiarHistorial()">🗑 Limpiar historial chat</button>
          <button class="btn btn-ghost" onclick="location.reload(true)">🔄 Hard reload</button>
          <button class="btn btn-danger" onclick="if(confirm('¿Cerrar sesión?'))location.reload()">🚪 Salir</button>
        </div>
      </div>
    `;
  },
  limpiarHistorial: async function(){
    if(!confirm('¿Limpiar todo el historial de chat?')) return;
    try { await App.api('/api/borrar_historial',{method:'POST'}); localStorage.removeItem('chat_history'); App.toast('Historial limpio','success'); } catch(e){}
  }
};
