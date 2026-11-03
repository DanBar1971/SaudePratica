import {test} from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const SECRET = "test-authorization-secret-123456789012345";
const env = {
  SAUDE_AGENT_SHARED_TOKEN: SECRET,
  AI: {
    async run(model,options) {
      assert.match(model,/^@cf\//);
      assert.equal(options.messages.length,2);
      assert.equal(options.messages[1].content,"Como faço um backup?");
      return {response:"Abre Opções e escolhe Backup."};
    }
  }
};
const call=(url="/v1/ask", options={})=>worker.fetch(
  new Request("https://unit-test.workers.dev"+url,options),env
);
test("must authenticate before invoking model",async()=>{
  const x=await call("/v1/ask",{method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({question:"Como faço um backup?"})});
  assert.equal(x.status,401);
});
test("only accepts typed question, never profile or medical records",async()=>{
  const x=await call("/v1/ask",{method:"POST",
    headers:{"content-type":"application/json",authorization:"Bearer "+SECRET},
    body:JSON.stringify({question:"Como faço um backup?",profile:{id:"abc"},medications:["X"]})});
  assert.equal(x.status,400);
});
test("runs Workers AI for authorized question",async()=>{
  const x=await call("/v1/ask",{method:"POST",
    headers:{"content-type":"application/json",authorization:"Bearer "+SECRET},
    body:JSON.stringify({question:"Como faço um backup?"})});
  assert.equal(x.status,200);
  assert.equal((await x.json()).answer,"Abre Opções e escolhe Backup.");
  assert.match(x.headers.get("cache-control"),/no-store/);
});
test("rejects invalid endpoint and oversize input",async()=>{
  assert.equal((await call("/admin",{method:"GET"})).status,404);
  const x=await call("/v1/ask",{method:"POST",
    headers:{"content-type":"application/json",authorization:"Bearer "+SECRET},
    body:JSON.stringify({question:"x".repeat(800)})});
  assert.equal(x.status,400);
});
test("without secret or binding, fails closed",async()=>{
  const x=await worker.fetch(new Request("https://unit-test.workers.dev/v1/ask",
   {method:"POST",headers:{"content-type":"application/json",authorization:"Bearer "+SECRET},
     body:'{"question":"Olá, saúde"}'}),{AI:env.AI});
  assert.equal(x.status,503);
});
