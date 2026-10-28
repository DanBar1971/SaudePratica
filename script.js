'use strict';
(function () {
  const REPO='DanBar1971/AndroidAppDev';
  const descriptions={
    alarm:'Quando chega a hora, o alarme apresenta a medicação e as ações disponíveis. A apresentação em ecrã inteiro depende das permissões e das regras do Android.',
    intakes:'Consulta as tomas por confirmar e as já confirmadas. Cada medicamento tem o seu próprio registo, mesmo nos alarmes de grupo.',
    nutrition:'Guarda fotografias das refeições e acompanha alimentos e porções. A análise com Gemini é opcional e requer quota disponível.',
    docs:'Arquiva e consulta imagens, PDFs e relatórios no perfil correspondente, para os encontrares quando precisares.'
  };
  const tabs=Array.from(document.querySelectorAll('.screen-tabs [role="tab"]'));
  function selectTab(tab,moveFocus) {
    tabs.forEach(t=>{
      const yes=t===tab;
      t.setAttribute('aria-selected',String(yes));
      t.tabIndex=yes?0:-1;
      const p=document.getElementById('panel-'+t.dataset.panel);
      if(p) {p.hidden=!yes;p.classList.toggle('is-visible',yes);}
    });
    document.getElementById('screen-description').textContent=descriptions[tab.dataset.panel]||'';
    if(moveFocus)tab.focus();
  }
  tabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>selectTab(tab,false));
    tab.addEventListener('keydown',e=>{
      let next=-1;
      if(e.key==='ArrowRight'||e.key==='ArrowDown')next=(index+1)%tabs.length;
      if(e.key==='ArrowLeft'||e.key==='ArrowUp')next=(index-1+tabs.length)%tabs.length;
      if(e.key==='Home')next=0;
      if(e.key==='End')next=tabs.length-1;
      if(next>=0){e.preventDefault();selectTab(tabs[next],true);}
    });
  });
  const menuBtn=document.querySelector('.menu-toggle');
  const menu=document.querySelector('#main-menu');
  if(menuBtn&&menu){
    menuBtn.addEventListener('click',()=>{const open=menuBtn.getAttribute('aria-expanded')==='true';menuBtn.setAttribute('aria-expanded',String(!open));menu.classList.toggle('is-open',!open);});
    menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menuBtn.setAttribute('aria-expanded','false');menu.classList.remove('is-open');}));
  }
  const year=document.getElementById('year'); if(year)year.textContent=String(new Date().getFullYear());
  // Public release metadata only; no clinical information is sent or requested.
  fetch('https://api.github.com/repos/'+REPO+'/releases/latest',{headers:{'Accept':'application/vnd.github+json'}})
  .then(r=>{if(!r.ok)throw Error('Release unavailable');return r.json();})
  .then(data=>{
    if(!/^v\d+(?:\.\d+)+$/.test(data.tag_name))return;
    document.querySelectorAll('[data-release]').forEach(el=>el.textContent=data.tag_name);
    if(typeof data.html_url==='string'&&data.html_url.startsWith('https://github.com/'+REPO+'/releases/')){
      document.querySelectorAll('[data-release-link]').forEach(el=>el.href=data.html_url);
    }
    const apk=Array.isArray(data.assets)?data.assets.find(a=>a.name==='SaudePratica.apk'):null;
    if(apk&&typeof apk.browser_download_url==='string'&&apk.browser_download_url.startsWith('https://github.com/'+REPO+'/releases/download/')){
      document.querySelectorAll('[data-download]').forEach(el=>el.href=apk.browser_download_url);
    }
  }).catch(()=>{/* Static, permanent latest-release links still work offline or under API limits. */});
})();