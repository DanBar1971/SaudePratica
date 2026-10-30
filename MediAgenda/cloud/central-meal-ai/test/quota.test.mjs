import test from 'node:test';
import assert from 'node:assert/strict';
import {DailyMealQuota} from '../worker.mjs';
class Store {
 constructor(){this.m=new Map()}
 async get(k){return this.m.get(k)}
 async put(k,v){this.m.set(k,v)}
 async transaction(action){return action(this)}
}
const state={storage:new Store()};
const obj=new DailyMealQuota(state,{});
const call=(ip,day='2026-10-23')=>obj.fetch(new Request('https://quota.internal/consume',{
 method:'POST',headers:{'X-Internal-Quota-Request':'internal'},body:JSON.stringify({day,ip})
}));
test('five requests permitted per IP per UTC day, sixth blocked', async ()=>{
 for(let i=0;i<5;i++) assert.equal((await call('192.0.2.1')).status,200);
 assert.equal((await call('192.0.2.1')).status,429);
 assert.equal((await call('192.0.2.2')).status,200);
 assert.equal((await call('192.0.2.1','2026-10-24')).status,200);
});
test('raw IP not stored', async ()=>{ assert.ok([...state.storage.m.keys()].every(x=>!x.includes('192.0.2'))) });