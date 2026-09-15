FI.bindTheme();
const $=id=>document.getElementById(id);
const id=FI.params().get('id');

const insights={
  restaurant_technology_ai:'اهمیت این خبر بیشتر در اثر فناوری بر سفارش‌گیری، سرعت سرویس، هزینه نیروی انسانی، داده مشتری و کنترل عملیات رستوران است.',
  equipment_automation:'در خبرهای تجهیزات و اتوماسیون، نکته کلیدی اثر فناوری بر ظرفیت، یکنواختی کیفیت، مصرف انرژی، تعمیرات و بهره‌وری است.',
  food_cost_pricing:'این موضوع مستقیماً به حاشیه سود، مهندسی منو، قیمت‌گذاری و رفتار خرید مشتری مربوط می‌شود.',
  supply_chain:'این خبر می‌تواند روی موجودی، قیمت مواد اولیه، دسترسی به محصول و برنامه‌ریزی خرید اپراتورها اثر بگذارد.',
  food_safety:'اهمیت خبرهای ایمنی غذا در ریسک سلامت، فراخوان محصول، الزامات قانونی و اعتماد مشتری است.',
  consumer_behavior:'این خبر از زاویه تغییر رفتار مشتری مهم است؛ تغییری که می‌تواند روی منو، قیمت، کانال فروش و بازاریابی اثر بگذارد.',
  marketing_branding:'ارزش این خبر بیشتر به جایگاه‌سازی برند، تجربه مشتری، تبلیغات و تمایز رقابتی مربوط است.',
  restaurant_design_decor:'طراحی و دکور فقط مسئله زیبایی نیست؛ می‌تواند روی جریان حرکت، ظرفیت، تجربه مشتری و کارایی عملیات اثر بگذارد.',
  packaging_design:'بسته‌بندی هم‌زمان با هزینه، ایمنی، لجستیک، تجربه برند و ماندگاری محصول ارتباط دارد.',
  food_manufacturing:'برای تولیدکنندگان، این خبر با ظرفیت تولید، فرآیند، کیفیت، هزینه و فناوری کارخانه پیوند دارد.',
  menu_product_innovation:'نوآوری منو و محصول می‌تواند ابزار جذب مشتری باشد و هم‌زمان روی پیچیدگی عملیات، هزینه مواد و سرعت سرویس اثر بگذارد.',
  delivery_drive_thru:'دلیوری و درایو‌ثرو مستقیماً به سرعت سرویس، تجربه دیجیتال، هزینه کانال و طراحی عملیات مرتبط است.',
  restaurant_operations:'این خبر در حوزه عملیات قرار می‌گیرد؛ یعنی جریان کار، سرعت سرویس، نیروی انسانی، کنترل هزینه و ثبات کیفیت.'
};

function relatedScore(a,b){
  let s=0;
  const ba=new Set((a.brands||[]).map(x=>x.id)),bb=new Set((b.brands||[]).map(x=>x.id));
  for(const x of ba)if(bb.has(x))s+=5;
  const ca=new Set(a.categories||[]),cb=new Set(b.categories||[]);
  for(const x of ca)if(cb.has(x))s+=3;
  const ta=new Set(a.topics||[]),tb=new Set(b.topics||[]);
  for(const x of ta)if(tb.has(x))s+=2;
  if(a.geo?.primary_country?.code&&a.geo.primary_country.code===b.geo?.primary_country?.code)s+=1;
  return s;
}

function reportCoverage(x){
  if(x.report_coverage)return x.report_coverage;
  const n=(x.summary||'').length;
  if(x.report_fa)return'گسترده';
  if(n>=900)return'گسترده';
  if(n>=350)return'متوسط';
  return'بر پایه خلاصه منبع';
}

function normalizedText(text){
  return String(text||'')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\u200c\u200e\u200f\u2066-\u2069]/g,' ')
    .replace(/[^\p{L}\p{N}]+/gu,' ')
    .replace(/\s+/g,' ')
    .trim();
}

function textTokens(text){
  return new Set(normalizedText(text).split(' ').filter(x=>x.length>1));
}

function similarity(a,b){
  const na=normalizedText(a),nb=normalizedText(b);
  if(!na||!nb)return 0;
  if(na===nb)return 1;
  const shorter=na.length<=nb.length?na:nb;
  const longer=na.length>nb.length?na:nb;
  let containment=0;
  if(shorter.length>=35&&longer.includes(shorter))containment=shorter.length/longer.length;
  const aa=textTokens(a),bb=textTokens(b);
  if(!aa.size||!bb.size)return containment;
  let common=0;
  for(const token of aa)if(bb.has(token))common+=1;
  const dice=(2*common)/(aa.size+bb.size);
  return Math.max(containment,dice);
}

function nearDuplicate(a,b,threshold=.78){
  return Boolean(a&&b&&similarity(a,b)>=threshold);
}

function materiallyRicher(report,summary,title){
  if(!report)return false;
  if(nearDuplicate(report,title,.9))return false;
  if(!summary)return true;
  const r=normalizedText(report),s=normalizedText(summary);
  if(!r)return false;
  if(r.length>=s.length*1.4&&similarity(report,summary)<.93)return true;
  return !nearDuplicate(report,summary,.76);
}

function distinctKeyPoints(x,lead,report){
  const raw=Array.isArray(x.key_points_fa)?x.key_points_fa:[];
  const out=[];
  for(const value of raw){
    const point=String(value||'').trim();
    if(point.length<25)continue;
    if(nearDuplicate(point,x.title_fa,.88)||nearDuplicate(point,lead,.9))continue;
    if(report&&point.length>report.length*.72&&nearDuplicate(point,report,.8))continue;
    if(out.some(existing=>nearDuplicate(existing,point,.82)))continue;
    out.push(point);
    if(out.length>=5)break;
  }
  return out.length>=2?out:[];
}

function reportHtml(text){
  const parts=String(text||'').split(/\n\s*\n+/).map(x=>x.trim()).filter(Boolean);
  return parts.map(p=>`<p class="report-copy">${FI.richText(p)}</p>`).join('');
}

function relatedThumb(y){
  if(y.image_url)return `<div class="related-thumb"><img src="${FI.esc(y.image_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.textContent='${FI.categoryIcons[(y.categories||[])[0]]||'◌'}'"></div>`;
  return `<div class="related-thumb" style="display:grid;place-items:center;font-size:23px">${FI.categoryIcons[(y.categories||[])[0]]||'◌'}</div>`;
}

function externalLinksHtml(b,compact=false){
  if(!FI.brandLinksFor)return'';
  const links=FI.brandLinksFor(b);
  const rows=compact?links.slice(0,3):links;
  return `<div class="brand-external-links ${compact?'compact':''}">${rows.map(link=>`<a class="brand-external-link ${link.direct?'official':'search'}" href="${FI.esc(link.url)}" target="_blank" rel="noopener noreferrer nofollow" title="${link.direct?'لینک رسمی ثبت‌شده':'جست‌وجوی پروفایل رسمی'}"><span class="network-icon">${link.icon}</span><span>${FI.esc(link.label)}</span><small>${link.direct?'رسمی':'جست‌وجو'}</small></a>`).join('')}</div>`;
}

function brandProfilesSection(x){
  const brands=x.brands||[];
  if(!brands.length||!FI.brandLinksFor)return'';
  return `<section class="section brand-profiles-section"><div class="brand-profiles-head"><div><h2>برندها و شبکه‌های رسمی</h2><p>وب‌سایت و شبکه‌های اجتماعی مرتبط با برندهای این خبر. «رسمی» یعنی لینک مستقیم ثبت شده؛ «جست‌وجو» برای مواردی است که هنوز آدرس مستقیم تأیید نشده است.</p></div></div><div class="brand-profile-grid">${brands.map(b=>{const logo=FI.brandLogo(b);return `<article class="brand-profile-card"><div class="brand-profile-title">${logo?`<img src="${FI.esc(logo)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`:''}<div><b>${FI.esc(b.fa||b.name)}</b><small>${FI.esc(b.name||'')}</small></div></div>${externalLinksHtml(b)}</article>`}).join('')}</div></section>`;
}

function brandDossier(x,items){
  const b=(x.brands||[])[0];
  if(!b)return'';
  const related=items.filter(y=>y.id!==x.id&&(y.brands||[]).some(z=>z.id===b.id));
  const recent=related.filter(y=>Date.now()-new Date(y.published_at)<30*864e5).length;
  const s=FI.brandStyles[b.id];
  const logo=FI.brandLogo(b);
  return `<div class="side-card brand-dossier"><h3>رادار برند</h3><div class="brand-head">${logo?`<img src="${logo}" alt="${FI.esc(b.fa||b.name)}" onerror="this.remove()">`:`<span class="brand-dot" style="${s?`background:${s[0]};color:${s[1]}`:''}">●</span>`}<div><b>${FI.esc(b.fa||b.name)}</b><small style="display:block;color:var(--muted)">${FI.faN(recent)} خبر در ۳۰ روز اخیر</small></div></div><p>وب‌سایت و شبکه‌های برند را باز کن یا همه خبرهای مرتبط با آن را ببین.</p>${externalLinksHtml(b,true)}<a class="pill-btn brand-news-btn" href="./?brand=${encodeURIComponent(b.id)}#feed">خبرهای این برند</a></div>`;
}

function render(x,items){
  document.title=`${x.title_fa} | رادار صنعت غذا`;
  const iran=FI.isIran(x);
  const cat=(x.categories||[])[0];
  const why=insights[cat]||'اهمیت این خبر به اثر احتمالی آن بر بازار، رقابت، عملیات یا تصمیم‌گیری در صنعت غذا مربوط می‌شود.';
  const cities=(x.geo?.cities||[]);
  const related=items
    .filter(y=>y.id!==x.id&&y.title_fa)
    .map(y=>[relatedScore(x,y),y])
    .filter(z=>z[0]>0)
    .sort((a,b)=>b[0]-a[0]||new Date(b[1].published_at)-new Date(a[1].published_at))
    .slice(0,7)
    .map(z=>z[1]);
  const facts=[
    ['منبع',FI.srcName(x)],
    ['کشور',FI.countryLabel(x)],
    ['شهر',cities.map(c=>c.fa).join('، ')||'—'],
    ['زمان انتشار',new Date(x.published_at).toLocaleString('fa-IR')],
    ['امتیاز اهمیت',FI.faN(x.relevance_score)],
    ['ارتباط با ایران',FI.faN(x.iran_relevance_score||0)]
  ];

  const summary=String(x.summary_fa||'').trim();
  const report=String(x.report_fa||'').trim();
  let lead=summary&&!nearDuplicate(summary,x.title_fa,.88)?summary:'';
  const showReport=materiallyRicher(report,lead||summary,x.title_fa);
  if(!lead&&report&&!showReport)lead=report;
  const points=distinctKeyPoints(x,lead,showReport?report:'');
  const coverage=reportCoverage(x);
  const edited=String(x.editorial?.status||'').startsWith('edited');
  const reportTitle=coverage==='خلاصه منبع'||coverage==='بر پایه خلاصه منبع'?'جزئیات فارسی خبر':'گزارش جامع فارسی';

  const reportSection=showReport?`<section class="section"><div class="report-head"><h2>${reportTitle}</h2><span class="coverage-badge ${coverage==='گسترده'?'wide':''}">پوشش: ${FI.esc(coverage)}</span>${edited?'<span class="editorial-badge">ویرایش خبری فارسی</span>':''}</div>${reportHtml(report)}${points.length?`<div class="key-facts">${points.map((p,i)=>`<div class="key-fact"><small>نکته ${FI.faN(i+1)}</small><b>${FI.richText(p)}</b></div>`).join('')}</div>`:''}</section>`:'';

  $('app').className='article-layout';
  $('app').innerHTML=`<article class="article ${iran?'iran':''}">
    <div class="article-hero">${FI.visual(x)}<div class="article-hero-overlay"><span class="country">${FI.esc(FI.countryLabel(x))}</span>${cities.map(c=>`<a class="city" href="./?city=${encodeURIComponent(c.id)}#feed">${FI.esc(c.fa)}</a>`).join('')}</div></div>
    <div class="eyebrow"><span>${FI.esc(FI.srcName(x))}</span><span>•</span><span>${FI.ago(x.published_at)}</span>${FI.brandMarks(x)}${FI.importance(x)}</div>
    <h1>${FI.richText(x.title_fa)}</h1>
    ${lead?`<p class="lead">${FI.richText(lead)}</p>`:''}
    <div class="chips">${(x.brands||[]).map(FI.brandChip).join('')}${(x.categories||[]).map(FI.categoryChip).join('')}</div>
    <div class="metrics"><div class="metric"><b>${FI.faN(x.relevance_score)}</b><span>اهمیت</span></div><div class="metric"><b>${FI.faN(x.iran_relevance_score||0)}</b><span>ارتباط با ایران</span></div><div class="metric"><b>${FI.faN((x.brands||[]).length)}</b><span>برند</span></div><div class="metric"><b>${FI.faN((x.categories||[]).length)}</b><span>حوزه تخصصی</span></div></div>
    ${reportSection}
    ${brandProfilesSection(x)}
    <section class="section"><div class="operator-box"><h3>برای مدیر یا اپراتور چه معنایی دارد؟</h3><p>${FI.esc(why)}</p></div></section>
    <section class="section"><h2>اطلاعات جغرافیایی</h2><p>${cities.length?`این خبر به ${cities.map(c=>`${c.fa} در استان ${c.province}`).join('، ')} مرتبط تشخیص داده شده است.`:`کشور اصلی این خبر ${FI.countryLabel(x)} تشخیص داده شده است.`}</p><p><a href="map.html?view=${iran?'iran':'world'}">مشاهده روی نقشه ↗</a></p></section>
    <section class="section"><h2>منبع اصلی</h2><div class="source-box"><b>${FI.esc(FI.srcName(x))}</b><div class="original">${FI.esc(x.title)}</div><a class="source-btn" href="${FI.esc(x.url)}" target="_blank" rel="noopener">خواندن اصل خبر ↗</a></div></section>
  </article>
  <aside class="article-rail"><div class="side-card"><h3>مشخصات خبر</h3>${facts.map(([k,v])=>`<div class="fact"><span>${FI.esc(k)}</span><b>${FI.esc(v)}</b></div>`).join('')}</div>${brandDossier(x,items)}<div class="side-card related"><h3>خبرهای مرتبط</h3>${related.length?related.map(y=>`<a class="related-card" href="${FI.storyUrl(y)}"><div><b>${FI.richText(y.title_fa)}</b><span>${FI.countryLabel(y)} · ${FI.ago(y.published_at)}</span></div>${relatedThumb(y)}</a>`).join(''):'<p>خبر مرتبط کافی پیدا نشد.</p>'}</div></aside>`;
}

async function boot(){
  if(!id)throw new Error('missing id');
  const r=await fetch('data/news.json?ts='+Date.now());
  const d=await r.json();
  const items=d.items||[];
  const x=items.find(y=>y.id===id);
  if(!x)throw new Error('not found');
  render(x,items);
}

boot().catch(()=>$('app').innerHTML='<div class="empty">این خبر پیدا نشد یا هنوز نسخه فارسی آن آماده نیست.</div>');