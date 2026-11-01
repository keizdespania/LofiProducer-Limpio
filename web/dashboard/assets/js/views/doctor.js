// ═══ KEIZ OS · Doctor ═══
window.Views = window.Views || {};
window.Views.doctor = {
  onEnter: function(){
    const v = document.getElementById('view-doctor');
    v.innerHTML = `
      <h1>🩺 Doctor</h1>
      <p class="text-muted mt-2 mb-6">Diagnóstico + autoreparación</p>
      <div class="grid-2 mb-6">
        <div class="card" style="cursor:pointer" onclick="Views.doctor.accion('doctor','🩺 Diagnóstico')">
          <div style="font-size:2em">🩺</div><div class="card-title mt-2">Diagnóstico</div><p class="text-sm">Escanea el sistema</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.doctor.accion('auditar_dios','🔍 Auditoría Dios')">
          <div style="font-size:2em">🔍</div><div class="card-title mt-2">Auditar con Dios</div><p class="text-sm">Revisión profunda</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="Views.doctor.accion('conserje','🧹 Conserje')">
          <div style="font-size:2em">🧹</div><div class="card-title mt-2">Conserje</div><p class="text-sm">Limpieza de temporales</p>
        </div>
        <div class="card" style="cursor:pointer" onclick="location.reload()">
          <div style="font-size:2em">🔄</div><div class="card-title mt-2">Recargar dashboard</div><p class="text-sm">Hard reload</p>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">📜 Log</div><button class="btn btn-ghost btn-sm" onclick="document.getElementById('doc-log').textContent=''">Limpiar</button></div>
        <pre id="doc-log" style="max-height:500px;overflow:auto;background:rgba(0,0,0,0.3);padding:12px;border-radius:8px;font-family:var(--mono);font-size:0.85em;color:var(--muted);white-space:pre-wrap"></pre>
      </div>
    `;
  },
  log: function(m){ const el = document.getElementById('doc-log'); el.textContent += '['+new Date().toLocaleTimeString()+'] '+m+'\n'; el.scrollTop = el.scrollHeight; },
  accion: async function(ep, titulo){
    Views.doctor.log(titulo+' ejecutando...');
    try {
      const r = await App.api('/api/'+ep, {method:'POST'});
      Views.doctor.log(JSON.stringify(r, null, 2));
      App.toast(titulo+' OK','success');
    } catch(e){ Views.doctor.log('❌ '+e.message); }
  }
};
