/**
 * Central Gemini meal analyzer. The Android app does not store a Gemini API key.
 * Google receives the photo only after the user explicitly approves sending it.
 * Photos, responses and user identities are not logged or stored by this Worker.
 * The IP-derived, peppered daily quota is implemented in the existing Durable Object.
 * This endpoint must be deployed and given GEMINI_API_KEY by the app maintainer.
 */
export { DailyMealQuota } from './worker.mjs';
const JSON_HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'cache-control': 'no-store',
  'x-content-type-options': 'nosniff',
};
const result = (data,status=200) => new Response(JSON.stringify(data),{status,headers:JSON_HEADERS});
const cap=(v,lo,hi)=>Number.isFinite(Number(v)) ? Math.max(lo,Math.min(hi,Number(v))) : 0;
const PROMPT=`Analisa a fotografia de uma REFEIÇÃO COMPLETA em português de Portugal.
Identifica separadamente TODOS os alimentos realmente visíveis: prato principal,
acompanhamentos, salada, sopa, pão, bebida e sobremesa, quando houver evidência.
Nunca assumes que a imagem mostra uma única receita ou prato. Não inventes molhos,
azeite, alergénios ou ingredientes invisíveis. Dá nomes portugueses (ex.: lombo de
porco, arroz cozido, batata frita, esparregado, salada mista, sopa de legumes,
bolo de iogurte) SÓ SE FIZEREM SENTIDO para esta imagem concreta; os exemplos
não são uma lista obrigatória. Usa porções aproximadas e estimativas por alimento.
Responde somente JSON válido:
{"foods":[{"name":"arroz cozido","grams":150,"kcal":195,"protein_g":4,
"carbs_g":42,"fat_g":0.5}],"total_kcal":195,
"uncertainty_note":"Porções aproximadas; não é possível medir óleo ou molho escondido."}
Se não houver comida legível, devolve foods=[] e explica incerteza.
Evita certezas clínicas, conselhos dietéticos e estimativas exageradamente exatas.`;

function normalize(body) {
  const entries=Array.isArray(body?.foods)?body.foods:[];
  const foods=[];
  for(const item of entries.slice(0,18)){
    if(!item||typeof item.name!=='string')continue;
    const name=item.name.trim().slice(0,90);
    const grams=cap(item.grams,0,2500),kcal=cap(item.kcal,0,5000);
    if(!name||grams<=0||kcal<0)continue;
    foods.push({name,grams:Math.round(grams),kcal:Math.round(kcal),
      protein_g:cap(item.protein_g,0,1000),
      carbs_g:cap(item.carbs_g,0,1000),
      fat_g:cap(item.fat_g,0,1000)});
  }
  const total_kcal=foods.reduce((a,b)=>a+b.kcal,0);
  if(!foods.length || total_kcal>10000 || total_kcal<=0)
    return {error:'Não foi possível identificar uma refeição completa. Usa o modo manual.'};
  return {foods,total_kcal,
    uncertainty_note:String(body.uncertainty_note||'Porções estimadas visualmente.').slice(0,300)};
}

export default {
  async fetch(req,env) {
    const path=new URL(req.url).pathname;
    if(path==='/health'&&req.method==='GET')
      return result({service:'SaúdePrática Gemini Meal AI',ready:Boolean(env.GEMINI_API_KEY && env.QUOTA)});
    if(path!=='/analyze'||req.method!=='POST') return result({error:'Rota não encontrada.'},404);
    if(!env.GEMINI_API_KEY||!env.QUOTA)
      return result({error:'O serviço Gemini ainda não está ativo. Usa o registo manual.'},503);
    if(!String(req.headers.get('content-type')||'').startsWith('application/json'))
      return result({error:'Formato de pedido inválido.'},415);
    const claimed=Number(req.headers.get('content-length')||0);
    if(claimed>3_500_000)return result({error:'Fotografia demasiado grande.'},413);
    let b;
    try{
      const text=await req.text();
      if(text.length>3_500_000)throw Error('size');
      b=JSON.parse(text);
      if(b.image_mime!=='image/jpeg'||typeof b.image_base64!=='string'||
          b.image_base64.length<500||b.image_base64.length>3_400_000||
          !/^[A-Za-z0-9+/=]+$/.test(b.image_base64))throw Error('jpeg');
    }catch{return result({error:'A fotografia enviada não é válida.'},400);}
    try{
      const quota=env.QUOTA.get(env.QUOTA.idFromName('global-quotas-v1'));
      const q=await quota.fetch('https://quota.internal/consume',{
        method:'POST',headers:{'X-Internal-Quota-Request':'internal','Content-Type':'application/json'},
        body:JSON.stringify({day:new Date().toISOString().slice(0,10),
          ip:req.headers.get('cf-connecting-ip')||'unknown'})});
      if(!q.ok)return result({error:'Limite diário de análises atingido. Usa modo manual.'},429);
    }catch{return result({error:'Controlo de limites indisponível.'},503);}

    // The upstream key is server-only. Never include it in error messages or logs.
    const model=env.GEMINI_MODEL||'gemini-3.1-flash-lite';
    if(!/^gemini-[a-z0-9.-]{3,45}$/.test(model))
      return result({error:'Modelo de análise não configurado.'},503);
    const request={contents:[{role:'user',parts:[{text:PROMPT},
      {inlineData:{mimeType:'image/jpeg',data:b.image_base64}}]}],
      generationConfig:{temperature:0.1,responseMimeType:'application/json',maxOutputTokens:1800}};
    const abort=new AbortController();
    const timer=setTimeout(()=>abort.abort(),38000);
    try{
      const upstream=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,{
        method:'POST',signal:abort.signal,
        headers:{'content-type':'application/json','x-goog-api-key':env.GEMINI_API_KEY},
        body:JSON.stringify(request)});
      if(!upstream.ok){
        if(upstream.status===429)return result({error:'Limite gratuito Gemini atingido; tenta mais tarde.'},429);
        return result({error:'Gemini indisponível; usa o modo manual.'},503);
      }
      const answer=await upstream.json();
      const text=(answer.candidates?.[0]?.content?.parts||[]).map(x=>x.text||'').join('');
      if(text.length>30000)throw Error('oversize');
      const normalized=normalize(JSON.parse(text));
      if(normalized.error)return result(normalized,422);
      return result(normalized);
    }catch{return result({error:'Não foi possível analisar. O modo manual continua disponível.'},503);}
    finally{clearTimeout(timer);}
  }
};