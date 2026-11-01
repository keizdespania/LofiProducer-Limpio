// ═══ KEIZ OS · Jarvis (botón flotante Dios) ═══
window.Jarvis = (function(){
  let activo = false, recognition = null;
  function toggle(){
    const fab = document.getElementById('jarvis-fab');
    if(!activo){
      activo = true; fab.classList.add('active'); fab.textContent = '🔴';
      App.toast('Jarvis escuchando... (voz)', 'info', 2000);
      if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR(); recognition.lang = 'es-ES'; recognition.continuous = false; recognition.interimResults = false;
        recognition.onresult = async e => {
          const texto = e.results[0][0].transcript;
          App.toast('Tú: ' + texto, 'info', 3000);
          try {
            const r = await App.api('/api/dios_hablar', { method:'POST', body:{ texto } });
            const respuesta = r.respuesta || r.msg || 'Sin respuesta';
            App.toast('Dios: ' + respuesta.substring(0, 100), 'success', 5000);
            if('speechSynthesis' in window){
              const u = new SpeechSynthesisUtterance(respuesta); u.lang='es-ES'; speechSynthesis.speak(u);
            }
          } catch(e){ App.toast('Error hablando con Dios','error'); }
          detener();
        };
        recognition.onerror = () => { App.toast('Jarvis: no te oí','warning'); detener(); };
        recognition.onend = () => { if(activo) detener(); };
        recognition.start();
      } else {
        location.hash='chat'; App.route(); detener();
      }
    } else { detener(); }
  }
  function detener(){
    activo = false;
    const fab = document.getElementById('jarvis-fab');
    if(fab){ fab.classList.remove('active'); fab.textContent = '🤖'; }
    if(recognition){ try { recognition.stop(); } catch(e){} recognition = null; }
  }
  function init(){ }
  return { init, toggle, detener };
})();
