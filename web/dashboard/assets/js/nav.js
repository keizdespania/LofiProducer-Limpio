// ═══ KEIZ OS · Navegación ═══
window.Nav = (function(){
  const structure = [
    { label: 'General', items: [
      { id:'inicio', icon:'🏠', label:'Inicio' },
      { id:'chat', icon:'🤖', label:'Dios' },
    ]},
    { label: 'Estudios', items: [
      { id:'musica', icon:'🎵', label:'Música' },
      { id:'imagen', icon:'🎨', label:'Imagen' },
      { id:'voz', icon:'🎙️', label:'Voz' },
      { id:'video', icon:'🎬', label:'Vídeo' },
      { id:'media', icon:'🎞️', label:'Media Vault' },
    ]},
    { label: 'Factory', items: [
      { id:'factory', icon:'🏭', label:'Content Factory' },
      { id:'encuadre', icon:'🎬', label:'El Encuadre', external:'/encuadre' },
    ]},
    { label: 'Canales & Intel', items: [
      { id:'canales', icon:'📺', label:'Mis Canales' },
      { id:'tendencias', icon:'🕵️', label:'Tendencias' },
      { id:'blogs', icon:'📝', label:'Blogs SEO' },
      { id:'informe', icon:'📰', label:'Informe' },
      { id:'analytics', icon:'📊', label:'Analytics' },
      { id:'produccion', icon:'📋', label:'Producción' },
    ]},
    { label: 'Sistema', items: [
      { id:'doctor', icon:'🩺', label:'Doctor' },
      { id:'rss', icon:'📰', label:'RSS' },
      { id:'especialista', icon:'🧠', label:'Especialistas' },
      { id:'prompts', icon:'💡', label:'Prompt Studio' },
      { id:'docs', icon:'📚', label:'Docs' },
      { id:'ajustes', icon:'⚙️', label:'Ajustes' },
      { id:'papelera', icon:'🗑️', label:'Papelera' },
    ]},
  ];
  const all = {};
  structure.forEach(g => g.items.forEach(it => all[it.id] = it));

  function init(){
    const root = document.getElementById('nav-root');
    root.innerHTML = '';
    structure.forEach(g => {
      const group = document.createElement('div');
      group.className = 'nav-group';
      group.innerHTML = `<div class="nav-header">${g.label} <span class="chev">▾</span></div><div class="nav-items"></div>`;
      group.querySelector('.nav-header').onclick = () => group.classList.toggle('collapsed');
      const items = group.querySelector('.nav-items');
      g.items.forEach(it => {
        const a = document.createElement('a');
        a.className = 'nav-item';
        a.href = it.external ? it.external : '#' + it.id;
        if(it.external) a.target = '_blank';
        a.dataset.view = it.id;
        a.innerHTML = `<span class="nav-icon">${it.icon}</span><span>${it.label}</span>`;
        a.onclick = () => { if(window.innerWidth<900) App.closeSidebar(); };
        items.appendChild(a);
      });
      root.appendChild(group);
    });
    // Inyectar vistas al outlet si no existen
    const outlet = document.getElementById('outlet');
    if(!outlet.dataset.ready){
      Object.keys(all).forEach(id => {
        if(!document.getElementById('view-'+id)){
          const v = document.createElement('div');
          v.id = 'view-' + id;
          v.className = 'view';
          v.innerHTML = `<div class="empty-state"><div class="emoji">${all[id].icon}</div><p>Cargando ${all[id].label}...</p></div>`;
          outlet.appendChild(v);
        }
      });
      outlet.dataset.ready = '1';
    }
  }
  function updateActive(id){
    document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === id));
  }
  function exists(id){ return !!all[id]; }
  function getLabel(id){ return all[id] ? all[id].label : id; }
  return { init, updateActive, exists, getLabel, structure, all };
})();
