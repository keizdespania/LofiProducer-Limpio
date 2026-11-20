// ═══ KEIZ OS · Prompt Studio ═══
window.Views = window.Views || {};
window.Views.prompts = {
  onEnter: function(){
    const v = document.getElementById('view-prompts');
    v.innerHTML = `
      <h1>💡 Prompt Studio</h1>
      <p class="text-muted mt-2 mb-6">Mejora prompts con IA</p>
      <div class="card mb-6">
        <div class="flex gap-2 mb-4" style="flex-wrap:wrap">
          ${['visual','musica','seo','estrategia'].map(t=>`<button class="btn btn-ghost btn-sm" onclick="document.getElementById('pr-tipo').value='${t}';App.toast('${t}','info',1000)">${t}</button>`).join('')}
        </div>
        <input type="hidden" id="pr-tipo" value="visual">
        <input id="pr-idea" class="input mb-4" placeholder="Idea base (ej: gato futurista)">
        <button class="btn btn-primary" style="width:100%" onclick="Views.prompts.generar()">💡 Generar prompt mejorado</button>
        <div id="pr-result" class="mt-4"></div>
      </div>
    `;
  },
  generar: async function(){
    const idea = document.getElementById('pr-idea').value.trim();
    if(!idea) return;
    const el = document.getElementById('pr-result');
    el.innerHTML = '<div class="list-item"><span class="spinner"></span><span>Mejorando...</span></div>';
    try {
      const r = await App.api('/api/prompt',{method:'POST',body:{tipo:document.getElementById('pr-tipo').value, idea}});
      el.innerHTML = `<div class="card"><div class="flex between mb-2"><div class="card-title">✨ Resultado</div><button class="btn btn-ghost btn-sm" onclick="navigator.clipboard.writeText(\`${(r.prompt||'').replace(/`/g,'')}\`);App.toast('Copiado','success')">📋 Copiar</button></div><pre style="white-space:pre-wrap;font-family:var(--font);font-size:0.95em">${r.prompt||JSON.stringify(r,null,2)}</pre></div>`;
    } catch(e){ el.innerHTML = `<div class="card" style="border-left:3px solid var(--red)"><p>${e.message}</p></div>`; }
  }
};
