// ═══ KEIZ OS · RSS ═══
window.Views = window.Views || {};
window.Views.rss = {
  onEnter: function(){
    const v = document.getElementById('view-rss');
    v.innerHTML = `
      <h1>📰 RSS</h1>
      <p class="text-muted mt-2 mb-6">Lector de fuentes</p>
      <div class="card mb-6">
        <div class="flex gap-2">
          <select id="rss-fuente" class="select" style="flex:1">
            <option value="techcrunch">TechCrunch</option>
            <option value="hackernews">Hacker News</option>
            <option value="verge">The Verge</option>
            <option value="boe">BOE</option>
          </select>
          <button class="btn btn-primary" onclick="Views.rss.leer()">📰 Leer</button>
        </div>
      </div>
      <div id="rss-items"></div>
    `;
  },
  leer: async function(){
    const fuente = document.getElementById('rss-fuente').value;
    const el = document.getElementById('rss-items');
    el.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';
    try {
      const r = await App.api('/api/rss_leer',{method:'POST',body:{fuente}});
      const items = r.items || r.articulos || [];
      if(!items.length){ el.innerHTML = '<div class="empty-state"><p>Sin items</p></div>'; return; }
      el.innerHTML = items.slice(0,30).map(i=>`
        <div class="list-item mb-2">
          <div style="flex:1"><div style="font-weight:600">${i.titulo||i.title}</div><div class="text-sm text-muted">${(i.descripcion||i.summary||'').substring(0,120)}</div></div>
          ${i.link?`<a href="${i.link}" target="_blank" class="btn btn-ghost btn-sm">🔗</a>`:''}
        </div>
      `).join('');
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  }
};
