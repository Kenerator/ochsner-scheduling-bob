// Deliberately small feasibility surface. One DOM survives sidecar polling.
export default {render({el}) {
  const base = 'http://127.0.0.1:28451';
  let token = sessionStorage.getItem('bob-probe-token'), role = sessionStorage.getItem('bob-probe-role') || 'patient';
  let state, busy = false, closed = false;
  const node = (tag, text, parent=el) => {const n=document.createElement(tag); n.textContent=text; parent.append(n); return n;};
  node('h1', 'BOB • paired Marimo feasibility');
  node('p', 'Synthetic local probe only. No model, booking or handoff controls. Identity is not mirrored.');
  const status=node('p','Not connected'); status.setAttribute('role','status');
  const connect=node('section','');
  const button=(text,fn,parent=connect)=>{const b=node('button',text,parent); b.onclick=()=>fn().catch(()=>{status.textContent='Local operation unavailable. No effect was retried.';});return b;};
  const field=(label,parent=connect)=>{const l=node('label',label+' ',parent), i=node('input','',l); i.setAttribute('aria-label',label); return i;};
  async function call(path,body) {
    const response=await fetch(base+path,{method:body===undefined?'GET':'POST',cache:'no-store',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
    if(!response.ok) throw new Error('local request rejected'); return response.json();
  }
  const save=()=>{sessionStorage.setItem('bob-probe-token',token);sessionStorage.setItem('bob-probe-role',role);};
  button('Start independent patient',async()=>{const r=await call('/create',{});token=r.token;role='patient';save();await poll();});
  const grant=field('Pairing grant');
  button('Join as demo support',async()=>{const r=await call('/join',{grant:grant.value});token=r.token;role='support';grant.value='';save();await poll();});
  const pairing=node('output',''); pairing.setAttribute('aria-label','Current pairing grant');
  const controls=node('section','');
  button('Create one-use pairing grant',async()=>{pairing.textContent=(await call('/pair',{})).grant;},controls);
  async function command(action) {await call('/command',{action,data:{},revision:(state.patient||state).revision});await poll();}
  button('Help',()=>command('help'),controls);
  button('Take demo control',()=>command('takeover'),controls);
  button('Return patient control',()=>command('return'),controls);
  let heldRevision;
  const validation=node('p','');validation.setAttribute('role','status');
  button('Hold current revision for stale test',async()=>{heldRevision=(state.patient||state).revision;validation.textContent='Held revision '+heldRevision;},controls);
  button('Submit held Help revision',async()=>{const result=await call('/command',{action:'help',data:{},revision:heldRevision});validation.textContent=result.stale?result.message:'Held submission was current';await poll();},controls);
  const patient=node('section','');
  node('h2','Patient renderer',patient);
  const message=node('p','',patient), revision=node('p','',patient);
  const draft=field('Public unsent draft',patient); draft.id='message';
  const details=node('details','',patient); details.id='details';node('summary','Public detail disclosure',details);node('p','Disclosure state is semantic, not a pixel recording.',details);
  draft.value=sessionStorage.getItem('bob-probe-draft')||'';
  details.open=sessionStorage.getItem('bob-probe-expanded')==='1';
  draft.addEventListener('input',()=>{if(role==='patient')sessionStorage.setItem('bob-probe-draft',draft.value);});
  details.addEventListener('toggle',()=>{if(role==='patient')sessionStorage.setItem('bob-probe-expanded',details.open?'1':'0');});
  const observed=node('pre','',patient);
  const replayPanel=node('section','');node('h2','Effect-free replay probe',replayPanel);
  const replayOutput=node('pre','',replayPanel);let reference='';
  button('Start synthetic capture',async()=>{replayOutput.textContent=JSON.stringify(await call('/capture',{enabled:true,synthetic:true}));},replayPanel);
  button('Seal synthetic capture',async()=>{const report=await call('/capture',{enabled:false,synthetic:true});reference=report.reference;replayOutput.textContent=JSON.stringify(report);},replayPanel);
  button('Open recorded projection',async()=>{replayOutput.textContent=JSON.stringify(await call('/replay',{operation:'open',data:{reference}}));},replayPanel);
  button('Step recorded projection',async()=>{replayOutput.textContent=JSON.stringify(await call('/replay',{operation:'step',data:{}}));},replayPanel);
  function render(view, receipt) {
    message.textContent=view?.message||'No acknowledged screen yet';
    revision.textContent='Revision '+(view?.revision??'—')+' • '+(view?.takeover?'Demo support control':'Patient control');
    if(role==='support') {draft.value=receipt?.draft?.message||'';draft.disabled=true;details.open=(receipt?.expanded||[]).includes('details');}
    else draft.disabled=false;
    observed.textContent=role==='support'?JSON.stringify({draft:receipt?.draft,focus:receipt?.focus,scroll:receipt?.scroll,expanded:receipt?.expanded},null,2):'Unsent draft stays in this DOM while polling.';
  }
  async function ack() {
    if(!token||role!=='patient'||!state||closed) return;
    // AnyWidget may use a shadow root: document.activeElement is then its host.
    await call('/ack',{receipt:{revision:state.revision,renderer:'bob-v1',visible:['message','details'],draft:{message:draft.value},focus:draft.matches(':focus')?'message':null,scroll:Math.round(window.scrollY),expanded:details.open?['details']:[]}});
  }
  for(const event of ['input','focus','blur']) draft.addEventListener(event,()=>ack().catch(()=>{}));
  details.addEventListener('toggle',()=>ack().catch(()=>{}));
  async function poll() {
    if(!token||busy||closed) return; busy=true;
    try {state=await call('/state'); const support=role==='support';
      render(support?state.observed_patient:state,support?state.last_observed:undefined);
      status.textContent=support?('Demo support • '+(state.fresh?'fresh':'stale / missing')+' • age '+(state.age_seconds??'—')):'Patient • connected';
      await ack();
    } catch {status.textContent='Local connection unavailable. Refresh/reconnect performs no effects.';}
    finally {busy=false;}
  }
  poll(); const timer=setInterval(poll,500);
  return ()=>{closed=true;clearInterval(timer);};
}};
