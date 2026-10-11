// Pure presentation shared by patient and read-only support. Never authorizes I/O.
export function presentation(view, role='patient') {
  const proposal=view?.proposal, slot=proposal?.slot;
  const provider=(view?.providers||[]).find(p=>p.providerId===slot?.providerId);
  const outcome=r=>r?`${r.kind}: ${r.status}`:'No current attempt';
  return {canConfirm:role==='patient' && !!proposal?.nonce && proposal.revision===view.revision && view.identity_status==='verified' && !view.takeover && !view.booking_blocked,
    summary:slot?[slot.startTime,slot.specialty,slot.location,provider?.name||slot.providerId].join(' • '):'No current proposal',
    current:outcome(view?.current_result),history:(view?.history||[]).map(outcome)};
}

export function semanticReceipt(revision,draft,focus,scroll,expanded,presentation) {
  return {revision,renderer:'bob-v1',visible:['message','specialty','location','start_date','end_date','local-controls','developer'],draft,focus,scroll,expanded,...(presentation?{presentation}:{})};
}

export function mirroredNotice(receipt,view) {
  const messages={none:'',working:'Working locally… No action will be retried automatically.',ready:'Ready',stale:'This screen is out of date. Review the current screen before acting.',
    pairing:'Share this one-use grant only with the other local demo tab. It expires in five minutes.',grant:'This local grant is missing, expired, or not permitted. Start a patient session or use a fresh pairing grant. No effect was retried.',
    reference:'This recording reference is unavailable or not granted. Check the reference or import an approved recording into this session. No effect was retried.',
    invalid:'That input is not supported. Review the current controls or ask for help. No effect was retried.',unavailable:'Local connection unavailable. Check the sidecar and refresh; no effect was retried.',
    ack_unavailable:'Support acknowledgement unavailable. Keep private information in the local identity controls; the support mirror may be stale.'};
  return messages[receipt?.presentation?.notice]??view?.message??'';
}

export default {render({model,el}) {
  const base='http://127.0.0.1:28451', storage='bob-v1-';
  let token=sessionStorage.getItem(storage+'token'), role=sessionStorage.getItem(storage+'role')||'patient';
  let state=null, shown=null, working=false, pendingRequests=0, polling=false, disposed=false, renderedRevision=-1, playing=false;
  let dirty=false, noticeKind='none', choiceButtons=[], replayReference=sessionStorage.getItem(storage+'reference')||'';
  const n=(tag,text='',parent=el)=>{const x=document.createElement(tag);x.textContent=text;parent.append(x);return x;};
  const style=n('style');style.textContent=`
    .bob{font:16px/1.5 system-ui,-apple-system,sans-serif;color:#1d252d;max-width:1120px;margin:auto;background:#f4f7fa;padding:24px;border-radius:16px}
    .bob *{box-sizing:border-box}.bob h1{font-size:30px;line-height:1.15;margin:18px 0 8px}.bob h2{font-size:20px;margin:0 0 14px}.bob h3{font-size:17px;margin:14px 0 8px}
    .bob p{margin:8px 0}.bob .brand{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:4px solid #e0a42e;padding-bottom:20px}.bob .brand img{width:222px;height:26px}
    .bob .badge{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#13477d}.bob .muted{color:#46566a;font-size:14px}
    .bob .grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(260px,1fr);gap:18px;margin-top:18px}.bob .card{background:white;border:1px solid #d8e0e8;border-radius:12px;padding:22px;margin-bottom:16px}
    .bob label{display:block;font-size:14px;font-weight:600;margin:10px 0}.bob input,.bob select,.bob textarea{display:block;width:100%;background:white;border:1px solid #8898a9;border-radius:6px;padding:10px;font:inherit;margin-top:5px;color:#1d252d}
    .bob textarea{min-height:90px}.bob button{background:#13477d;color:white;border:1px solid #13477d;border-radius:6px;font:600 14px system-ui;padding:10px 14px;margin:6px 6px 6px 0;cursor:pointer}
    .bob button.secondary{background:#fff;color:#13477d}.bob button:disabled{opacity:.5;cursor:not-allowed}.bob :focus-visible{outline:3px solid #b17409;outline-offset:3px}
    .bob .row{display:flex;flex-wrap:wrap;gap:10px}.bob .row>label{flex:1;min-width:120px}.bob summary{cursor:pointer;font-weight:600;color:#13477d}.bob details{margin:12px 0}
    .bob .notice{border-left:4px solid #13477d;background:#eaf2fa;padding:12px 16px;border-radius:4px}.bob .warning{border-left-color:#a75c00;background:#fff4df}.bob .option{border-top:1px solid #d8e0e8;padding:12px 0}
    .bob pre{white-space:pre-wrap;word-break:break-word;font:12px/1.5 ui-monospace,monospace;max-height:460px;overflow:auto;background:#f4f7fa;padding:12px;border-radius:6px}.bob output{display:block;word-break:break-all;font:13px ui-monospace,monospace}
    .bob .proposal{border:2px solid #13477d}.bob .history{font-size:14px}.bob .mirror-focus{outline:3px solid #b17409}.bob .dev{margin-top:30px;border-top:1px solid #c5cfda;padding-top:20px}
    @media(max-width:760px){.bob{padding:14px}.bob .grid{grid-template-columns:1fr}.bob .brand{align-items:flex-start;flex-direction:column}}
  `;
  const root=n('div');root.className='bob';
  const brand=n('header','',root);brand.className='brand';const logo=n('img','',brand);logo.src=model.get('logo');logo.alt='Ochsner Health';
  const badge=n('span','Private internal review · Synthetic PoC',brand);badge.className='badge';
  n('h1','Find care. Stay in control.',root);
  const disclosure=n('p','BOB is an AI scheduling assistant, not a clinician or a live representative. Use synthetic information only.',root);disclosure.className='muted';
  const connection=n('p','Start a local patient session or join with a one-use pairing grant.',root);connection.setAttribute('role','status');
  const notice=n('p','',root);notice.setAttribute('role','status');notice.className='notice';notice.hidden=true;
  const toolbar=n('div','',root);toolbar.className='row';
  const button=(label,fn,parent=toolbar,secondary=false)=>{const b=n('button',label,parent);b.type='button';if(secondary)b.className='secondary';b.onclick=()=>run(fn);return b;};
  const field=(label,parent,type='text',id)=>{const l=n('label',label,parent),i=n('input','',l);i.type=type;i.setAttribute('aria-label',label);i.autocomplete='off';if(id)i.id=id;return i;};
  const select=(label,choices,parent,id)=>{const l=n('label',label,parent),s=n('select','',l);s.setAttribute('aria-label',label);if(id)s.id=id;for(const [value,text]of choices){const o=n('option',text,s);o.value=value;}return s;};
  const showNotice=(text,warning=false,kind='domain')=>{noticeKind=text?kind:'none';notice.textContent=text;notice.hidden=!text;notice.className='notice'+(warning?' warning':'');};
  async function api(path,body) {
    const response=await fetch(base+path,{method:body===undefined?'GET':'POST',cache:'no-store',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
    if(!response.ok) {
      const error=new Error('local');error.status=response.status;
      // Only a closed Replay denial category selects reference recovery. Never
      // display raw response text or confuse a real capability/join failure.
      if(path==='/replay'&&response.status===403){try{error.referenceUnavailable=(await response.json()).error==='reference_unavailable';}catch{}}
      throw error;
    }return response.json();
  }
  function saveCapability(){sessionStorage.setItem(storage+'token',token);sessionStorage.setItem(storage+'role',role);}
  async function run(fn,allowDuringWait=false){if(working&&!allowDuringWait)return;pendingRequests++;working=true;showNotice('Working locally… No action will be retried automatically.',false,'working');updateEnabled();ack().catch(()=>{});const start=performance.now();try{await fn();if(notice.textContent.startsWith('Working locally'))showNotice('Ready · '+Math.round(performance.now()-start)+' ms',false,'ready');}catch(error){const kind=error.referenceUnavailable?'reference':error.status===403?'grant':error.status===400?'invalid':'unavailable';showNotice(mirroredNotice({presentation:{notice:kind}},null),true,kind);}finally{pendingRequests--;working=pendingRequests>0;updateEnabled();ack().catch(()=>{});}}
  async function command(action,data={}) {const revision=(state?.patient||state)?.revision;if(!Number.isInteger(revision))throw new Error('no current view');const result=await api('/command',{action,data,revision});showNotice(result.message||result.patient?.message||'Local command processed',!!result.stale,result.stale?'stale':'domain');await refresh();return result;}
  button('Start independent patient',async()=>{const created=await api('/create',{});token=created.token;role='patient';saveCapability();renderedRevision=-1;message.value='';dirty=false;persistPublic();await refresh();});
  const grant=field('One-use pairing grant',toolbar);grant.maxLength=128;
  button('Join demo support',async()=>{const result=await api('/join',{grant:grant.value});token=result.token;role='support';saveCapability();grant.value='';renderedRevision=-1;await refresh();});
  const pairOutput=n('output','',root);pairOutput.setAttribute('aria-label','Current pairing grant');
  const pairButton=button('Create support pairing grant',async()=>{pairOutput.textContent=(await api('/pair',{})).grant;showNotice('Share this one-use grant only with the other local demo tab. It expires in five minutes.',false,'pairing');});
  const grid=n('div','',root);grid.className='grid';const flow=n('main','',grid), side=n('aside','',grid);
  const card=(title,parent)=>{const c=n('section','',parent);c.className='card';n('h2',title,c);return c;};
  const publicCard=card('1 · What works for you?',flow);
  const messageLabel=n('label','Public scheduling request',publicCard),message=n('input','',messageLabel);message.id='message';message.setAttribute('aria-label','Public scheduling request');message.maxLength=2048;message.placeholder='Find a family doctor downtown, or type help';
  n('p','Keep phone, birth date, ZIP and names out of this box. Use private controls below. Offline commands work without a model.',publicCard).className='muted';
  const send=button('Send scheduling request',async()=>{const text=message.value,revision=state.revision;message.value='';dirty=false;persistPublic();const result=await api('/text',{text,revision});if(result.stale)showNotice(result.message,true,'stale');else showNotice(result.message);await refresh();},publicCard);
  message.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();send.click();}});
  const filterRow=n('div','',publicCard);filterRow.className='row';
  const specialty=select('Specialty',[['','Choose specialty'],['primary_care','Primary care'],['dermatology','Dermatology']],filterRow,'specialty');
  const location=select('Location',[['','Any location'],['downtown','Downtown'],['uptown','Uptown'],['lakeside','Lakeside']],filterRow,'location');
  const dates=n('div','',publicCard);dates.className='row';const startDate=field('From date',dates,'date','start_date'),endDate=field('Through date',dates,'date','end_date');
  const filters=()=>({specialty:specialty.value||null,location:location.value||null,start_date:startDate.value||null,end_date:endDate.value||null});
  const apply=button('Apply preferences',async()=>{const result=await command('preferences',filters());if(!result.stale){dirty=false;syncFilters(result.preferences);}await refresh();},publicCard,true);
  const discover=button('Find providers',async()=>{await command('discover',filters());dirty=false;await refresh();},publicCard);
  const active=n('p','',publicCard);active.className='muted';
  const suggestions=n('div','',publicCard);
  const providers=n('div','',publicCard);
  const identityDetails=n('details','',flow);identityDetails.id='local-controls';identityDetails.className='card';n('summary','2 · Private synthetic identity',identityDetails);
  n('p','Local controls, not model input. This demonstrates fixture matching, not production authentication. No email is needed.',identityDetails).className='muted';
  const identityStatus=n('p','',identityDetails),identityRow=n('div','',identityDetails);identityRow.className='row';
  const phone=field('Synthetic phone',identityRow,'tel','private_phone'),dob=field('Date of birth',identityRow,'date','private_dob'),zip=field('ZIP discriminator',identityDetails,'text','private_zip');zip.maxLength=5;
  n('p','Blank fields keep prior local entries. Changing any discriminator revokes the prior match and proposal. Private drafts are never mirrored or saved in browser storage.',identityDetails).className='muted';
  const verify=button('Check or correct identity',async()=>{const data={};if(phone.value)data.phone=phone.value;if(dob.value)data.dob=dob.value;if(zip.value)data.zip=zip.value;const result=await command('identity',data);if(result.identity_status==='verified'){phone.value='';dob.value='';zip.value='';}dirty=false;await refresh();},identityDetails);
  const optionsCard=card('3 · Review returned options',flow);
  const availability=button('Get current availability',()=>command('availability'),optionsCard);
  const appointments=button('Look up my appointments',()=>command('appointments'),optionsCard,true);
  const options=n('div','',optionsCard),appointmentList=n('div','',optionsCard);
  const proposalCard=card('4 · Confirm the exact appointment',flow);proposalCard.classList.add('proposal');
  const summary=n('p','No current proposal',proposalCard);
  n('p','Selecting an option does not book it. Confirm in a separate step after checking the exact API time and location.',proposalCard).className='muted';
  const confirm=button('Confirm appointment',async()=>{const proposal=shown?.proposal;const revision=shown?.revision;if(!presentation(shown,role).canConfirm||dirty)throw new Error('no current confirmation');const result=await api('/command',{action:'confirm',data:{proposal_id:proposal.id,nonce:proposal.nonce},revision});showNotice(result.message,!!result.stale,result.stale?'stale':'domain');dirty=false;await refresh();},proposalCard);
  const decline=button('Decline / change my mind',()=>command('decline'),proposalCard,true);
  const outcomeCard=card('Outcomes — not assumptions',side),current=n('p','',outcomeCard),history=n('ol','',outcomeCard);history.className='history';
  n('p','A mock queue receipt is not real staff contact. Unknown writes remain protected after reset or reconnect.',outcomeCard).className='muted';
  const helpCard=card('Help is always available',side);
  const help=button('Help',()=>command('help'),helpCard);
  const medical=button('Medical boundary',()=>command('medical'),helpCard,true);
  const unsupported=button('Unsupported request',()=>command('unsupported'),helpCard,true);
  // Safety routes remain usable during a slow language request. The old model
  // result is revision-bound by the service and cannot overwrite this turn.
  help.onclick=()=>run(()=>command('help'),true);
  medical.onclick=()=>run(()=>command('medical'),true);
  unsupported.onclick=()=>run(()=>command('unsupported'),true);
  const handoff=button('Submit mock handoff',()=>command('handoff',{reason:'user_requested'}),helpCard,true);
  const reset=button('Reset local workflow',async()=>{await command('reset');phone.value='';dob.value='';zip.value='';message.value='';dirty=false;renderedRevision=-1;persistPublic();await refresh();},helpCard,true);
  const supportCard=card('Paired demo support',side),supportStatus=n('p','',supportCard),observedMeta=n('pre','',supportCard),context=n('p','',supportCard);
  const takeover=button('Take demo control',()=>command('takeover'),supportCard);
  const returnControl=button('Return patient control',()=>command('return'),supportCard,true);
  const supportLocation=select('Suggested public location',[['downtown','Downtown'],['uptown','Uptown'],['lakeside','Lakeside']],supportCard);
  const suggest=button('Suggest preference — not adoption',async()=>{state=await api('/suggest',{preferences:{location:supportLocation.value},revision:state.patient.revision});render();},supportCard,true);
  const suggestionText=n('p','',supportCard),accept=button('Accept reviewed support suggestion',async()=>{await api('/accept',{id:shown.support_suggestion.id,revision:shown.revision});dirty=false;await refresh();},supportCard);
  const dev=n('details','',root);dev.id='developer';dev.className='dev';dev.open=sessionStorage.getItem(storage+'developer')==='1';n('summary','Developer Mode · local PoC diagnostics and replay',dev);
  n('p','This disclosure is not authentication. Sanitized diagnostics are not exact transcripts. Replay is a typed semantic simulation, not live consent or full renderer parity.',dev).className='muted';
  const reference=field('Interaction reference',dev);reference.value=replayReference;reference.maxLength=128;
  const capture=button('Start synthetic recording',async()=>{showNotice('Recording only explicitly synthetic supported inputs. Private controls use approved fixture references.');const r=await api('/capture',{enabled:true,synthetic:true});reference.value=r.reference;await inspect();},dev,true);
  button('Seal recording',async()=>{const r=await api('/capture',{enabled:false,synthetic:true});reference.value=r.reference;sessionStorage.setItem(storage+'reference',r.reference);await inspect();},dev,true);
  const diagnostics=n('pre','',dev);diagnostics.setAttribute('aria-label','Sanitized diagnostics');
  async function inspect(){diagnostics.textContent=JSON.stringify(await api('/diagnostics'),null,2);}
  button('Inspect sanitized diagnostics',inspect,dev,true);
  const replayOutput=n('pre','',dev);replayOutput.setAttribute('aria-label','Replay inspection');
  async function replay(operation,data={}){const r=await api('/replay',{operation,data});replayOutput.textContent=JSON.stringify(r,null,2);if(r.reference){replayReference=r.reference;sessionStorage.setItem(storage+'reference',r.reference);}return r;}
  button('Open reference',()=>replay('open',{reference:reference.value}),dev);
  for(const [label,operation]of [['Previous','previous'],['Step','step'],['Pause','pause']])button(label,async()=>{if(operation==='pause')playing=false;await replay(operation);},dev,true);
  button('Play recorded steps',async()=>{await replay('play');playing=true;},dev,true);
  const jump=field('Replay step index (zero based)',dev,'number');jump.value='0';jump.min='0';
  button('Jump / inspect before and after',async()=>{await replay('jump',{index:Number(jump.value)});await replay('beforeafter',{index:Number(jump.value)});},dev,true);
  const bookmark=field('Bookmark name',dev);bookmark.maxLength=64;
  button('Bookmark current step',()=>replay('bookmark',{name:bookmark.value}),dev,true);
  button('Go to bookmark',()=>replay('go_bookmark',{name:bookmark.value}),dev,true);
  const changesLabel=n('label','Typed variant JSON',dev),changes=n('textarea','',changesLabel);changes.setAttribute('aria-label','Typed variant JSON');changes.value='{"api_status":"unknown"}';changes.maxLength=4096;
  button('Fork isolated simulation',()=>replay('fork',{index:Number(jump.value),changes:JSON.parse(changes.value)}),dev,true);
  button('Compare with reference',()=>replay('compare',{reference:reference.value}),dev,true);
  button('Propose reviewed regression fixture',()=>replay('promote',{reviewed:true}),dev,true);
  button('Export reviewed synthetic recording',async()=>{const r=await replay('export',{reviewed:true});exportText.value=r.payload||r.json||'';},dev,true);
  const exportLabel=n('label','Reviewed recording JSON / import',dev),exportText=n('textarea','',exportLabel);exportText.setAttribute('aria-label','Reviewed recording JSON / import');exportText.maxLength=1048576;
  button('Import bounded synthetic recording',()=>replay('import',{payload:exportText.value}),dev,true);
  button('Purge selected recording only',async()=>{playing=false;await replay('purge',{reference:replayReference||reference.value});await inspect();},dev,true);
  const patientControls=[message,send,specialty,location,startDate,endDate,apply,discover,phone,dob,zip,verify,availability,appointments,decline,handoff,reset,capture];
  const publicFields=[message,specialty,location,startDate,endDate];
  function persistPublic(){if(role!=='patient')return;sessionStorage.setItem(storage+'draft',JSON.stringify({message:message.value,specialty:specialty.value,location:location.value,start_date:startDate.value,end_date:endDate.value}));}
  try{const saved=JSON.parse(sessionStorage.getItem(storage+'draft')||'{}');for(const input of publicFields)input.value=typeof saved[input.id]==='string'?saved[input.id]:'';}catch{}
  identityDetails.open=sessionStorage.getItem(storage+'local-controls')==='1';
  for(const input of [...publicFields,phone,dob,zip])input.addEventListener('input',()=>{dirty=true;persistPublic();updateEnabled();ack().catch(()=>{});});
  for(const input of publicFields){input.addEventListener('focus',()=>ack().catch(()=>{}));input.addEventListener('blur',()=>ack().catch(()=>{}));}
  for(const detail of [dev,identityDetails])detail.addEventListener('toggle',()=>{if(role==='patient')sessionStorage.setItem(storage+detail.id,detail.open?'1':'0');ack().catch(()=>{});});
  function syncFilters(preferences={}){specialty.value=preferences.specialty||'';location.value=preferences.location||'';startDate.value=preferences.start_date||'';endDate.value=preferences.end_date||'';persistPublic();}
  function updateEnabled(){for(const input of patientControls)input.disabled=!state||role!=='patient'||working||(shown?.takeover&&!([reset].includes(input)));confirm.disabled=working||dirty||!presentation(shown,role).canConfirm;
    for(const input of choiceButtons)input.disabled=!state||role!=='patient'||working||!!shown?.takeover;
    for(const safe of [help,medical,unsupported])safe.disabled=!state;
    pairButton.disabled=!state||role!=='patient'||working;takeover.disabled=role!=='support'||!state?.fresh||working;returnControl.disabled=role!=='support'||!state?.patient?.takeover||working;suggest.disabled=role!=='support'||!state?.patient?.takeover||working;supportLocation.disabled=role!=='support';accept.disabled=role!=='patient'||!shown?.support_suggestion||shown?.takeover||working;
  }
  function render(){if(!state)return;const mirror=role==='support';shown=mirror?state.observed_patient:state;
    connection.textContent=mirror?`Demo support · ${state.fresh?'fresh':'stale / missing'} · observation age ${state.age_seconds??'—'} seconds`:`Patient · ${(state.interpretation?.mode||'offline')} interpretation · revision ${state.revision}`;
    // Pairing outlives temporary control and does not depend on an acknowledged screen.
    supportStatus.textContent=mirror?`Local participant: ${state.demo_support} · demo control: ${state.control_status||'not reported'} · lease ${state.lease_seconds||0}s`:'Only explicitly paired local demo support can observe the acknowledged screen.';
    if(!shown){current.textContent='No acknowledged patient screen';updateEnabled();return;}
    if(mirror){const receipt=state.last_observed;for(const input of publicFields){input.value=receipt?.draft?.[input.id]||'';input.classList.toggle('mirror-focus',receipt?.focus===input.id);}identityDetails.open=(receipt?.expanded||[]).includes('local-controls');dev.open=(receipt?.expanded||[]).includes('developer');showNotice(mirroredNotice(receipt,shown),['stale','grant','invalid','unavailable','ack_unavailable'].includes(receipt?.presentation?.notice),receipt?.presentation?.notice||'domain');}
    else if(!dirty&&renderedRevision!==shown.revision){syncFilters(shown.preferences);if(!working&&noticeKind==='domain')showNotice(shown.message);}
    identityStatus.textContent='Identity: '+shown.identity_status+(mirror?' · private fields are not mirrored':'');
    active.textContent='Active filters: '+(Object.entries(shown.preferences||{}).map(([k,v])=>`${k.replaceAll('_',' ')}: ${v}`).join(' · ')||'none');
    summary.textContent=presentation(shown,role).summary;
    if(renderedRevision!==shown.revision){providers.replaceChildren();options.replaceChildren();appointmentList.replaceChildren();suggestions.replaceChildren();history.replaceChildren();choiceButtons=[];
      for(const [index,p]of(shown.providers||[]).entries()){const row=n('div','',providers);row.className='option';n('p',`${index+1}. ${p.name} · ${p.specialty.replaceAll('_',' ')} · ${p.locations.join(', ')}`,row);const b=button(`Choose provider ${index+1}`,()=>command('preferences',{provider_id:p.providerId}),row,true);b.disabled=mirror;}
      for(const [index,s]of(shown.slots||[]).entries()){const row=n('div','',options);row.className='option';n('p',`${index+1}. ${s.startTime} · ${s.specialty.replaceAll('_',' ')} · ${s.location}`,row);const b=button(`Select option ${index+1}`,()=>command('select',{index:index+1}),row);b.disabled=mirror;}
      for(const a of(shown.appointments||[]))n('p',`${a.startTime} · ${a.specialty} · ${a.location} · ${a.status}`,appointmentList);
      for(const item of(shown.suggestions||[])){const b=button(`Use ${item.value}`,()=>command('preferences',{[item.field]:item.value}),suggestions,true);b.disabled=mirror;}
      for(const item of presentation(shown,role).history)n('li',item,history);
      choiceButtons=[...providers.children,...options.children,...suggestions.children].flatMap(row=>row.tagName==='BUTTON'?[row]:Array.from(row.children||[]).filter(child=>child.tagName==='BUTTON'));
      renderedRevision=shown.revision;
    }
    current.textContent='Current attempt: '+presentation(shown,role).current;
    observedMeta.textContent=mirror?JSON.stringify({last_observed:state.last_observed,known:state.known,missing:state.missing,uncertain:state.uncertain},null,2):'';
    context.textContent=mirror?`Current backend context (not necessarily observed): revision ${state.patient.revision}, ${state.patient.state}; last acknowledged: ${shown.revision}. Patient display: ${state.last_observed?.presentation?.pending===true?'working':state.last_observed?.presentation?.pending===false?'not working':'work status not reported'}, ${state.last_observed?.presentation?.dirty===true?'unsent corrections':state.last_observed?.presentation?.dirty===false?'no unsent corrections':'correction status not reported'}, confirmation ${state.last_observed?.presentation?.can_confirm===true?'was enabled':state.last_observed?.presentation?.can_confirm===false?'was disabled':'not reported'}. Mirrored transaction controls are read-only.`:shown.message;
    suggestionText.textContent=shown.support_suggestion?'Review suggestion: '+JSON.stringify(shown.support_suggestion.preferences):'No pending public preference suggestion.';
    if(!mirror&&!working&&!notice.textContent)showNotice(shown.message);updateEnabled();
  }
  async function ack(){if(disposed||!state||role!=='patient')return;const focused=publicFields.find(i=>i.matches(':focus'));
    // Historical enabled state is observation only, never a confirmation token.
    await api('/ack',{receipt:semanticReceipt(state.revision,Object.fromEntries(publicFields.map(i=>[i.id,i.value])),focused?.id||null,Math.max(0,Math.round(window.scrollY)),[identityDetails,dev].filter(d=>d.open).map(d=>d.id),{notice:noticeKind,pending:working,dirty,can_confirm:!confirm.disabled})});
  }
  async function refresh(){if(disposed||!token||polling)return;polling=true;try{
    state=await api('/state');render();
    // A rejected privacy-sensitive receipt is not a failed domain read. Keep
    // the patient view honest while explicitly warning that support is stale.
    try{await ack();}catch{showNotice('Support acknowledgement unavailable. Keep private information in the local identity controls; the support mirror may be stale.',true,'ack_unavailable');}
  }catch{connection.textContent='Disconnected or expired. Reconnect is read-only; use a fresh local grant if needed.';confirm.disabled=true;}finally{polling=false;}}
  updateEnabled();refresh();const timer=setInterval(()=>{refresh();if(playing)replay('tick').catch(()=>{playing=false;});},500);
  return()=>{disposed=true;clearInterval(timer);};
}};
