FI.bindTheme();
const $=id=>document.getElementById(id);
const id=FI.params().get('id');
const DAY=864e5;

function brandFrom(items){
  const c=FI.brandCatalogById?.[id];
  if(c)return c;
  for(const item of items){
    const b=(item.brands||[]).find(x=>x.id===id);
    if(b)return {id:b.id,name:b.name||b.id,fa:b.fa||b.name||b.id,market:b.market||((item.market==='iran'||(item.iran_relevance_score||0)>=70)?'iran':'world'),sector:'سایر'};
  }
  return null;
}
function logoHtml(b){
  const logo=FI.brandLogo?FI.brandLogo(b):'';
  return logo?`<img class="brand-avatar" src="${FI.esc(logo)}" alt="" referrerpolicy="no-referrer" onerror="this.style.display='none'">`:`<div class="brand-avatar" style="display:grid;place-items:center;font-family:Estedad">${FI.esc((b.fa||b.name||'?').slice(0,1))}</div>`;
}
function sourceName(x){return x.discovered_publisher||x.source?.name||'منبع'}
function timelineItem(x){
  const watched=(x.brand_watch?.matched_brand_ids||[]).includes(id);
  const official=x.source?.class==='official_brand_channel';
  const summary=String(x.summary_fa||'').trim();
  return `<a class="timeline-item" href="story.html?id=${encodeURIComponent(x.id)}"><div class="timeline-meta"><span>${FI.esc(sourceName(x))}</span><span>•</span><span>${FI.ago(x.published_at)}</span>${watched?'<span class="signal-badge">Brand Watch</span>':''}${official?'<span class="official-badge">منبع رسمی برند</span>':''}</div><h3>${FI.richText(x.title_fa||x.title||'')}</h3>${summary?`<p>${FI.richText(summary.slice(0,260))}${summary.length>260?'…':''}</p>`:''}</a>`;
}
function topTopics(rows){
  const counts=new Map();
  rows.forEach(x=>(x.categories||[]).forEach(c=>counts.set(c,(counts.get(c)||0)+1)));
  return [...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,6);
}

fetch('data/news.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
  const items=data.items||[];
  const brand=brandFrom(items);
  if(!brand){$('brandApp').innerHTML='<div class="empty-brand">این برند در کاتالوگ پیدا نشد.</div>';return}
  const rows=items.filter(x=>x.title_fa&&(x.brands||[]).some(b=>b.id===id)).sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
  const now=Date.now();
  const d30=rows.filter(x=>now-new Date(x.published_at)<30*DAY).length;
  const d7=rows.filter(x=>now-new Date(x.published_at)<7*DAY).length;
  const watch=rows.filter(x=>(x.brand_watch?.matched_brand_ids||[]).includes(id)).length;
  const official=rows.filter(x=>x.source?.class==='official_brand_channel').length;
  const links=FI.brandLinksFor?FI.brandLinksFor(brand):[];
  const direct=links.filter(x=>x.direct);
  const topics=topTopics(rows);
  const market=brand.market==='iran'?'🇮🇷 ایران':'🌍 جهان';
  document.title=`${brand.fa||brand.name} | رادار برندها`;
  $('brandApp').className='brand-profile-layout';
  $('brandApp').innerHTML=`<section class="brand-profile-main"><div class="brand-hero"><div class="brand-profile-header">${logoHtml(brand)}<div><h1>${FI.esc(brand.fa||brand.name)}</h1><p>${FI.esc(brand.name||'')} · ${market} · ${FI.esc(brand.sector||'صنعت غذا')}</p></div></div><div class="brand-tags"><span class="brand-tag watch">● تحت رصد Brand Watch</span><span class="brand-tag">${FI.esc(brand.sector||'صنعت غذا')}</span></div></div><div class="brand-kpis"><div class="brand-kpi"><b>${FI.faN(d30)}</b><span>خبر در ۳۰ روز</span></div><div class="brand-kpi"><b>${FI.faN(d7)}</b><span>خبر در ۷ روز</span></div><div class="brand-kpi"><b>${FI.faN(watch)}</b><span>سیگنال رصد اختصاصی</span></div><div class="brand-kpi"><b>${FI.faN(official)}</b><span>فعالیت از منبع رسمی</span></div></div><div class="brand-hero"><h1 style="font-size:18px">تایم‌لاین برند</h1><p>${rows.length?'آخرین خبرها و سیگنال‌های ثبت‌شده برای این برند.':'هنوز خبر معتبر قابل‌انتشاری برای این برند ثبت نشده؛ برند همچنان در واچ‌لیست فعال است.'}</p></div><div class="timeline">${rows.length?rows.slice(0,60).map(timelineItem).join(''):'<div class="empty-brand">هنوز سیگنالی ثبت نشده است.</div>'}</div></section><aside class="brand-profile-side"><div class="brand-side-card"><h3>وب‌سایت و شبکه‌های رسمی</h3><div class="brand-side-links">${links.map(x=>`<a href="${FI.esc(x.url)}" target="_blank" rel="noopener noreferrer nofollow"><span>${x.icon} ${FI.esc(x.label)}</span><small>${x.direct?'رسمی':'جست‌وجو'}</small></a>`).join('')}</div></div><div class="brand-side-card"><h3>موضوع‌های پرتکرار</h3>${topics.length?topics.map(([topic,count])=>`<div class="mini-stat"><span>${FI.esc(FI.categoryFa?.[topic]||topic)}</span><b>${FI.faN(count)}</b></div>`).join(''):'<p style="color:var(--muted);font-size:11px">هنوز داده کافی نداریم.</p>'}</div><div class="brand-side-card"><h3>دسترسی سریع</h3><div class="brand-actions"><a class="pill-btn" href="${brand.market==='iran'?'iran.html':'./'}?brand=${encodeURIComponent(id)}#feed">فید خبرهای برند</a><a class="pill-btn" href="brands.html?market=${brand.market==='iran'?'iran':'world'}">برندهای ${brand.market==='iran'?'ایران':'جهان'}</a></div></div></aside>`;
}).catch(err=>{$('brandApp').innerHTML=`<div class="empty-brand">خطا در دریافت داده برند: ${FI.esc(err.message||err)}</div>`});
