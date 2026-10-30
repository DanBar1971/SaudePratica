/** SaúdePrática central meal-photo analysis, Cloudflare Workers.
 * A single OPENAI_API_KEY secret is required; end users configure nothing.
 * No images, names, credentials, clinical records or response bodies are persisted.
 * A SQLite-backed Durable Object enforces 5 requests per IP and 200 total per UTC day.
 * Per-IP hash uses a random server-side pepper, not raw IPs.
 */
const MAX_IP_PER_DAY = 5;
const MAX_TOTAL_PER_DAY = 200;
const MAX_IMAGE_BASE64 = 3_200_000;
const HEADERS = { 'content-type':'application/json; charset=utf-8', 'cache-control':'no-store', 'x-content-type-options':'nosniff' };
const json = (obj, status=200) => new Response(JSON.stringify(obj),{status,headers:HEADERS});

export class DailyMealQuota {
  constructor(state, env) { this.state=state; }
  async fetch(request) {
    const auth = request.headers.get('X-Internal-Quota-Request');
    // DO only reachable via Worker namespace binding, not through public routing.
    if (auth !== 'internal') return json({error:'Forbidden'},403);
    const {day, ip} = await request.json();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || typeof ip!=='string' || ip.length>100) return json({error:'Invalid'},400);
    let salt=await this.state.storage.get('pepper');
    if (!salt) {
      salt=Array.from(crypto.getRandomValues(new Uint8Array(24)),v=>v.toString(16).padStart(2,'0')).join('');
      await this.state.storage.put('pepper',salt);
    }
    const bytes=new TextEncoder().encode(`${salt}:${day}:${ip}`);
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
    const userKey=`ip:${day}:${digest}`;
    const totalKey=`global:${day}`;
    const passed=await this.state.storage.transaction(async txn => {
      const dayTotal=(await txn.get(totalKey))||0;
      const userTotal=(await txn.get(userKey))||0;
      if (dayTotal >= MAX_TOTAL_PER_DAY || userTotal >= MAX_IP_PER_DAY) return {ok:false,global:dayTotal>=MAX_TOTAL_PER_DAY};
      await txn.put(totalKey,dayTotal+1);
      await txn.put(userKey,userTotal+1);
      return {ok:true};
    });
    return json(passed,passed.ok?200:429);
  }
}

const SYSTEM_PROMPT = `És um assistente alimentar em português de Portugal. Analisa apenas os alimentos visíveis e estima com prudência as quantidades e calorias. Não apresentes as quantidades como exatas. A fotografia não permite observar azeite, sal, molhos ou ingredientes escondidos, e não deve ser utilizada para garantir ausência de alergénios. Devolve EXCLUSIVAMENTE JSON válido: {"foods":[{"name":"arroz cozido","grams":130,"kcal":170}],"total_kcal":450,"protein_g":23,"carbs_g":45,"fat_g":18,"uncertainty_note":"Porções estimadas; confirme azeite, molhos e ingredientes."}. Se a imagem não contiver uma refeição visível, devolve foods vazio, 0 nutrientes e explica no uncertainty_note. Não faças recomendações médicas ou dietas.`;

export default {
  async fetch(req, env) {
    const url=new URL(req.url);
    if(url.pathname==='/health' && req.method==='GET') return json({service:'SaúdePrática Meal AI',ready:Boolean(env.OPENAI_API_KEY)});
    if(url.pathname!=='/analyze' || req.method!=='POST') return json({error:'Rota não encontrada'},404);
    if(!env.OPENAI_API_KEY) return json({error:'Serviço de IA não está ativo.'},503);
    if(!env.QUOTA) return json({error:'Limites de segurança indisponíveis.'},503);
    if((req.headers.get('content-type')||'').split(';')[0].trim().toLowerCase()!=='application/json') return json({error:'Usa application/json'},415);
    const size=Number(req.headers.get('content-length')||0);
    if(size>MAX_IMAGE_BASE64+1024) return json({error:'Imagem demasiado grande'},413);
    // Validate body before counting against quota; never print it.
    let image;
    try {
      const text=await req.text();
      if(text.length>MAX_IMAGE_BASE64+1024) throw Error('too big');
      image=JSON.parse(text);
      if(!['image/jpeg','image/png','image/webp'].includes(image.image_mime) ||
          typeof image.image_base64!=='string' ||
          !/^[-_A-Za-z0-9+/=\s]+$/.test(image.image_base64) ||
          image.image_base64.length < 500 || image.image_base64.length > MAX_IMAGE_BASE64) throw Error('invalid image');
    } catch {return json({error:'Fotografia inválida'},400)}
    const ip=req.headers.get('cf-connecting-ip')||'unknown';
    const day=new Date().toISOString().slice(0,10);
    try {
      const quota=env.QUOTA.get(env.QUOTA.idFromName('global-quotas-v1'));
      const reply=await quota.fetch('https://quota.internal/consume',{method:'POST',headers:{'X-Internal-Quota-Request':'internal','Content-Type':'application/json'},body:JSON.stringify({day,ip})});
      if(!reply.ok) return json({error:'Limite diário de análises atingido. Tenta amanhã.'},reply.status===429?429:503);
    } catch { return json({error:'Serviço temporariamente indisponível.'},503) }
    const request={
      model:env.OPENAI_MODEL||'gpt-4o-mini',
      max_tokens:700,temperature:0.2,response_format:{type:'json_object'},
      messages:[
        {role:'system',content:SYSTEM_PROMPT},
        {role:'user',content:[
          {type:'text',text:'Estima a composição e macros da refeição da fotografia; não assumes pesos exatos.'},
          {type:'image_url',image_url:{url:`data:${image.image_mime};base64,${image.image_base64}`,detail:'high'}}
        ]}
      ]
    };
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),38000);
    try {
      const response=await fetch('https://api.openai.com/v1/chat/completions',{
        method:'POST',headers:{'content-type':'application/json','authorization':`Bearer ${env.OPENAI_API_KEY}`},
        body:JSON.stringify(request),signal:controller.signal
      });
      if(!response.ok) return json({error:'A análise não está disponível neste momento.'},502);
      const responseBody=await response.json();
      const data=JSON.parse(responseBody.choices?.[0]?.message?.content||'{}');
      if(!Array.isArray(data.foods)||!Number.isFinite(Number(data.total_kcal))) throw Error('invalid response');
      const num=(n,max)=>Math.max(0,Math.min(max,Number(n)||0));
      return json({
        foods:data.foods.slice(0,20).map(f=>({name:String(f.name||'Alimento').slice(0,110),grams:num(f.grams,3000),kcal:num(f.kcal,10000)})),
        total_kcal:num(data.total_kcal,10000),protein_g:num(data.protein_g,1000),
        carbs_g:num(data.carbs_g,1000),fat_g:num(data.fat_g,1000),
        uncertainty_note:String(data.uncertainty_note||'Estimativa visual; confirma ingredientes e quantidades.').slice(0,500)
      });
    } catch {return json({error:'Não foi possível analisar esta fotografia.'},502)}
    finally {clearTimeout(timeout)}
  }
};