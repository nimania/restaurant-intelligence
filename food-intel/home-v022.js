FI.bindTheme();
const $=id=>document.getElementById(id);
const DAY=864e5, HOUR=36e5;
const FOLLOW_KEY='fi_followed_brands_v1';
const INTEREST_KEY='fi_manager_interests_v1';
const INTERESTS={
  brand:{label:'مدیریت برند',terms:['brand','marketing','consumer','loyalty','pricing','campaign','برند','بازاریابی','وفاداری','قیمت','marka','pazarlama','müşteri','sadakat','fiyat']},
  strategy:{label:'استراتژی و مدیریت',terms:['strategy','growth','leadership','expansion','finance','franchise','استراتژی','توسعه','مدیریت','سرمایه','büyüme','yatırım','yönetim','franchise','bayilik']},
  ai:{label:'هوش مصنوعی و فناوری',terms:['ai','artificial intelligence','automation','technology','digital','robot','هوش مصنوعی','اتوماسیون','فناوری','ربات','yapay zeka','otomasyon','teknoloji']},
  operations:{label:'عملیات رستوران',terms:['operations','labor','kitchen','supply','food safety','عملیات','آشپزخانه','نیروی انسانی','زنجیره تامین','operasyon','mutfak','tedarik','gıda güvenliği']},
  product:{label:'محصول و نوآوری',terms:['product','menu','innovation','launch','beverage','food','محصول','منو','نوآوری','نوشیدنی','ürün','menü','inovasyon','içecek','gıda']},
  marketing:{label:'مارکتینگ و مشتری',terms:['marketing','consumer','customer','loyalty','social','campaign','مشتری','وفاداری','کمپین','pazarlama','tüketici','müşteri','kampanya']},
  finance:{label:'مالی و سرمایه‌گذاری',terms:['earnings','revenue','sales','profit','investment','roi','فروش','درآمد','سود','سرمایه','ciro','satış','kâr','yatırım']}
};
function getSet(key){try{return new Set(JSON.parse(localStorage.getItem(key)||'[]'))}catch{return new Set()}}
function saveSet(key,set){localStorage.setItem(key,JSON.stringify([...set]))}
let followed=getSet(FOLLOW_KEY), interests=getSet(INTEREST_KEY);
let allItems=[], ready=[];
function ms(x){const t=Date.parse(x?.published_at||'');return Number.isFinite(t)?t:0}
function isRecent(x,h=24){return Date.now()-ms(x)<h*HOUR}
function inferMarket(x,b){if(b?.market)return b.market;if(x.market==='turkey'||x.country==='TR'||x.geo?.primary_country?.code==='TR')return'turkey';if(x.market==='iran'||(x.iran_relevance_score||0)>=70)return'iran';return'world'}
function marketLabel(m){return m==='iran'?'ایران':m==='turkey'?'ترکیه':'جهان'}
function brandCatalog(items){
  const map=new Map((FI.brandCatalog||[]).map(b=>[b.id,b]));
  for(const x of items)for(const b of x.brands||[])if(b?.id&&!map.has(b.id))map.set(b.id,{...b,market:inferMarket(x,b),sector:'صنعت غذا'});
  return [...map.values()];
}
function brandRows(id){return ready.filter(x=>(x.brands||[]).some(b=>b.id===id))}
function sevenDaySeries(rows){
  const start=new Date();start.setHours(0,0,0,0);const base=start.getTime();const vals=Array(7).fill(0);
  rows.forEach(x=>{const age=Math.floor((base-ms(x))/DAY);if(age>=0&&age<7)vals[6-age]++});return vals;
}
function attentionFor(b){
  const rows=brandRows(b.id), now=Date.now();
  const d1=rows.filter(x=>now-ms(x)<DAY).length,d7=rows.filter(x=>now-ms(x)<7*DAY).length,d30=rows.filter(x=>now-ms(x)<30*DAY).length;
  const watch=rows.filter(x=>(x.brand_watch?.matched_brand_ids||[]).includes(b.id)).length;
  const official=rows.filter(x=>x.source?.class==='official_brand_channel').length;
  const raw=d1*16+d7*5+Math.min(d30,20)+Math.min(watch,12)*2+Math.min(official,8)*2;
  const score=Math.max(1,Math.min(100,Math.round(raw)));
  const last=[...rows].sort((a,c)=>ms(c)-ms(a))[0]||null;
  return {score,d1,d7,d30,watch,official,last,series:sevenDaySeries(rows)};
}
function sparkline(values){
  const w=180,h=38,pad=3,max=Math.max(1,...values),step=(w-pad*2)/Math.max(values.length-1,1);
  const pts=values.map((v,i)=>`${(pad+i*step).toFixed(1)},${(h-pad-(v/max)*(h-pad*2)).toFixed(1)}`).join(' ');
  return `<div class="brand-spark"><div><span>فعالیت ۷روزه در رادار</span><b>${values.map(FI.faN).join(' · ')}</b></div><svg viewBox="0 0 ${w} ${h}" role="img" aria-label="فعالیت هفت روز اخیر"><polyline points="${pts}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>`;
}
function logo(b,cls=''){const src=FI.brandLogo?FI.brandLogo(b):'';return src?`<img class="${cls}" src="${FI.esc(src)}" alt="${FI.esc(b.fa||b.name||'')}" loading="lazy" referrerpolicy="no-referrer" onerror="this.outerHTML='<span class=&quot;brand-fallback&quot;>${FI.esc((b.fa||b.name||'?').slice(0,1))}</span>'">`:`<span class="brand-fallback ${cls}">${FI.esc((b.fa||b.name||'?').slice(0,1))}</span>`}
function reason(b,s){
  if(!s.last)return 'این برند تحت رصد است؛ هنوز سیگنال تازه‌ای ثبت نشده.';
  const cats=(s.last.categories||[]).slice(0,2).map(c=>FI.labels?.[c]||c).filter(Boolean);
  if(s.d1)return `${FI.faN(s.d1)} اشاره در ۲۴ ساعت اخیر${cats.length?' · '+cats.join('، '):''}`;
  if(s.d7)return `${FI.faN(s.d7)} خبر در ۷ روز اخیر${cats.length?' · '+cats.join('، '):''}`;
  return `${FI.faN(s.d30)} خبر در ۳۰ روز اخیر`;
}
function toggleFollow(id){followed.has(id)?followed.delete(id):followed.add(id);saveSet(FOLLOW_KEY,followed);renderBrands();renderForYou()}
window.toggleFollow=toggleFollow;
function renderBrands(){
  const brands=brandCatalog(ready).map(b=>[b,attentionFor(b)]).filter(([,s])=>s.d30||s.watch).sort((a,b)=>b[1].score-a[1].score);
  let top=brands.slice(0,8);
  const must=['iran','turkey','world'];
  for(const market of must){if(!top.some(([b])=>b.market===market)){const x=brands.find(([b])=>b.market===market);if(x)top[Math.max(0,top.length-1)]=x}}
  $('hotBrands').innerHTML=top.slice(0,6).map(([b,s])=>`<article class="brand-pulse-card"><div class="brand-pulse-top">${logo(b)}<button class="follow-btn ${followed.has(b.id)?'following':''}" onclick="toggleFollow('${FI.esc(b.id)}')">${followed.has(b.id)?'✓ دنبال می‌کنم':'+ دنبال کردن'}</button></div><h3>${FI.esc(b.fa||b.name)}</h3><small>${FI.esc(b.name||'')} · ${marketLabel(b.market)}</small><div class="attention-line"><span>شاخص توجه رادار</span><b>${FI.faN(s.score)}</b></div><div class="attention-bar"><i style="width:${s.score}%"></i></div>${sparkline(s.series)}<p class="brand-reason">${FI.esc(reason(b,s))}</p><a href="brand.html?id=${encodeURIComponent(b.id)}">در ۳۰ ثانیه ببین چه خبر است ←</a></article>`).join('');
}
function topicSignals(){
  const map=new Map();
  for(const x of ready.filter(y=>Date.now()-ms(y)<7*DAY)){
    for(const c of x.categories||[]){const r=map.get(c)||{id:c,d1:0,d7:0,brands:new Set()};r.d7++;if(isRecent(x))r.d1++;for(const b of x.brands||[])r.brands.add(b.id);map.set(c,r)}
  }
  return [...map.values()].sort((a,b)=>b.d1-a.d1||b.d7-a.d7).slice(0,8)
}
function renderTrends(){
  const rows=topicSignals().slice(0,4);
  $('trendCards').innerHTML=rows.map(x=>{const label=FI.labels?.[x.id]||x.id,icon=FI.categoryIcons?.[x.id]||'◉';return `<a class="trend-card" href="explore.html?category=${encodeURIComponent(x.id)}#feed"><span class="trend-icon">${icon}</span><h3>${FI.esc(label)}</h3><p>${FI.faN(x.brands.size)} برند · ${FI.faN(x.d7)} خبر در ۷ روز</p><div class="trend-meter"><b>${FI.faN(x.d1)}</b><span>خبر در ۲۴ ساعت اخیر</span></div></a>`}).join('')||'<div class="empty">هنوز داده کافی نداریم.</div>';
}
function renderChanges(){
  const rows=[...ready].filter(x=>(x.brands||[]).length&&(x.brand_watch||x.source?.class==='official_brand_channel')).sort((a,b)=>ms(b)-ms(a)).slice(0,8);
  $('changeList').innerHTML=rows.map(x=>{const b=(x.brands||[])[0]||{};return `<a class="change-item" href="story.html?id=${encodeURIComponent(x.id)}">${logo(b,'change-logo')}<div><h3>${FI.richText(x.title_fa||x.title||'')}</h3><p>${FI.esc(b.fa||b.name||'برند')} · ${FI.ago(x.published_at)}${x.source?.class==='official_brand_channel'?' · منبع رسمی':''}</p></div></a>`}).join('')||'<div class="empty">تغییر تازه‌ای ثبت نشده است.</div>';
}
function interestScore(x){
  if(!interests.size)return x.relevance_score||0;
  const hay=[x.title,x.title_fa,x.summary,x.summary_fa,...(x.categories||[]),...(x.topics||[])].join(' ').toLowerCase();let score=x.relevance_score||0;
  for(const id of interests){for(const term of INTERESTS[id]?.terms||[])if(hay.includes(term.toLowerCase()))score+=24}
  if((x.brands||[]).some(b=>followed.has(b.id)))score+=35;
  return score;
}
function renderForYou(){
  const rows=[...ready].filter(x=>Date.now()-ms(x)<14*DAY).sort((a,b)=>interestScore(b)-interestScore(a)||ms(b)-ms(a)).slice(0,6);
  $('forYouList').innerHTML=rows.map(x=>`<div class="brief-item"><a href="story.html?id=${encodeURIComponent(x.id)}">${FI.richText(x.title_fa||x.title||'')}</a><div>${(x.brands||[]).slice(0,2).map(b=>FI.esc(b.fa||b.name)).join(' · ')||FI.srcName(x)} · ${FI.ago(x.published_at)}</div></div>`).join('');
  const labels=[...interests].map(id=>INTERESTS[id]?.label).filter(Boolean);$('personalState').textContent=labels.length?`بر اساس: ${labels.join('، ')}${followed.size?` و ${FI.faN(followed.size)} برند دنبال‌شده`:''}`:'برای شخصی‌سازی، حوزه کاری‌ات را انتخاب کن.';
}
function renderInterestChips(){
  $('interestChips').innerHTML=Object.entries(INTERESTS).map(([id,x])=>`<button class="interest-chip ${interests.has(id)?'active':''}" data-id="${id}">${x.label}</button>`).join('');
  $('interestChips').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{const id=btn.dataset.id;interests.has(id)?interests.delete(id):interests.add(id);saveSet(INTEREST_KEY,interests);renderInterestChips();renderForYou()}));
}
function renderPulse(data){
  const d1=ready.filter(x=>isRecent(x)).length,brandIds=new Set(ready.filter(x=>isRecent(x)).flatMap(x=>(x.brands||[]).map(b=>b.id))),watch=ready.filter(x=>isRecent(x)&&(x.brand_watch||x.source?.class==='official_brand_channel')).length;
  $('pulseNews').textContent=FI.faN(d1);$('pulseBrands').textContent=FI.faN(brandIds.size);$('pulseSignals').textContent=FI.faN(watch);$('pulseSources').textContent=FI.faN(new Set(ready.filter(x=>isRecent(x)).map(x=>x.source?.id).filter(Boolean)).size);$('lastUpdate').textContent=data.generated_at?`آخرین به‌روزرسانی ${new Date(data.generated_at).toLocaleString('fa-IR')}`:'رادار زنده';
}
async function boot(){
  const r=await fetch('data/news.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('news');const data=await r.json();allItems=data.items||[];ready=allItems.filter(x=>x.title_fa&&!['retry','block'].includes(x.translation_quality?.status));renderPulse(data);renderInterestChips();renderBrands();renderTrends();renderChanges();renderForYou();
}
boot().catch(e=>{['hotBrands','trendCards','changeList','forYouList'].forEach(id=>{if($(id))$(id).innerHTML='<div class="empty">داده‌ها فعلاً در دسترس نیستند.</div>'})});