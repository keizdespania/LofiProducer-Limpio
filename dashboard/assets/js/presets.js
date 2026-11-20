// ═══ KEIZ OS · Presets export/import ═══
window.Presets = {
  exportar: function(){
    const all = {};
    Object.keys(localStorage).filter(k=>k.startsWith('keiz_preset_')).forEach(k=>{ all[k] = localStorage.getItem(k); });
    const blob = new Blob([JSON.stringify(all, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'keiz_presets_'+Date.now()+'.json'; a.click();
    URL.revokeObjectURL(url);
    App.toast('Presets exportados','success');
  },
  importar: function(){
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.json';
    input.onchange = e => {
      const f = e.target.files[0]; if(!f) return;
      const r = new FileReader();
      r.onload = () => {
        try {
          const data = JSON.parse(r.result);
          Object.entries(data).forEach(([k,v]) => localStorage.setItem(k, v));
          App.toast('Presets importados: '+Object.keys(data).length, 'success');
        } catch(err){ App.toast('JSON inválido', 'error'); }
      };
      r.readAsText(f);
    };
    input.click();
  },
  guardar: function(motor, nombre, params){
    localStorage.setItem('keiz_preset_'+motor+'_'+nombre, JSON.stringify({motor, nombre, params, ts:Date.now()}));
    App.toast('Preset "'+nombre+'" guardado', 'success');
  },
  listar: function(motor){
    const items = [];
    Object.keys(localStorage).filter(k=>k.startsWith('keiz_preset_'+motor+'_')).forEach(k=>{
      try { items.push(JSON.parse(localStorage.getItem(k))); } catch(e){}
    });
    return items;
  }
};
