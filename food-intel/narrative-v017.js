(()=>{
  const params=new URLSearchParams(location.search);
  const storyId=params.get('id');
  if(!storyId)return;

  fetch('data/news.json',{cache:'no-store'})
    .then(r=>r.ok?r.json():Promise.reject(new Error('news data unavailable')))
    .then(data=>{
      const item=(data.items||[]).find(x=>x.id===storyId);
      if(!item?.narrative_fa)return;

      const apply=()=>{
        const heads=[...document.querySelectorAll('.report-head h2')];
        const heading=heads.find(h=>/گزارش جامع فارسی|جزئیات فارسی خبر/.test(h.textContent||''));
        if(!heading)return false;
        heading.textContent='روایت تفصیلی فارسی';
        const head=heading.closest('.report-head');
        if(head&&!head.querySelector('.narrative-badge')){
          const badge=document.createElement('span');
          badge.className='editorial-badge narrative-badge';
          badge.textContent='بر پایه بدنه خبر';
          head.appendChild(badge);
        }
        return true;
      };

      if(apply())return;
      const app=document.getElementById('app');
      if(!app)return;
      const observer=new MutationObserver(()=>{
        if(apply())observer.disconnect();
      });
      observer.observe(app,{childList:true,subtree:true});
    })
    .catch(()=>{});
})();
