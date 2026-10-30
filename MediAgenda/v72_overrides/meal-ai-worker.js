/** SaúdePrática meal-photo AI proxy — Cloudflare Worker.
 * Set secrets: OPENAI_API_KEY and APP_TOKEN; optional var OPENAI_MODEL (default gpt-4o-mini).
 * Deploy HTTPS Worker; then configure its full /analyze URL and APP_TOKEN inside SaúdePrática.
 * Never expose OPENAI_API_KEY in Android, GitHub, or the browser.
 */
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname !== '/analyze' || req.method !== 'POST') {
      return new Response(JSON.stringify({error:'Rota não encontrada'}), {status:404,headers:{'content-type':'application/json'}});
    }
    const authorization = req.headers.get('authorization') || '';
    // The app token is not an OpenAI key. Rotate it when needed.
    if (!env.APP_TOKEN || !authorization.startsWith('Bearer ') || authorization.slice(7) !== env.APP_TOKEN) {
      return new Response(JSON.stringify({error:'Não autorizado'}),{status:401,headers:{'content-type':'application/json'}});
    }
    if (!env.OPENAI_API_KEY) return new Response(JSON.stringify({error:'Serviço por configurar'}),{status:503});
    const size = Number(req.headers.get('content-length') || 0);
    if (size > 3_500_000) return new Response(JSON.stringify({error:'Imagem demasiado grande'}),{status:413});
    let input;
    try {
      input = await req.json();
      if (!['image/jpeg','image/png','image/webp'].includes(input.image_mime)
        || typeof input.image_base64 !== 'string' || input.image_base64.length > 3_500_000
        || input.image_base64.length < 500) throw Error('Imagem inválida');
    } catch {
      return Response.json({error:'Fotografia inválida'}, {status:400});
    }
    const prompt = `És um assistente alimentar em português de Portugal. Examina apenas a refeição visível.
A fotografia não permite determinar as calorias com precisão. Identifica os alimentos e estima porções em gramas e nutrientes.
Considera que azeite, molhos, bebidas e ingredientes escondidos podem estar ausentes; não inventes alergénios nem faças afirmações médicas.
Responde EXCLUSIVAMENTE com JSON válido, sem markdown, no formato:
{"foods":[{"name":"arroz cozido","grams":130,"kcal":170}],"total_kcal":450,"protein_g":23,"carbs_g":45,"fat_g":18,"uncertainty_note":"Porções e gorduras de confeção são estimativas; confirme os ingredientes."}
Usa valores plausíveis, não apresente falsa precisão. Se não reconhecer comida, retorna foods vazio, 0 nutrientes e explica.`;
    const request = {
      model:env.OPENAI_MODEL || 'gpt-4o-mini',
      max_tokens:650,
      temperature:0.2,
      response_format:{type:'json_object'},
      messages:[
        {role:'system',content:prompt},
        {role:'user',content:[
          {type:'text',text:'Estima a composição desta refeição. Não assumes peso exato.'},
          {type:'image_url',image_url:{url:`data:${input.image_mime};base64,${input.image_base64}`,detail:'high'}}
        ]}
      ]
    };
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),38000);
    try {
      const response=await fetch('https://api.openai.com/v1/chat/completions', {
        method:'POST',
        headers:{'content-type':'application/json','authorization':`Bearer ${env.OPENAI_API_KEY}`},
        body:JSON.stringify(request),signal:controller.signal
      });
      if(!response.ok){
        return Response.json({error:`Falha temporária do serviço de IA (HTTP ${response.status})`},{status:502});
      }
      const result=await response.json();
      const json=JSON.parse(result.choices?.[0]?.message?.content || '{}');
      if (!Array.isArray(json.foods) || typeof json.total_kcal !== 'number') {
        throw new Error('Formato inesperado');
      }
      const cleaned={
        foods:json.foods.slice(0,20).map(food=>({
          name:String(food.name||'Alimento').slice(0,110),
          grams:Number(food.grams)||0,kcal:Number(food.kcal)||0
        })),
        total_kcal:Math.max(0,Math.min(10000,Number(json.total_kcal)||0)),
        protein_g:Math.max(0,Math.min(1000,Number(json.protein_g)||0)),
        carbs_g:Math.max(0,Math.min(1000,Number(json.carbs_g)||0)),
        fat_g:Math.max(0,Math.min(1000,Number(json.fat_g)||0)),
        uncertainty_note:String(json.uncertainty_note||'Estimativa visual: confirme porções e ingredientes.').slice(0,500)
      };
      return Response.json(cleaned,{headers:{'cache-control':'no-store'}});
    } catch(e) {
      return Response.json({error:'Não foi possível analisar a fotografia.'},{status:502,headers:{'cache-control':'no-store'}});
    } finally {clearTimeout(timer)}
  }
};