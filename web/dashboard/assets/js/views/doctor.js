// ═══ KEIZ OS · Doctor (diagnóstico + autoreparación) ═══
window.Views = window.Views || {};
window.Views.doctor = {
  onEnter: function(){
    const v = document.getElementById('view-doctor');
    v.innerHTML = `
      <h1>🩺 Doctor</h1>
      <p class="text-muted mt-2 mb-6">Diagnóstico del ecosistema + autoreparación</p>
      <div class="grid-2 mb-6">
        <div class="card" style="cursor:pointer" onclick="Views.doctor.diagnosticar()">
          <div style="font-size:2em">🩺</div>
          <div class="card-title mt-2">Diagnosticar</div>
          <p class="text-sm">Escanea Flask, OmniRoute, worker, cron</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.doctor.auditar()">
          <div style="font-size:2em">🔍</div>
          <div class="card-title mt-2">Auditar con Dios</div>
          <p class="text-sm">Revisión completa del ecosistema</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.doctor.conserje()">
          <div style="font-size:2em">🧹</div>
          <div class="card-title mt-2">Conserje</div>
          <p class="text-sm">Limpieza de archivos temporales</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.doctor.sanar()">
          <div style="font-size:2em">💊</div>
          <div class="card-title mt-2">Sanar</div>
          <p class="text-sm">Autoreparación de módulos</p>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">📜 Log de diagnóstico</div><button class="btn btn-ghost btn-sm" onclick="document.getElementById('doc-log').textContent=''">Limpiar</button></div>
        <pre id="doc-log" style="max-height:500px;overflow:auto;background:rgba(0,0,0,0.3);padding:12px;border-radius:8px;font-family:var(--mono);font-size:0.85em;color:var(--muted);white-space:pre-wrap"></pre>
      </div>
    `;
  },
  log: function(msg){ const el = document.getElementById('doc-log'); el.textContent += '['+new Date().toLocaleTimeString()+'] '+msg+'\n'; el.scrollTop = el.scrollHeight; },
  diagnosticar: async function(){
    Views.doctor.log('🩺 Ejecutando diagnóstico...');
    try { const r = await App.api('/api/doctor',{method:'POST'}); Views.doctor.log(JSON.stringify(r,null,2)); App.toast('Diagnóstico OK','success'); } catch(e){ Views.doctor.log('❌ '+e.message); }
  },
  auditar: async function(){
    Views.doctor.log('🔍 Auditando...');
    try { const r = await App.api('/api/auditar_dios',{method:'POST'}); Views.doctor.log(JSON.stringify(r,null,2)); App.toast('Auditoría OK','success'); } catch(e){ Views.doctor.log('❌ '+e.message); }
  },
  conserje: async function(){
    Views.doctor.log('🧹 Ejecutando conserje...');
    try { const r = await App.api('/api/conserje',{method:'POST'}); Views.doctor.log(JSON.stringify(r,null,2)); App.toast('Limpieza OK','success'); } catch(e){ Views.doctor.log('❌ '+e.message); }
  },
  sanar: async function(){
    Views.doctor.log('💊 Sanando ecosistema...');
    App.toast('Sanador en desarrollo (backend pendiente)','info');
  }
};
