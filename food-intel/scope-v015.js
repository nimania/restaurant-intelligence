(()=>{
  const currentScope=()=>{
    const scope=document.body?.dataset?.feedScope||'world';
    return ['iran','turkey','latest'].includes(scope)?scope:'world';
  };
  FI.feedScope=currentScope;
  FI.feedBase=()=>currentScope()==='iran'?'iran.html':currentScope()==='turkey'?'turkey.html':currentScope()==='latest'?'latest.html':'explore.html';
  FI.feedHref=(key,val)=>{
    const p=new URLSearchParams();
    if(key&&val!==undefined&&val!==null&&val!=='')p.set(key,val);
    const q=p.toString();
    return `${FI.feedBase()}${q?'?'+q:''}${q?'#feed':''}`;
  };
  FI.brandChip=b=>{
    const s=FI.brandStyles[b.id];
    const style=s?`style="background:${s[0]};color:${s[1]};border-color:${s[2]}"`:'';
    const logo=FI.brandLogo(b);
    return `<a class="chip brand-chip" href="${FI.feedHref('brand',b.id)}" ${style}>${logo?`<img src="${FI.esc(logo)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`:''}<span>${FI.esc(b.fa||b.name)}</span></a>`;
  };
  FI.brandMark=b=>{
    const s=FI.brandStyles[b.id],bg=s?.[0]||'var(--panel-2)',fg=s?.[1]||'var(--text)',logo=FI.brandLogo(b),label=b.fa||b.name||'';
    return `<a class="brand-mark" href="${FI.feedHref('brand',b.id)}" title="${FI.esc(label)}" style="--brand-bg:${bg};--brand-fg:${fg}">${logo?`<img src="${FI.esc(logo)}" alt="${FI.esc(label)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove();this.parentElement.classList.add('no-logo')">`:''}<span>${FI.esc(label.slice(0,1))}</span></a>`;
  };
  FI.categoryChip=c=>`<a class="chip category-chip" href="${FI.feedHref('category',c)}"><span>${FI.categoryIcons[c]||'•'}</span>${FI.esc(FI.labels[c]||c)}</a>`;
  FI.setParam=(key,val)=>{location.href=FI.feedHref(key,val)};
})();
