// Run after launching an isolated headless Chrome on localhost:9229.
// Uses native Node WebSocket/CDP; no browser package dependency required.
import {mkdir,writeFile} from 'node:fs/promises';
const password=process.env.DEMO_ACCOUNT_PASSWORD;
if(!password)throw new Error('Set DEMO_ACCOUNT_PASSWORD first');
const targets=await(await fetch('http://127.0.0.1:9229/json')).json();
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
let sequence=0;const pending=new Map(),runtimeErrors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')runtimeErrors.push(m.params.exceptionDetails.text);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result)}};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const wait=async expression=>{for(let i=0;i<150;i++){try{if(await evaluate(expression))return}catch{}await new Promise(r=>setTimeout(r,100))}throw new Error('UI timeout: '+expression)};
const assert=(condition,message)=>{if(!condition)throw new Error(message)};
const cases=[
 ['admin_demo','ADMIN','admin-layout',null],
 ['soc_manager','SOC_MANAGER','manager-layout','DMINC000'],
 ['analyst_l1','SOC_L1','l1-layout','DMINC005'],
 ['analyst_l2','SOC_L2','l2-layout','DMINC001'],
 ['analyst_l3','SOC_L3','l3-layout','DMINC016'],
 ['incident_responder','INCIDENT_RESPONDER','responder-layout','DMINC002'],
 ['threat_hunter','THREAT_HUNTER','hunter-layout','DMINC003'],
];
const output=[];
const changeHash=hash=>evaluate(`location.hash=${JSON.stringify(hash)}`);
try{
 await mkdir('../docs/screenshots',{recursive:true});
 await send('Runtime.enable');await send('Page.enable');
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://127.0.0.1:5173/'});
 await wait("location.origin==='http://127.0.0.1:5173' && !!document.querySelector('#root')");
 for(const [username,role,layout,incident] of cases){
  await evaluate("localStorage.removeItem('soc_token');localStorage.setItem('soc_theme','dark');location.hash=''");
  await send('Page.reload');await wait("!!document.querySelector('#login-user')");
  await evaluate(`(()=>{const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;for(const [id,value] of [['login-user',${JSON.stringify(username)}],['login-password',${JSON.stringify(password)}]]){const input=document.getElementById(id);set.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}));}document.querySelector('.login-card form').requestSubmit();})()`);
  await wait(`document.querySelector('.role-workspace')?.dataset.role===${JSON.stringify(role)} && !!document.querySelector('.${layout}')`);
  const home=await evaluate(`({username:document.querySelector('.header-username').textContent,route:location.hash,accent:getComputedStyle(document.querySelector('.role-workspace')).getPropertyValue('--accent'),menus:[...document.querySelectorAll('.workspace-nav')].map(x=>x.textContent),errors:[...document.querySelectorAll('.error-banner,.error-box')].map(x=>x.textContent),rows:document.querySelectorAll('tbody tr').length,cards:document.querySelectorAll('.case-card').length})`);
  assert(home.username===username && home.route===`#/${role}/home`,username+' redirect/header');
  assert(!home.errors.length,username+' errors: '+home.errors.join(';'));
  if(role==='INCIDENT_RESPONDER')await wait("document.querySelectorAll('.board-column').length===2");
  const screenshot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(`../docs/screenshots/${role.toLowerCase()}.png`,Buffer.from(screenshot.data,'base64'));
  if(role!=='ADMIN'){
   await changeHash(`/${role}/personal`);await wait("document.querySelectorAll('.personal-layout .w-stat').length===4");
   assert(await evaluate("!document.querySelector('.personal-layout .error-box')"),username+' personal');
   await changeHash(`/${role}/incidents/${incident}`);await wait("!!document.querySelector('.detail-grid')");
   const forms=await evaluate(`({next:[...document.querySelectorAll('.detail-actions button')].map(x=>x.textContent).filter(x=>x.startsWith('Chuyển →')),actions:document.querySelector('select[name=action]')?.options.length||0,analysis:!!document.querySelector('input[name=risk_score]'),checklist:document.querySelectorAll('.response-checklist li').length,linkForms:document.querySelectorAll('.detail-actions select[name=value]').length})`);
   if(role==='SOC_L1')assert(forms.next.some(x=>x.includes('INVESTIGATING'))&&forms.actions===0,'L1 rights');
   if(role==='SOC_L2')assert(forms.actions===2&&forms.next.some(x=>x.includes('CONTAINED'))&&!forms.analysis,'L2 rights');
   if(role==='SOC_L3')assert(forms.actions===2&&forms.analysis,'L3 rights');
   if(role==='INCIDENT_RESPONDER')assert(forms.actions===7&&forms.checklist===7&&forms.next.some(x=>x.includes('REMEDIATING')),'Responder rights');
   if(role==='THREAT_HUNTER')assert(forms.actions===0&&forms.linkForms===2&&!forms.next.length,'Hunter rights');
   home.actionForms=forms;
  }else{
   for(const page of ['to_chuc','tai_san','nhan_vien_soc','audit']){
    await changeHash(`/ADMIN/${page}`);await wait(page==='audit'?"document.querySelectorAll('.w-panel tbody tr').length>0":"!!document.querySelector('.directory-grid')");
   }
  }
  await changeHash(`/${role==='ADMIN'?'SOC_L1':'ADMIN'}/home`);
  await wait("[...document.querySelectorAll('h2')].some(x=>x.textContent==='Không có quyền')");
  await changeHash(`/${role}/home`);await wait(`!!document.querySelector('.${layout}')`);
  await evaluate("document.querySelector('.theme-toggle').click()");
  await wait("document.documentElement.dataset.theme==='light'");
  assert(await evaluate("localStorage.getItem('soc_theme')==='light'"),'Theme persistence');
  output.push({...home,role,result:'PASS'});console.log(username+' '+role+' PASS: home, menu, forms, personal, URL guard, theme');
 }
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await wait("innerWidth===390");
 assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile overflow');
 const mobile=await send('Page.captureScreenshot',{format:'png'});await writeFile('../docs/screenshots/hunter-mobile-light.png',Buffer.from(mobile.data,'base64'));
 assert(runtimeErrors.length===0,'Browser runtime errors: '+runtimeErrors.join(';'));
 await writeFile('../docs/workspace-browser-results.json',JSON.stringify(output,null,2));
 console.log('7 browser journeys PASS; mobile PASS; no runtime errors.');
 await send('Browser.close');
}catch(e){console.error(e);process.exitCode=1}finally{ws.close()}
