(()=>{
  const P={
    mcdonalds:{website:'https://www.mcdonalds.com/',instagram:'https://www.instagram.com/mcdonalds/',youtube:'https://www.youtube.com/@McDonalds',x:'https://x.com/McDonalds'},
    starbucks:{website:'https://www.starbucks.com/',instagram:'https://www.instagram.com/starbucks/',youtube:'https://www.youtube.com/@Starbucks',x:'https://x.com/Starbucks'},
    yum_brands:{website:'https://www.yum.com/',linkedin:'https://www.linkedin.com/company/yum-brands/'},
    kfc:{website:'https://www.kfc.com/',instagram:'https://www.instagram.com/kfc/',youtube:'https://www.youtube.com/@KFC',x:'https://x.com/kfc'},
    taco_bell:{website:'https://www.tacobell.com/',instagram:'https://www.instagram.com/tacobell/',youtube:'https://www.youtube.com/@TacoBell',x:'https://x.com/tacobell'},
    pizza_hut:{website:'https://www.pizzahut.com/',instagram:'https://www.instagram.com/pizzahut/',youtube:'https://www.youtube.com/@PizzaHut',x:'https://x.com/pizzahut'},
    burger_king:{website:'https://www.bk.com/',instagram:'https://www.instagram.com/burgerking/',x:'https://x.com/BurgerKing'},
    rbi:{website:'https://www.rbi.com/',linkedin:'https://www.linkedin.com/company/restaurant-brands-international/'},
    wendys:{website:'https://www.wendys.com/',instagram:'https://www.instagram.com/wendys/',x:'https://x.com/Wendys'},
    dominos:{website:'https://www.dominos.com/',instagram:'https://www.instagram.com/dominos/',x:'https://x.com/dominos'},
    chipotle:{website:'https://www.chipotle.com/',instagram:'https://www.instagram.com/chipotle/'},
    cava:{website:'https://cava.com/',instagram:'https://www.instagram.com/cava/'},
    sweetgreen:{website:'https://www.sweetgreen.com/',instagram:'https://www.instagram.com/sweetgreen/'},
    panera:{website:'https://www.panerabread.com/',instagram:'https://www.instagram.com/panerabread/'},
    subway:{website:'https://www.subway.com/',instagram:'https://www.instagram.com/subway/'},
    chickfila:{website:'https://www.chick-fil-a.com/',instagram:'https://www.instagram.com/chickfila/'},
    popeyes:{website:'https://www.popeyes.com/',instagram:'https://www.instagram.com/popeyes/'},
    dunkin:{website:'https://www.dunkin.com/',instagram:'https://www.instagram.com/dunkin/'},
    shake_shack:{website:'https://shakeshack.com/',instagram:'https://www.instagram.com/shakeshack/'},
    wingstop:{website:'https://www.wingstop.com/',instagram:'https://www.instagram.com/wingstop/'},
    arbys:{website:'https://www.arbys.com/',instagram:'https://www.instagram.com/arbys/'},
    blaze_pizza:{website:'https://www.blazepizza.com/',instagram:'https://www.instagram.com/blazepizza/'},
    mountain_mikes:{website:'https://www.mountainmikespizza.com/'},
    juice_it_up:{website:'https://juiceitup.com/'},
    wonder:{website:'https://www.wonder.com/'},
    doordash:{website:'https://www.doordash.com/',instagram:'https://www.instagram.com/doordash/',youtube:'https://www.youtube.com/@DoorDash'},
    uber_eats:{website:'https://www.ubereats.com/',instagram:'https://www.instagram.com/ubereats/',youtube:'https://www.youtube.com/@UberEats'},
    grubhub:{website:'https://www.grubhub.com/',instagram:'https://www.instagram.com/grubhub/'},
    toast:{website:'https://pos.toasttab.com/',linkedin:'https://www.linkedin.com/company/toast-inc/'},
    olo:{website:'https://www.olo.com/',linkedin:'https://www.linkedin.com/company/olo/'},
    ncr_voyix:{website:'https://www.ncrvoyix.com/',linkedin:'https://www.linkedin.com/company/ncrvoyix/'},
    par_technology:{website:'https://partech.com/',linkedin:'https://www.linkedin.com/company/par-technology/'},
    sysco:{website:'https://www.sysco.com/',linkedin:'https://www.linkedin.com/company/sysco/'},
    us_foods:{website:'https://www.usfoods.com/',linkedin:'https://www.linkedin.com/company/us-foods/'},
    performance_food_group:{website:'https://www.pfgc.com/',linkedin:'https://www.linkedin.com/company/performance-food-group/'},
    rational:{website:'https://www.rational-online.com/'},
    middleby:{website:'https://www.middleby.com/'},
    welbilt:{website:'https://www.welbilt.com/'},
    unox:{website:'https://www.unox.com/'},
    nestle:{website:'https://www.nestle.com/',instagram:'https://www.instagram.com/nestle/',youtube:'https://www.youtube.com/@Nestle'},
    pepsico:{website:'https://www.pepsico.com/',instagram:'https://www.instagram.com/pepsi/',youtube:'https://www.youtube.com/@Pepsi'},
    coca_cola:{website:'https://www.coca-colacompany.com/',instagram:'https://www.instagram.com/cocacola/',youtube:'https://www.youtube.com/@CocaCola'},
    mars:{website:'https://www.mars.com/',linkedin:'https://www.linkedin.com/company/mars/'},
    snickers:{website:'https://www.snickers.com/',instagram:'https://www.instagram.com/snickers/'},
    southern_glazers:{website:'https://www.southernglazers.com/',linkedin:'https://www.linkedin.com/company/southern-glazer-s-wine-spirits/'},
    mondelez:{website:'https://www.mondelezinternational.com/',linkedin:'https://www.linkedin.com/company/mondelezinternational/'},
    kraft_heinz:{website:'https://www.kraftheinzcompany.com/',linkedin:'https://www.linkedin.com/company/the-kraft-heinz-company/'},
    tyson_foods:{website:'https://www.tysonfoods.com/',linkedin:'https://www.linkedin.com/company/tyson-foods/'},
    general_mills:{website:'https://www.generalmills.com/',linkedin:'https://www.linkedin.com/company/general-mills/'},
    kalleh:{website:'https://kalleh.com/'},
    solico:{website:'https://solico-group.com/'},
    mihan_dairy:{website:'https://mihan-food.com/'},
    snappfood:{website:'https://snappfood.ir/'},
    sunich:{website:'https://sunich.org/'},
    mahram:{website:'https://mahramco.com/'},
    mazmaz:{website:'https://mazmazgroup.com/'}
  };
  const q=s=>encodeURIComponent(String(s||'').trim());
  const google=(domain,name)=>`https://www.google.com/search?q=${q(`site:${domain} "${name}" official`)}`;
  FI.brandProfiles=P;
  FI.brandProfile=b=>P[b?.id]||{};
  FI.brandLinksFor=b=>{
    const name=b?.name||b?.fa||b?.id||'';
    const p=FI.brandProfile(b);
    return [
      {id:'website',label:p.website?'وب‌سایت رسمی':'یافتن وب‌سایت رسمی',icon:'🌐',url:p.website||`https://www.google.com/search?q=${q(`${name} official website`)}`,direct:Boolean(p.website)},
      {id:'instagram',label:'اینستاگرام',icon:'◎',url:p.instagram||google('instagram.com',name),direct:Boolean(p.instagram)},
      {id:'youtube',label:'یوتیوب',icon:'▶',url:p.youtube||`https://www.youtube.com/results?search_query=${q(`${name} official`)}`,direct:Boolean(p.youtube)},
      {id:'linkedin',label:'لینکدین',icon:'in',url:p.linkedin||`https://www.linkedin.com/search/results/companies/?keywords=${q(name)}`,direct:Boolean(p.linkedin)},
      {id:'x',label:'X',icon:'𝕏',url:p.x||`https://x.com/search?q=${q(`${name} official`)}`,direct:Boolean(p.x)},
      {id:'tiktok',label:'تیک‌تاک',icon:'♪',url:p.tiktok||google('tiktok.com',name),direct:Boolean(p.tiktok)}
    ];
  };
})();
