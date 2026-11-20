// ═══ KEIZ OS · Command Palette (Ctrl+K) ═══
window.CommandPalette = (function(){
  let selected = 0, filtered = [];
  const actions = [
    { id:'run-pipeline', icon:'🚀', label:'Lanzar pipeline del día', action:()=>App.api('/api/encuadre/run_pipeline',{method:'POST'}).then(()=>App.toast('Pipeline lanzado','success')) },
    { id:'audit-dios', icon:'🔍', label:'Auditar ecosistema con Dios', action:()=>App.api('/api/auditar_dios',{method:'POST'}).then(r=>App.toast('Auditoría: '+(r.msg||'OK'),'info')) },
    { id:'doctor', icon:'🩺', label:'Diagnóstico del doctor', action:()=>{ location.hash='doctor'; App.route(); } },
    { id:'health', icon:'💚', label:'Comprobar salud del sistema', action:()=>App.api('/api/dashboard').then(r=>App.toast('Flask OK · '+(r.total_canales||0)+' canales','success')) },
    { id:'clear-cache', icon:'🧹', label:'Limpiar caché', action:()=>App.toast('Limpieza lanzada','info') },
  ];
  const views = () => Object.values(Nav.all).map(v => ({ id:'view-'+v.id, icon:v.icon, label:'Ir a '+v.label, action:()=>{ location.hash=v.id; App.route(); } }));

  function buildAll(){
    const viewCmds = views().map(v=>({ ...v, group:'Vistas' }));
    const actCmds = actions.map(a=>({ ...a, group:'Acciones' }));
    return [...viewCmds, ...actCmds];
  }
  let allCmds = [];

  function open(){
    document.getElementById('cmd-palette').classList.add('open');
    const input = document.getElementById('cmd-input');
    input.value = ''; input.focus(); selected = 0;
    allCmds = buildAll();
    render(allCmds);
  }
  function close(){ document.getElementById('cmd-palette').classList.remove('open'); }
  function filter(q){
    if(!q) return allCmds;
    const lq = q.toLowerCase().replace(/^>/,'');
    return allCmds.filter(c => c.label.toLowerCase().includes(lq) || c.id.includes(lq));
  }
  function render(items){
    filtered = items;
    const root = document.getElementById('cmd-results');
    if(items.length===0){ root.innerHTML = '<div class="empty-state" style="padding:24px"><p>Sin resultados</p></div>'; return; }
    let html = '', lastGroup = '';
    items.forEach((it, i) => {
      if(it.group !== lastGroup){ html += `<div class="cmd-group-label">${it.group}</div>`; lastGroup = it.group; }
      html += `<div class="cmd-item ${i===selected?'selected':''}" data-i="${i}"><span class="cmd-icon">${it.icon}</span><span class="cmd-label">${it.label}</span></div>`;
    });
    root.innerHTML = html;
    root.querySelectorAll('.cmd-item').forEach(el => {
      el.onclick = () => { const it = filtered[+el.dataset.i]; if(it){ close(); it.action(); } };
    });
  }
  function init(){
    document.getElementById('cmd-input').addEventListener('input', e => { selected = 0; render(filter(e.target.value)); });
    document.getElementById('cmd-input').addEventListener('keydown', e => {
      if(e.key==='ArrowDown'){ e.preventDefault(); selected = Math.min(selected+1, filtered.length-1); render(filter(document.getElementById('cmd-input').value)); }
      else if(e.key==='ArrowUp'){ e.preventDefault(); selected = Math.max(0, selected-1); render(filter(document.getElementById('cmd-input').value)); }
      else if(e.key==='Enter'){ e.preventDefault(); const it = filtered[selected]; if(it){ close(); it.action(); } }
      else if(e.key==='Escape') close();
    });
    document.addEventListener('keydown', e => {
      if((e.ctrlKey || e.metaKey) && e.key==='k'){ e.preventDefault(); open(); }
      if(e.key==='Escape') close();
    });
  }
  return { init, open, close };
})();
