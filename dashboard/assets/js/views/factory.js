// ═══ KEIZ OS · Factory (datos reales) ═══
window.Views = window.Views || {};
window.Views.factory = {
  onEnter: async function(){
    document.documentElement.setAttribute('data-theme', 'encuadre');
    const v = document.getElementById('view-factory');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🏭 Content Factory</h1><p class="text-muted mt-2">Producción real del día</p></div>
        <button class="btn btn-primary" onclick="Views.factory.lanzar()">🚀 Lanzar pipeline</button>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">📅 Selecciona fecha</div></div>
        <select id="fac-fecha" class="select" onchange="Views.factory.cargar(this.value)"><option>Cargando...</option></select>
      </div>
      <div id="fac-arbol"></div>
    `;
    try {
      const r = await App.api('/api/encuadre/fechas');
      const sel = document.getElementById('fac-fecha');
      if(r.fechas && r.fechas.length){
        sel.innerHTML = r.fechas.map(f=>`<option value="${f}">${f}</option>`).join('');
        Views.factory.cargar(r.fechas[0]);
      } else sel.innerHTML = '<option>Sin producciones</option>';
    } catch(e){ document.getElementById('fac-arbol').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  cargar: async function(fecha){
    const root = document.getElementById('fac-arbol');
    if(!fecha) return;
    root.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';
    try {
      // Probar varios JSON del día
      const [datos, redes] = await Promise.all([
        App.api('/api/encuadre/datos/'+fecha).catch(()=>null),
        App.api('/api/encuadre/datos/'+fecha).catch(()=>null)
      ]);
      const d = datos || redes || {};
      const medios = d.medios || d.fuentes || d.total_medios || '?';
      const temas = (d.temas||d.tendencias||[]).length || '?';
      const hooks = (d.hooks||[]).length || '?';
      const posts = (d.posts||d.articulos||[]).length || '?';
      root.innerHTML = `<div style="position:relative;padding-left:40px;">${[
        {emoji:'📥',titulo:'INPUT · Medios',desc:`${medios} medios analizados`,color:'blue'},
        {emoji:'🧠',titulo:'ANÁLISIS · Agentes',desc:`${temas} temas · ${hooks} hooks generados`,color:'purple'},
        {emoji:'🏭',titulo:'PRODUCCIÓN',desc:`${posts} posts · artículo + shorts + vídeo + podcast`,color:'purple'},
        {emoji:'📤',titulo:'DISTRIBUCIÓN',desc:'Web, Blogger, YouTube, Redes sociales',color:'yellow'},
      ].map((n,i,arr)=>`
        <div style="position:relative;margin-bottom:24px;">
          ${i<arr.length-1?`<div style="position:absolute;left:-28px;top:56px;width:2px;height:calc(100% + 8px);background:linear-gradient(to bottom,var(--${n.color}),transparent);"></div>`:''}
          <div style="position:absolute;left:-40px;top:16px;width:24px;height:24px;border-radius:50%;background:var(--${n.color});display:flex;align-items:center;justify-content:center;font-size:0.7em;color:white;font-weight:bold;">${i+1}</div>
          <div class="card">
            <div class="flex between center mb-2">
              <div class="card-title">${n.emoji} ${n.titulo}</div>
              <span class="badge badge-${n.color}">✓</span>
            </div>
            <p class="text-sm">${n.desc}</p>
          </div>
        </div>
      `).join('')}</div>
      <div class="mt-6"><button class="btn btn-ghost" onclick="location.href='/encuadre'" style="width:100%">🎬 Abrir El Encuadre completo →</button></div>`;
    } catch(e){ root.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  lanzar: async function(){
    if(!confirm('¿Lanzar pipeline del día?')) return;
    App.toast('Pipeline lanzado 🚀','success');
    try { await App.api('/api/encuadre/run_pipeline',{method:'POST'}); setTimeout(()=>Views.factory.onEnter(),3000); } catch(e){}
  }
};
