FI.bindTheme();
const $=id=>document.getElementById(id);
const DAY=864e5;
const now=Date.now();

function brandItems(items,id){
  return items.filter(x=>x.title_fa&&(x.brands||[]).some(b=>b.id===id));
}
function statsFor(items,brand){
  const rows=brandItems(items,brand.id).sort((a,b)=>new Date(b.published_at)-new Date(a.published_at));
  const d30=rows.filter(x=>now-new Date(x.published_at)<30*DAY).length;
  const d7=rows.filter(x=>now-new Date(x.published_at)<7*DAY).length;
  const watched=rows.filter(x=>(x.brand_watch?.matched_brand_ids||[]).includes(brand.id)).length;
  const official=rows.filter(x=>x.source?.class==='official_brand_channel').length;
  return {rows,d30,d7,watched,official,last:rows[0]||null};
}
function logoHtml(b){
  const logo=FI.brandLogo?FI.brandLogo(b):'';
  return logo?`<img src="${FI.esc(logo)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">`:`<div class="brand-avatar" style="display:grid;place-items:center;font-family:Estedad">${FI.esc((b.fa||b.name||'?').slice(0,1))}</div>`;
}
function marketLabel(market){
  if(market==='iran')return'🇮🇷 ایران';
  if(market==='turkey')return'🇹🇷 ترکیه';
  return'🌍 جهان';
}
function inferMarket(item,b){
  if(b?.market)return b.market;
  if(item.market==='turkey'||item.country==='TR'||item.geo?.primary_country?.code==='TR')return'turkey';
  if(item.market==='iran'||(item.iran_relevance_score||0)>=70)return'iran';
  return'world';
}
function card(b,s){
  const market=marketLabel(b.market);
  const last=s.last?`${FI.ago(s.last.published_at)} — ${FI.esc(s.last.title_fa)}`:'هنوز خبر قابل‌انتشاری برای این برند ثبت نشده است.';
  const links=FI.brandLinksFor?FI.brandLinksFor(b).filter(x=>x.direct).slice(0,2):[];
  return `<article class="brand-card"><div class="brand-card-head">${logoHtml(b)}<div><h2>${FI.esc(b.fa||b.name)}</h2><small>${FI.esc(b.name||'')}</small></div></div><div class="brand-tags"><span class="brand-tag watch">● تحت رصد</span><span class="brand-tag">${market}</span><span class="brand-tag">${FI.esc(b.sector||'صنعت غذا')}</span></div><div class="brand-stats"><div class="brand-stat"><b>${FI.faN(s.d30)}</b><span>خبر ۳۰ روز</span></div><div class="brand-stat"><b>${FI.faN(s.d7)}</b><span>خبر ۷ روز</span></div><div class="brand-stat"><b>${FI.faN(s.watched)}</b><span>سیگنال واچ</span></div></div><div class="brand-last">${last}</div><div class="brand-actions"><a class="pill-btn" href="brand.html?id=${encodeURIComponent(b.id)}">پروفایل برند ←</a>${links.map(x=>`<a class="pill-btn" target="_blank" rel="noopener noreferrer nofollow" href="${FI.esc(x.url)}">${x.icon} ${FI.esc(x.label)}</a>`).join('')}</div></article>`;
}

fetch('data/news.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
  const items=data.items||[];
  const catalog=[...(FI.brandCatalog||[])];
  const seen=new Map(catalog.map(x=>[x.id,x]));
  for(const item of items)for(const b of item.brands||[]){
    if(!b?.id||seen.has(b.id))continue;
    seen.set(b.id,{id:b.id,name:b.name||b.id,fa:b.fa||b.name||b.id,market:inferMarket(item,b),sector:'سایر',watched:false});
  }
  const brands=[...seen.values()];
  const stats=new Map(brands.map(b=>[b.id,statsFor(items,b)]));
  const sectors=[...new Set(brands.map(x=>x.sector).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'fa'));
  $('brandSector').innerHTML='<option value="">همه حوزه‌ها</option>'+sectors.map(x=>`<option value="${FI.esc(x)}">${FI.esc(x)}</option>`).join('');
  const params=FI.params();
  if(params.get('market'))$('brandMarket').value=params.get('market');
  function render(){
    const q=String($('brandSearch').value||'').trim().toLowerCase();
    const market=$('brandMarket').value;
    const sector=$('brandSector').value;
    const rows=brands.filter(b=>{
      if(market&&b.market!==market)return false;
      if(sector&&b.sector!==sector)return false;
      const hay=`${b.fa||''} ${b.name||''} ${b.sector||''}`.toLowerCase();
      return !q||hay.includes(q);
    }).sort((a,b)=>{
      const sa=stats.get(a.id),sb=stats.get(b.id);
      return (sb.d30-sa.d30)||((sb.last?+new Date(sb.last.published_at):0)-(sa.last?+new Date(sa.last.published_at):0))||(a.fa||a.name).localeCompare(b.fa||b.name,'fa');
    });
    $('brandCount').textContent=`${FI.faN(rows.length)} برند`;
    $('brandGrid').innerHTML=rows.length?rows.map(b=>card(b,stats.get(b.id))).join(''):'<div class="empty-brand">برندی با این فیلتر پیدا نشد.</div>';
  }
  ['brandSearch','brandMarket','brandSector'].forEach(id=>$(id).addEventListener(id==='brandSearch'?'input':'change',render));
  render();
}).catch(err=>{$('brandGrid').innerHTML=`<div class="empty-brand">خطا در دریافت داده برندها: ${FI.esc(err.message||err)}</div>`});
