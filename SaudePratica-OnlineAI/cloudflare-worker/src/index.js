/**
 * SaúdePrática: private, authenticated online assistant endpoint.
 *
 * Deploy to a Cloudflare account the owner controls. No API credentials are
 * embedded in the Android APK. The online AI receives ONLY the question the
 * user typed after opting into online mode. Never accept patient records,
 * profiles, medical history, or instructions to mutate health data.
 */
const MODEL = "@cf/meta/llama-3.2-3b-instruct";
const SYSTEM = [
  "És o Assistente SaúdePrática.",
  "Responde em português de Portugal de forma breve, clara e útil.",
  "Ajuda a utilizar a aplicação, mas não inventes dados dos perfis, consultas ou medicamentos.",
  "Não faças diagnósticos, não sugiras doses nem alterações de tratamento.",
  "Para operações na app, lembra que a pessoa tem de confirmar a ficha nativa.",
  "Não afirmes ter acesso a dados do telemóvel; só recebeste a pergunta escrita.",
].join(" ");

function response(json, status=200) {
  return new Response(JSON.stringify(json), {
    status, headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store, private",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
      "access-control-allow-origin": "null",
    },
  });
}
function equalsSecret(a,b) {
  if (typeof a !== "string" || typeof b !== "string" || b.length < 24) return false;
  let difference = a.length ^ b.length;
  const len = Math.max(a.length,b.length);
  for(let i=0;i<len;i++)difference |= (a.charCodeAt(i)||0) ^ (b.charCodeAt(i)||0);
  return difference === 0;
}

export default {
  async fetch(request, env) {
    const pathname = new URL(request.url).pathname;
    if (pathname === "/health" && request.method === "GET") {
      return response({ok:true,service:"saudepratica-online-ai",ready:!!env.AI && !!env.SAUDE_AGENT_SHARED_TOKEN});
    }
    if (pathname !== "/v1/ask") return response({error:"not_found"},404);
    if(request.method !== "POST") return response({error:"method_not_allowed"},405);
    if (!env.AI || !env.SAUDE_AGENT_SHARED_TOKEN) {
      return response({error:"server_not_configured"},503);
    }
    const authorization = request.headers.get("authorization") || "";
    if (!authorization.startsWith("Bearer ") ||
        !equalsSecret(authorization.slice(7),env.SAUDE_AGENT_SHARED_TOKEN)) {
      return response({error:"unauthorized"},401);
    }
    if (!/application\/json/i.test(request.headers.get("content-type")||"")) {
      return response({error:"json_required"},415);
    }
    const length=Number(request.headers.get("content-length")||0);
    if(length>4096) return response({error:"too_large"},413);
    let body;
    try {
      const raw=await request.text();
      if(raw.length>2048) return response({error:"too_large"},413);
      body=JSON.parse(raw);
    } catch {
      return response({error:"invalid_json"},400);
    }
    // Explicit allowlist: do not accept record or profile objects.
    if (!body || typeof body !== "object" ||
        Object.keys(body).sort().join(",") !== "question" ||
        typeof body.question !== "string" ||
        body.question.trim().length<2 || body.question.length>700) {
      return response({error:"question_only_2_to_700_chars"},400);
    }
    try {
      const result=await env.AI.run(MODEL,{
        messages:[
          {role:"system",content:SYSTEM},
          {role:"user",content:body.question.trim()}
        ],
        max_tokens:240, temperature:0.3, stream:false
      });
      const answer=(typeof result?.response === "string" ? result.response : "").trim();
      if(!answer) return response({error:"model_empty"},502);
      return response({answer:answer.slice(0,2200),provider:"Workers AI"});
    }catch {
      // Never echo prompts, secret values, or provider internals into logs/responses.
      return response({error:"ai_temporarily_unavailable"},503);
    }
  }
};
