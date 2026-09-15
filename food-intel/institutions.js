FI.bindTheme();
const institutions=[
  {name:'سازمان غذا و دارو',type:'government',typeFa:'دولتی / تنظیم‌گر',icon:'🏛️',scope:'ایمنی، مجوز، استاندارد و نظارت بر غذا و فرآورده‌ها',url:'https://www.fda.gov.ir/',news:'سازمان غذا و دارو'},
  {name:'وزارت جهاد کشاورزی',type:'government',typeFa:'دولتی / سیاست‌گذار',icon:'🌾',scope:'کشاورزی، مواد اولیه، زنجیره تأمین و سیاست‌های تولید',url:'https://www.maj.ir/',news:'وزارت جهاد کشاورزی'},
  {name:'وزارت صنعت، معدن و تجارت',type:'government',typeFa:'دولتی / سیاست‌گذار',icon:'⚙️',scope:'صنعت، تجارت، تولید و مقررات بنگاه‌های صنعتی',url:'https://www.mimt.gov.ir/',news:'وزارت صمت'},
  {name:'اتاق اصناف ایران',type:'guild',typeFa:'صنفی / ملی',icon:'🏪',scope:'اصناف، اتحادیه‌ها، مقررات صنفی و فضای کسب‌وکار',url:'https://otaghasnafeiran.ir/',news:'اتاق اصناف'},
  {name:'اتاق بازرگانی، صنایع، معادن و کشاورزی ایران',type:'chamber',typeFa:'اتاق / بخش خصوصی',icon:'🏢',scope:'تجارت، تشکل‌ها، سیاست‌گذاری بخش خصوصی و صادرات',url:'https://iccima.ir/',news:'اتاق بازرگانی ایران'},
  {name:'کانون انجمن‌های صنایع غذایی ایران',type:'association',typeFa:'تشکل تخصصی',icon:'🍽️',scope:'شبکه انجمن‌های تخصصی صنایع غذایی و پیگیری مسائل صنفی',url:'https://ifif.ir/',news:'کانون انجمن های صنایع غذایی'},
  {name:'انجمن صنایع فرآورده‌های گوشتی ایران',type:'association',typeFa:'انجمن تخصصی',icon:'🥩',scope:'صنایع فرآورده‌های گوشتی، کیفیت، مقررات و منافع اعضا',url:'https://mppso.com/',news:'انجمن صنایع فرآورده های گوشتی'},
  {name:'انجمن واردکنندگان مواد غذایی و آشامیدنی',type:'association',typeFa:'انجمن تخصصی',icon:'📦',scope:'واردات مواد غذایی و آشامیدنی، مقررات و لجستیک',url:'https://fbia.ir/',news:'انجمن واردکنندگان مواد غذایی'},
  {name:'انجمن واردکنندگان برنج ایران',type:'association',typeFa:'انجمن تخصصی',icon:'🍚',scope:'بازار برنج، واردات، تنظیم بازار و بخشنامه‌های تخصصی',url:'https://www.iria.org.ir/',news:'انجمن واردکنندگان برنج'},
  {name:'انجمن متخصصین علوم و صنایع غذایی ایران',type:'scientific',typeFa:'علمی / تخصصی',icon:'🧪',scope:'علوم و فناوری غذا، آموزش و شبکه متخصصان',url:'https://ifsta.ir/',news:'انجمن متخصصین علوم و صنایع غذایی'}
];
const $=id=>document.getElementById(id);
function card(x){return `<article class="institution-card"><div class="institution-top"><div><h2>${FI.esc(x.name)}</h2><div class="institution-meta"><span>${FI.esc(x.typeFa)}</span><span>ایران</span></div></div><div class="institution-icon">${x.icon}</div></div><p>${FI.esc(x.scope)}</p><div class="institution-actions"><a href="${FI.esc(x.url)}" target="_blank" rel="noopener">وب‌سایت رسمی ↗</a><a href="iran.html?q=${encodeURIComponent(x.news)}#feed">خبرهای مرتبط</a></div></article>`}
function render(){const q=($('institutionSearch').value||'').trim().toLowerCase();const type=$('institutionType').value;const rows=institutions.filter(x=>(!type||x.type===type)&&(!q||[x.name,x.typeFa,x.scope].join(' ').toLowerCase().includes(q)));$('institutionCount').textContent=`${FI.faN(rows.length)} نهاد`;$('institutionGrid').innerHTML=rows.length?rows.map(card).join(''):'<div class="empty">موردی با این فیلتر پیدا نشد.</div>'}
$('institutionSearch').addEventListener('input',render);$('institutionType').addEventListener('change',render);render();
