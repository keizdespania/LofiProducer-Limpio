// ═══ KEIZ OS · Factory (árbol visual de producción) ═══
window.Views = window.Views || {};
window.Views.factory = {
  onEnter: async function(){
    const v = document.getElementById('view-factory');
    v.innerHTML = `
      <div class="flex between center mb-6">
        <div><h1>🏭 Content Factory</h1><p class="text-muted mt-2">Producción del día en vivo</p></div>
        <div class="flex gap-2"><button class="btn btn-primary" onclick="Views.factory.lanzar()">🚀 Lanzar pipeline</button></div>
      </div>
      <div class="card mb-6">
        <div class="card-header"><div class="card-title">📅 Fecha</div></div>
        <select id="fac-fecha" class="select" onchange="Views.factory.cargar(this.value)"><option>Cargando...</option></select>
      </div>
      <div id="fac-arbol"><div class="empty-state"><div class="spinner"></div><p class="mt-4">Cargando árbol de producción...</p></div></div>
    `;
    try {
      const r = await App.api('/api/encuadre/fechas');
      const sel = document.getElementById('fac-fecha');
      if(r.fechas && r.fechas.length){
        sel.innerHTML = r.fechas.map(f=>`<option value="${f}">${f}</option>`).join('');
        Views.factory.cargar(r.fechas[0]);
      } else { sel.innerHTML = '<option>Sin producciones</option>'; }
    } catch(e){ console.warn(e); }
  },
  cargar: async function(fecha){
    const root = document.getElementById('fac-arbol');
    if(!fecha) return;
    root.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';
    try {
      const [prod, redes] = await Promise.all([
        App.api('/api/encuadre/datos/'+fecha).catch(()=>null),
        App.api('/api/encuadre/datos/'+fecha).catch(()=>null)
      ]);
      const d = prod || redes || {};
      // Árbol estático (los datos pueden variar)
      const nodos = [
        { emoji:'📥', titulo:'INPUT · Medios', descripcion:(d.medios || d.fuentes || 11)+' medios analizados', estado:'ok', color:'blue' },
        { emoji:'🧠', titulo:'ANÁLISIS · Agentes', descripcion:(d.agentes || 15)+' agentes ejecutados', estado:'ok', color:'purple' },
        { emoji:'🏭', titulo:'PRODUCCIÓN', descripcion:'Artículo + shorts + vídeo + podcast', estado:'ok', color:'purple' },
        { emoji:'📤', titulo:'DISTRIBUCIÓN', descripcion:'Web, Blogger, YouTube, Redes', estado:'parcial', color:'yellow' },
      ];
      root.innerHTML = `<div style="position:relative;padding-left:40px;">${nodos.map((n,i)=>`
        <div style="position:relative;margin-bottom:24px;">
          ${i<nodos.length-1?`<div style="position:absolute;left:-28px;top:56px;width:2px;height:calc(100% + 8px);background:linear-gradient(to bottom,var(--${n.color}),transparent);"></div>`:''}
          <div style="position:absolute;left:-40px;top:16px;width:24px;height:24px;border-radius:50%;background:var(--${n.color});display:flex;align-items:center;justify-content:center;font-size:0.7em;box-shadow:0 0 16px var(--${n.color}-glow,var(--purple-glow));">${i+1}</div>
          <div class="card">
            <div class="flex between center mb-2">
              <div class="card-title">${n.emoji} ${n.titulo}</div>
              <span class="badge badge-${n.color}">${n.estado}</span>
            </div>
            <p class="text-sm">${n.descripcion}</p>
          </div>
        </div>
      `).join('')}</div>
      <div class="mt-6"><button class="btn btn-ghost" onclick="location.href='/encuadre'" style="width:100%">🎬 Abrir El Encuadre completo →</button></div>`;
    } catch(e){ root.innerHTML = '<div class="empty-state"><p>Error cargando datos</p></div>'; }
  },
  lanzar: function(){
    App.api('/api/encuadre/run_pipeline',{method:'POST'}).then(()=>{ App.toast('Pipeline lanzado 🚀','success'); setTimeout(()=>Views.factory.onEnter(),2000); }).catch(()=>{});
  }
};

// Auto-tema El Encuadre cuando se entra a factory
const _origFactoryOnEnter = window.Views.factory.onEnter;
window.Views.factory.onEnter = function(){
  document.documentElement.setAttribute('data-theme', 'encuadre');
  return _origFactoryOnEnter.apply(this, arguments);
};
