(()=>{
  const nativeFetch=window.fetch.bind(window);
  const isTurkey=x=>x?.market==='turkey'||x?.country==='TR'||x?.source?.country==='TR'||x?.region==='TR'||x?.geo?.primary_country?.code==='TR'||(x?.geo?.countries||[]).some(c=>c.code==='TR')||(x?.brands||[]).some(b=>b.market==='turkey');
  window.fetch=async(input,init)=>{
    const response=await nativeFetch(input,init);
    const target=typeof input==='string'?input:(input?.url||'');
    if(!target.includes('data/news.json'))return response;
    try{
      const data=await response.clone().json();
      data.items=(data.items||[]).filter(isTurkey);
      data.count=data.items.length;
      return new Response(JSON.stringify(data),{
        status:response.status,
        statusText:response.statusText,
        headers:{'Content-Type':'application/json; charset=utf-8'}
      });
    }catch{return response}
  };
})();
