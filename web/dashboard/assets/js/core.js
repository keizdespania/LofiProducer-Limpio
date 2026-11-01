// ═══ KEIZ OS · Core ═══
window.App = (function(){
  const state = { view: 'inicio', theme: localStorage.getItem('keiz_theme') || 'dark' };

  function toast(msg, tipo='info', ms=3500){
    const el = document.createElement('div');
    el.className = 'toast ' + tipo;
    el.innerHTML = `<span style="font-size:1.2em">${tipo==='success'?'✅':tipo==='error'?'❌':tipo==='warning'?'⚠️':'ℹ️'}</span><div style="flex:1;font-size:0.9em">${msg}</div>`;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => { el.classList.add('leaving'); setTimeout(() => el.remove(), 300); }, ms);
  }

  async function api(path, opts={}){
    try {
      const r = await fetch(path, {
        headers: {'Content-Type':'application/json'},
        ...opts,
        body: opts.body ? (typeof opts.body==='string'?opts.body:JSON.stringify(opts.body)) : undefined
      });
      if(!r.ok) throw new Error('HTTP '+r.status);
      return await r.json();
    } catch(e){
      toast('Error: ' + e.message, 'error');
      throw e;
    }
  }

  function route(){
    const hash = location.hash.replace('#','') || 'inicio';
    const view = hash.split('?')[0];
    if(!Nav.exists(view)){ location.hash = 'inicio'; return; }
    state.view = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById('view-' + view);
    if(target) target.classList.add('active');
    Nav.updateActive(view);
    const label = Nav.getLabel(view);
    document.getElementById('bc-current').textContent = label;
    if(window.Views && window.Views[view] && window.Views[view].onEnter){
      try { window.Views[view].onEnter(); } catch(e){ console.error(e); }
    }
  }

  function toggleTheme(){
    state.theme = state.theme==='dark'?'light':'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('keiz_theme', state.theme);
    toast('Tema: '+state.theme, 'info', 1500);
  }

  function toggleSidebar(){ document.getElementById('sidebar').classList.toggle('open'); }
  function closeSidebar(){ document.getElementById('sidebar').classList.remove('open'); }

  if(state.theme==='light') document.documentElement.setAttribute('data-theme','light');
  return { state, toast, api, route, toggleTheme, toggleSidebar, closeSidebar };
})();

// ═══ Atajos globales ═══
document.addEventListener('keydown', e => {
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if(e.key === 'g' && !e.ctrlKey && !e.metaKey){ window._gPressed = Date.now(); return; }
  if(window._gPressed && Date.now() - window._gPressed < 1000){
    const map = { i:'inicio', d:'chat', m:'musica', v:'video', p:'imagen', c:'canales', f:'factory', b:'blogs', t:'tendencias', a:'analytics', s:'ajustes', r:'produccion', o:'doctor', e:'especialista' };
    if(map[e.key]){ location.hash = map[e.key]; App.route(); }
    window._gPressed = 0;
  }
  if(e.key === '?'){
    App.toast('Ctrl+K buscar · G+I inicio · G+D dios · G+M música · G+V vídeo · G+F factory · G+B blogs', 'info', 8000);
  }
});
