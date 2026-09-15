(()=>{
  const q=s=>encodeURIComponent(String(s||'').trim());
  const google=(domain,name)=>`https://www.google.com/search?q=${q(`site:${domain} "${name}" official`)}`;
  FI.brandLinksFor=b=>{
    const name=b?.name||b?.fa||b?.id||'';
    const p=FI.brandProfile?FI.brandProfile(b):(FI.brandProfiles?.[b?.id]||{});
    return [
      {id:'website',label:p.website?'وب‌سایت رسمی':'یافتن وب‌سایت رسمی',icon:'🌐',url:p.website||`https://www.google.com/search?q=${q(`${name} official website`)}`,direct:Boolean(p.website)},
      {id:'instagram',label:'اینستاگرام',icon:'◎',url:p.instagram||google('instagram.com',name),direct:Boolean(p.instagram)},
      {id:'youtube',label:'یوتیوب',icon:'▶',url:p.youtube||`https://www.youtube.com/results?search_query=${q(`${name} official`)}`,direct:Boolean(p.youtube)},
      {id:'linkedin',label:'لینکدین',icon:'in',url:p.linkedin||`https://www.linkedin.com/search/results/companies/?keywords=${q(name)}`,direct:Boolean(p.linkedin)},
      {id:'telegram',label:'تلگرام',icon:'✈',url:p.telegram||google('t.me',name),direct:Boolean(p.telegram)},
      {id:'aparat',label:'آپارات',icon:'◉',url:p.aparat||`https://www.aparat.com/result/${q(name)}`,direct:Boolean(p.aparat)},
      {id:'x',label:'X',icon:'𝕏',url:p.x||`https://x.com/search?q=${q(`${name} official`)}`,direct:Boolean(p.x)},
      {id:'tiktok',label:'تیک‌تاک',icon:'♪',url:p.tiktok||google('tiktok.com',name),direct:Boolean(p.tiktok)}
    ];
  };
})();
