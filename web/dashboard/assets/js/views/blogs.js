// ═══ KEIZ OS · Blogs SEO ═══
window.Views = window.Views || {};
window.Views.blogs = {
  onEnter: function(){
    const v = document.getElementById('view-blogs');
    v.innerHTML = `
      <h1>📝 Centro Editorial</h1>
      <p class="text-muted mt-2 mb-6">Borradores + publicar en Blogger</p>
      <div class="card mb-6">
        <div class="flex gap-2" style="flex-wrap:wrap">
          <input id="blog-tema" class="input" style="flex:1;min-width:200px" placeholder="Tema (ej: OpenAI GPT-5)">
          <button class="btn btn-primary" onclick="Views.blogs.crear()">✍️ Redactar noticia</button>
          <button class="btn btn-ghost" onclick="Views.blogs.cargar()">🔄 Refresh</button>
        </div>
        <div class="flex gap-2 mt-4" style="flex-wrap:wrap">
          <span class="badge badge-blue" id="blog-stats">Blogger: …</span>
          <span class="badge badge-purple" id="blog-borradores">Borradores: …</span>
        </div>
      </div>
      <div id="blogs-list"><div class="empty-state"><div class="spinner"></div></div></div>
    `;
    Views.blogs.cargar();
  },
  cargar: async function(){
    const el = document.getElementById('blogs-list');
    try {
      const [borr, stats] = await Promise.all([
        App.api('/api/borradores_blog').catch(()=>({borradores:[]})),
        App.api('/api/blogger_stats').catch(()=>({})),
      ]);
      const bs = borr.borradores||borr.files||[];
      document.getElementById('blog-borradores').textContent = 'Borradores: ' + bs.length;
      if(stats.posts!==undefined) document.getElementById('blog-stats').textContent = 'Blogger: ' + (stats.posts||0) + ' posts';
      if(!bs.length){ el.innerHTML = '<div class="empty-state"><div class="emoji">📝</div><p>Sin borradores</p></div>'; return; }
      el.innerHTML = `<div class="grid-2">${bs.map(b=>`
        <div class="card">
          <div class="card-title mb-2">${b.titulo||b.title||b.filename||'Sin título'}</div>
          <p class="text-sm mb-4">${(b.resumen||b.summary||'').substring(0,120)}</p>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm" style="flex:1" onclick="Views.blogs.publicar('${b.filename||b.id}')">📤 Publicar</button>
            <button class="btn btn-ghost btn-sm" onclick="Views.blogs.preview('${b.filename||b.id}')">👁 Ver</button>
            <button class="btn btn-danger btn-sm" onclick="Views.blogs.descartar('${b.filename||b.id}')">🗑</button>
          </div>
        </div>
      `).join('')}</div>`;
    } catch(e){ el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
  },
  crear: async function(){
    const tema = document.getElementById('blog-tema').value.trim();
    if(!tema){ App.toast('Escribe un tema','warning'); return; }
    try { await App.api('/api/crear_post_blog',{method:'POST',body:{tema}}); App.toast('Borrador creado (2-3 min)','success'); setTimeout(()=>Views.blogs.cargar(),3000); } catch(e){}
  },
  publicar: async function(f){
    try { await App.api('/api/publicar_borrador',{method:'POST',body:{filename:f}}); App.toast('Publicado en Blogger ✅','success'); Views.blogs.cargar(); } catch(e){}
  },
  descartar: async function(f){
    if(!confirm('¿Descartar?')) return;
    try { await App.api('/api/descartar_borrador',{method:'POST',body:{filename:f}}); App.toast('Descartado','info'); Views.blogs.cargar(); } catch(e){}
  },
  preview: function(f){ App.toast('Preview: '+f,'info'); }
};
