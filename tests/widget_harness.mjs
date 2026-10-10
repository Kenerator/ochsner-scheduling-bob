// Minimal DOM boundary double, not browser/accessibility qualification. Exercise
// the shipped request guard: a pending model turn must not swallow local Help.
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
const cleanup=widget.render({model:{get:()=>''},el:new Element('root')});
const named=text=>nodes.find(n=>n.tag==='button'&&n.textContent===text);
const flush=async()=>{for(let n=0;n<4;n++)await new Promise(setImmediate);};
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
