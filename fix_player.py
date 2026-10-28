"""Reescribe el reproductor de voz del chat (Play/Pausa + Barra) y arregla el auto-play."""
import pathlib, re

p = pathlib.Path("assets/app.js")
js = p.read_text()

# 1. Limpiar el _jarvisLog para que solo escriba en la consola azul, no flotante
patron_log = re.compile(r'function _jarvisLog\(msg\) \{.*?^\}', re.DOTALL | re.MULTILINE)
nuevo_log = """function _jarvisLog(msg) {
    console.log('[Jarvis]', msg);
    const consoleDiv = document.getElementById('log-console');
    if (consoleDiv) {
        const line = document.createElement('div');
        line.innerText = '> ' + msg;
        line.style.color = '#00ffcc';
        consoleDiv.appendChild(line);
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }
}"""
if patron_log.search(js):
    js = patron_log.sub(nuevo_log, js)

# 2. Reemplazar el bloque HTML de los 3 botones por el reproductor Pro
patron_html = re.compile(r'botMsg\.innerHTML = `<div style="background: rgba\(0,255,204,0\.1\);.*?</div>`;', re.DOTALL)

nuevo_html = '''const uid = 'audio_' + Math.random().toString(36).substr(2, 9);
        botMsg.innerHTML = `
            <div id="texto-${uid}" style="background: rgba(0,255,204,0.1); border-left: 3px solid #00ffcc; padding: 8px; border-radius: 4px; font-family: monospace; white-space: pre-wrap;">${respuesta}</div>
            <div style="display:flex; align-items:center; gap:10px; margin-top:8px; background:#111; padding:6px 12px; border-radius:20px; border:1px solid #333;">
                <button id="btn-${uid}" onclick="togglePlayTTS('${uid}')" style="background:#00ffcc; color:#000; border:none; border-radius:50%; width:34px; height:34px; cursor:pointer; font-size:16px; display:flex; align-items:center; justify-content:center;">▶️</button>
                <input type="range" id="slider-${uid}" min="0" max="100" value="0" style="flex:1; height:6px; accent-color:#00ffcc;" disabled>
                <span id="time-${uid}" style="color:#888; font-size:12px; min-width:36px; text-align:right; font-family:monospace;">0:00</span>
            </div>
        `;
        if (modoConversacion) {
            setTimeout(() => togglePlayTTS(uid), 500);
        }'''

if patron_html.search(js):
    js = patron_html.sub(nuevo_html, js)
    print("OK: HTML del reproductor actualizado (Play/Pausa + Slider)")
else:
    print("AVISO: No se encontro el bloque HTML de los botones viejos")

# 3. Reemplazar las funciones viejas (reproducirTexto, pausarTTS, detenerTTS) por el nuevo togglePlayTTS
# Buscamos desde 'let _utteranceActual' hasta el final de 'detenerTTS()'
patron_func = re.compile(r'// ═══ CONTROLES TTS ═══.*?^// ═══ FIN CONTROLES TTS ═══', re.DOTALL | re.MULTILINE)

nuevas_funciones = '''// ═══ CONTROLES TTS PRO ═══
let currentTTS = { utterance: null, btn: null, slider: null, timeLabel: null, interval: null, startTime: 0, duration: 0, isPaused: false };

function togglePlayTTS(uid) {
    const btn = document.getElementById(`btn-${uid}`);
    const slider = document.getElementById(`slider-${uid}`);
    const timeLabel = document.getElementById(`time-${uid}`);
    const textoDiv = document.getElementById(`texto-${uid}`);
    const texto = textoDiv ? textoDiv.innerText : '';

    if (!('speechSynthesis' in window)) return alert("Tu navegador no soporta TTS.");

    // Si es el mismo audio que estaba sonando
    if (currentTTS.utterance && currentTTS.btn === btn) {
        if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
            btn.innerText = '⏸️';
            currentTTS.isPaused = false;
            startTTSInterval();
        } else if (window.speechSynthesis.speaking) {
            window.speechSynthesis.pause();
            btn.innerText = '▶️';
            currentTTS.isPaused = true;
            clearInterval(currentTTS.interval);
        }
        return;
    }

    // Nuevo audio: parar el anterior si existe
    window.speechSynthesis.cancel();
    clearInterval(currentTTS.interval);
    
    const cleanText = texto.replace(/<[^>]*>?/gm, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'es-ES';
    utterance.rate = 1.1;
    
    const voices = window.speechSynthesis.getVoices();
    const esVoice = voices.find(v => v.lang.startsWith('es'));
    if (esVoice) utterance.voice = esVoice;

    // Estimacion de duracion (aprox 150 palabras por minuto)
    const words = cleanText.split(/\\s+/).length;
    const durationEst = (words / 150) * 60;

    currentTTS = { utterance, btn, slider, timeLabel, interval: null, startTime: 0, duration: durationEst, isPaused: false };

    utterance.onstart = () => {
        btn.innerText = '⏸️';
        currentTTS.startTime = Date.now();
        startTTSInterval();
    };

    utterance.onend = () => {
        btn.innerText = '▶️';
        clearInterval(currentTTS.interval);
        slider.value = 100;
        timeLabel.innerText = formatTime(durationEst);
        currentTTS.utterance = null;
        if (modoConversacion) {
            setTimeout(iniciarEscuchaConversacion, 500);
        }
    };

    utterance.onerror = () => {
        btn.innerText = '▶️';
        clearInterval(currentTTS.interval);
    };

    window.speechSynthesis.speak(utterance);
}

function startTTSInterval() {
    clearInterval(currentTTS.interval);
    currentTTS.interval = setInterval(() => {
        if (!window.speechSynthesis.speaking || window.speechSynthesis.paused) return;
        const el = (Date.now() - currentTTS.startTime) / 1000;
        const percent = Math.min((el / currentTTS.duration) * 100, 99);
        currentTTS.slider.value = percent;
        currentTTS.timeLabel.innerText = formatTime(el);
    }, 250);
}

function formatTime(secs) {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return m + ':' + s.toString().padStart(2, '0');
}
// ═══ FIN CONTROLES TTS PRO ═══'''

if patron_func.search(js):
    js = patron_func.sub(nuevas_funciones, js)
    print("OK: Funciones de audio actualizadas (togglePlay, progreso, tiempo)")
else:
    print("AVISO: No se encontraron las funciones viejas (puede que ya estuvieran borradas)")
    # Si no hay marca, las añadimos al final
    js += "\n" + nuevas_funciones

p.write_text(js)
print("OK: app.js actualizado")
