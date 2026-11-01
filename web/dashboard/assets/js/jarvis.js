// ═══ KEIZ OS · Jarvis Infinity ═══
window.Jarvis = (function(){
  let activo = false, recognition = null;

  function detectarIntencion(texto){
    const t = texto.toLowerCase().trim();
    const reglas = [
      { match: /(lanza|lanzar|ejecuta|corre|inicia).*(pipeline|producci[oó]n)/, tool:'run_pipeline', params:{} },
      { match: /(produce|producir).*(ia_news|encuadre|keiz|lofi|finanzas|boe)/, tool:'producir_nicho', params:(m)=>({nicho:m[1]}) },
      { match: /(investiga|busca|tendencias).*(ia_news|encuadre|keiz|lofi|finanzas|boe)/, tool:'investigar', params:(m)=>({nicho:m[1]}) },
      { match: /(genera|crea|haz|pon).*(m[uú]sica|cancion|canci[oó]n|beat)/, tool:'generar_musica', params:()=>({prompt:texto, duration:60, preset:'lofi'}) },
      { match: /(genera|crea|haz|dibuja).*(imagen|foto)/, tool:'generar_imagen', params:()=>({prompt:texto, aspect_ratio:'1:1', style:'cinematic'}) },
      { match: /(genera|crea|haz).*(v[ií]deo|clip)/, tool:'generar_video', params:()=>({prompt:texto, preset:'cinematic', resolucion:'480p'}) },
      { match: /(escribe|redacta|crea).*(post|blog|art[ií]culo|noticia).*?(?:sobre|de)\s+(.+)/i, tool:'crear_post_blog', params:(m)=>({tema:m[1]||texto}) },
      { match: /(diagn[oó]stico|doctor|revisa sistema)/, tool:'doctor', params:{} },
      { match: /(audita|auditor[ií]a|revisa todo)/, tool:'auditar_dios', params:{} },
      { match: /(limpia|conserje)/, tool:'conserje', params:{} },
      { match: /(canales|nichos)/, tool:'ver_canales', params:{} },
      { match: /(cola|tareas|pendientes)/, tool:'ver_cola', params:{} },
      { match: /(media|vault|archivos)/, tool:'ver_media', params:{} },
      { match: /(analytics|m[eé]tricas|estad[ií]sticas)/, tool:'ver_analytics', params:{} },
      { match: /(borradores|blogs pendientes)/, tool:'ver_borradores', params:{} },
      { match: /(worker|log)/, tool:'ver_worker_log', params:{} },
      { match: /(informes)/, tool:'ver_informes', params:{} },
    ];
    for(const r of reglas){
      const m = t.match(r.match);
      if(m) return { tool: r.tool, params: typeof r.params === 'function' ? r.params(m) : r.params };
    }
    return null;
  }

  async function ejecutar(tool, params){
    App.toast(`⚡ Jarvis: ${tool}...`, 'info', 2000);
    try {
      const r = await App.api('/api/jarvis/execute', { method:'POST', body:{ tool, params } });
      if(r.status === 'ok'){
        const res = r.result || {};
        let resumen = '';
        if(res.result) resumen = JSON.stringify(res.result).substring(0, 200);
        else if(res.reporte) resumen = res.reporte.substring(0, 200);
        else if(Array.isArray(res)) resumen = `${res.length} items`;
        else resumen = JSON.stringify(res).substring(0, 200);
        App.toast(`✅ ${tool}: ${resumen}`, 'success', 6000);
        console.log('[Jarvis]', tool, r);
        return r;
      }
    } catch(e){ App.toast(`❌ Jarvis: ${e.message}`, 'error', 5000); }
  }

  async function procesar(texto){
    const intencion = detectarIntencion(texto);
    if(intencion){
      App.toast(`🎯 Detectado: ${intencion.tool}`, 'success', 1500);
      return await ejecutar(intencion.tool, intencion.params);
    }
    try {
      const r = await App.api('/api/dios_hablar', { method:'POST', body:{ texto } });
      const resp = r.respuesta || r.msg || 'Sin respuesta';
      App.toast('Dios: ' + resp.substring(0, 150), 'info', 6000);
      if('speechSynthesis' in window && resp){
        const u = new SpeechSynthesisUtterance(resp); u.lang='es-ES'; u.rate=1.1; speechSynthesis.speak(u);
      }
      return r;
    } catch(e){ App.toast('❌ ' + e.message, 'error'); }
  }

  function toggle(){
    const fab = document.getElementById('jarvis-fab');
    if(activo){ detener(); return; }
    activo = true; fab.classList.add('active'); fab.textContent = '🔴';
    App.toast('🎙️ Jarvis escuchando...', 'info', 2000);
    if(!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)){
      App.toast('Voz no soportada, abre el chat', 'warning', 3000);
      location.hash='chat'; App.route(); detener(); return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = 'es-ES'; recognition.continuous = false; recognition.interimResults = false;
    recognition.onresult = async e => {
      const texto = e.results[0][0].transcript;
      App.toast('Tú: ' + texto, 'info', 3000);
      await procesar(texto); detener();
    };
    recognition.onerror = (ev) => { App.toast('Jarvis: ' + (ev.error||'error'), 'warning'); detener(); };
    recognition.onend = () => { if(activo) detener(); };
    recognition.start();
  }

  function detener(){
    activo = false;
    const fab = document.getElementById('jarvis-fab');
    if(fab){ fab.classList.remove('active'); fab.textContent = '🤖'; }
    if(recognition){ try { recognition.stop(); } catch(e){} recognition = null; }
  }

  function init(){ console.log('[Jarvis Infinity] ready · 20 tools'); }
  return { init, toggle, detener, procesar, ejecutar, detectarIntencion };
})();
