// Minimal DOM boundary double, not browser/accessibility qualification. Exercise
// the shipped request guard and truthful support observation wording.
import assert from 'node:assert/strict';
import widget from '../src/ochsner_bob/widget.js';
const nodes=[];
class Element {
  constructor(tag){this.tag=tag;this.tagName=tag.toUpperCase();this.textContent='';this.value='';this.children=[];this.listeners={};this.classList={add(){},toggle(){}};nodes.push(this);}
  append(child){this.children.push(child);}
  setAttribute(){}
  addEventListener(event,handler){this.listeners[event]=handler;}
  replaceChildren(){this.children=[];}
  matches(){return false;}
  click(){if(!this.disabled)this.onclick?.();}
}
globalThis.document={createElement:tag=>new Element(tag)};
const values=new Map();globalThis.sessionStorage={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};
globalThis.window={scrollY:0};globalThis.setInterval=()=>1;globalThis.clearInterval=()=>{};
let view={revision:0,state:'start',message:'Synthetic start',identity_status:'missing',preferences:{},providers:[{providerId:'p1',name:'Public fixture provider',specialty:'primary_care',locations:['downtown']}],slots:[],appointments:[],proposal:null,history:[],current_result:null,takeover:false,booking_blocked:false};
let releaseText, rejectAck=false;const commands=[],acks=[];
globalThis.fetch=async(url,request)=>{
  const path=new URL(url).pathname,body=request.body?JSON.parse(request.body):{};
  if(path==='/ack')acks.push(body.receipt);
  if(path==='/ack'&&rejectAck)return {ok:false,status:400};
  if(path==='/text')return new Promise(resolve=>{releaseText=()=>resolve({ok:true,json:async()=>({...view,stale:true,message:'Out of date'})});});
  if(path==='/command'){commands.push(body.action);view={...view,revision:view.revision+1,state:'help',message:'Help available'};}
  return {ok:true,json:async()=>path==='/create'?{token:'local-fixture-capability',view}:path==='/ack'?{}:view};
};
const named=text=>nodes.find(n=>n.tag==='button'&&n.textContent===text);
const flush=async()=>{for(let n=0;n<4;n++)await new Promise(setImmediate);};
if(process.argv.includes('--support-status')){
  for(const [control,lease,observed] of [['inactive',0,null],['inactive',0,view],['active',300,view],['inactive',0,view]]){
    nodes.length=0;values.clear();values.set('bob-v1-token','local-fixture-support');values.set('bob-v1-role','support');
    const mirror={patient:view,observed_patient:observed,last_observed:null,fresh:false,
      demo_support:'joined',control_status:control,lease_seconds:lease,known:[],missing:[],uncertain:[]};
    const requests=[];
    globalThis.fetch=async(url,request)=>{requests.push(new URL(url).pathname);return {ok:true,json:async()=>mirror};};
    const cleanup=widget.render({model:{get:()=>''},el:new Element('root')});await flush();
    assert.ok(nodes.some(n=>n.tag==='p'&&n.textContent===`Local participant: joined · demo control: ${control} · lease ${lease}s`),
      'pairing and temporary control must be labeled separately');
    assert.equal(named('Confirm appointment').disabled,true);
    assert.deepEqual(requests,['/state']);cleanup();
  }
}else if(process.argv.includes('--support-presentation')){
  const cases=[
    {name:'legacy receipt with no optional presentation',presentation:undefined,
      expected:'work status not reported, correction status not reported, confirmation not reported'},
    {name:'observed false',presentation:{notice:'domain',pending:false,dirty:false,can_confirm:false},
      expected:'not working, no unsent corrections, confirmation was disabled'},
    {name:'observed true',presentation:{notice:'domain',pending:true,dirty:true,can_confirm:true},
      expected:'working, unsent corrections, confirmation was enabled'},
    {name:'legacy three-field presentation',presentation:{notice:'domain',pending:false,dirty:true},
      expected:'not working, unsent corrections, confirmation not reported'},
    {name:'missing individual boolean observations',presentation:{notice:'domain',can_confirm:false},
      expected:'work status not reported, correction status not reported, confirmation was disabled'},
    {name:'non-boolean values are not observations',presentation:{notice:'domain',pending:1,dirty:'false',can_confirm:false},
      expected:'work status not reported, correction status not reported, confirmation was disabled'},
  ];
  for(const test of cases){
    nodes.length=0;values.clear();values.set('bob-v1-token','local-fixture-support');values.set('bob-v1-role','support');
    const receipt={revision:0,renderer:'bob-v1',visible:['message'],draft:{},focus:null,scroll:0,expanded:[],
      ...(test.presentation===undefined?{}:{presentation:test.presentation})};
    const originalReceipt=structuredClone(receipt);
    const mirror={patient:{...view,revision:1},observed_patient:{...view},last_observed:receipt,
      fresh:false,age_seconds:10,demo_support:'not_joined',lease_seconds:0,known:[],missing:['private identity'],uncertain:[]};
    const requests=[];
    globalThis.fetch=async(url,request)=>{
      requests.push({path:new URL(url).pathname,method:request.method});
      return {ok:true,json:async()=>mirror};
    };
    const cleanup=widget.render({model:{get:()=>''},el:new Element('root')});await flush();
    const context=nodes.find(n=>n.tag==='p'&&n.textContent.startsWith('Current backend context'));
    assert.ok(context,'actual support renderer did not display backend/observation context');
    assert.ok(context.textContent.includes(`Patient display: ${test.expected}.`),
      `${test.name}: ${context.textContent}`);
    assert.equal(named('Confirm appointment').disabled,true,`${test.name}: mirrored observation must not authorize confirmation`);
    assert.deepEqual(requests,[{path:'/state',method:'GET'}],`${test.name}: support rendering must remain effect-free`);
    assert.deepEqual(mirror.last_observed,originalReceipt,`${test.name}: rendering must not rewrite the receipt`);
    cleanup();
  }
}else{
const cleanup=widget.render({model:{get:()=>''},el:new Element('root')});
await named('Start independent patient').onclick();await flush();
const message=nodes.find(n=>n.id==='message');message.value='Find primary care downtown';
const pending=named('Send scheduling request').onclick();await flush();
assert.ok(releaseText,'public text request did not reach transport boundary');
assert.equal(named('Choose provider 1').disabled,true,'dynamic provider button remained enabled during a pending request');
await named('Help').onclick();await flush();
assert.deepEqual(commands,['help'],'pending model turn swallowed the visible local Help control');
assert.equal(nodes.find(n=>n.tag==='p'&&n.className?.startsWith('notice')).textContent,'Help available','main feedback hid the actionable response behind timing');
assert.equal(named('Confirm appointment').disabled,true,'pending/stale text enabled confirmation');
releaseText();await pending;await flush();
assert.deepEqual(acks.at(-1).presentation,{notice:'stale',pending:false,dirty:false,can_confirm:false},'actual renderer acknowledged ordinary backend state instead of its visible stale warning');
rejectAck=true;
await named('Help').onclick();await flush();
assert.ok(nodes.some(n=>n.tag==='p'&&n.textContent.includes('Patient · offline interpretation')),'acknowledgement rejection was mislabeled as a disconnected backend');
assert.ok(nodes.some(n=>n.tag==='p'&&n.textContent.includes('Support acknowledgement unavailable')),'patient was not told the support mirror may be stale');
cleanup();
}
