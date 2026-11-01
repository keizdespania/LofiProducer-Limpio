// ═══ KEIZ OS · Centro de Informes ═══
window.Views = window.Views || {};
window.Views.informe = {
  onEnter: function(){
    const v = document.getElementById('view-informe');
    v.innerHTML = `
      <h1>📰 Centro de Informes</h1>
      <p class="text-muted mt-2 mb-6">Informes por nicho con PDF</p>
      <div class="card mb-6">
        <div class="flex gap-2">
          <select id="inf-nicho" class="select" style="flex:1">
            <option value="ia_news">IA News</option>
            <option value="finanzas_barrio">Finanzas Barrio</option>
            <option value="boe">BOE</option>
            <option value="lofi">Lofi</option>
          </select>
          <button class="btn btn-primary" onclick="Views.informe.generar()">📄 Generar</button>
          <button class="btn btn-ghost" onclick="Views.informe.cargar()">🔄 Refresh</button>
        </div>
      </div>
      <div id="informe-list"><div class="empty-state"><div class="spinner"></div></div></div>
    `;
    Views.informe.cargar();
  },
  cargar: async function(){
    const el = document.getElementById('informe-list');
    try {
      const r = await App.api('/api/listar_informes').catch(()=>({informes:[]}));
      const arr = r.informes || r.files || [];
      if(!arr.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📰</div><p>Sin informes</p></div>'; return; }
      el.innerHTML = arr.map(i=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">📄 ${i.nombre||i.filename}</div><div class="text-sm text-muted">${i.fecha||''}</div></div>
          <a href="${i.url||i.path||'#'}" target="_blank" class="btn btn-ghost btn-sm">📥 Abrir</a>
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  generar: async function(){
    const nicho = document.getElementById('inf-nicho').value;
    try { await App.api('/api/informe_generar/'+nicho,{method:'POST'}); App.toast('Informe generando...','info'); setTimeout(()=>Views.informe.cargar(),5000); } catch(e){}
  }
};
