import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.dirname(fileURLToPath(import.meta.url));
const pub=path.join(root,'public');
const PORT=Number(process.env.PORT||3000);
const OWNER_PASSWORD=process.env.OWNER_PASSWORD||'';
const SESSION_SECRET=process.env.SESSION_SECRET||'';
const leads=[],campaigns=[],activity=[];
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.webmanifest':'application/manifest+json','.json':'application/json','.png':'image/png','.ico':'image/x-icon'};
const send=(res,status,data,headers={})=>{res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store',...headers});res.end(JSON.stringify(data))};
const readBody=req=>new Promise((resolve,reject)=>{let s='';req.on('data',c=>{s+=c;if(s.length>1e6)reject(Error('Request too large'))});req.on('end',()=>{try{resolve(s?JSON.parse(s):{})}catch{reject(Error('Invalid JSON'))}});req.on('error',reject)});
const b64=s=>Buffer.from(s).toString('base64url');
const sign=s=>crypto.createHmac('sha256',SESSION_SECRET).update(s).digest('base64url');
function makeToken(){const p=b64(JSON.stringify({exp:Date.now()+7*864e5,role:'owner'}));return p+'.'+sign(p)}
function validToken(req){const h=req.headers.authorization||'';if(!h.toLowerCase().startsWith('bearer '))return false;const [p,s]=h.slice(7).trim().split('.');if(!p||!s||!SESSION_SECRET)return false;const expected=sign(p);if(s.length!==expected.length||!crypto.timingSafeEqual(Buffer.from(s),Buffer.from(expected)))return false;try{return JSON.parse(Buffer.from(p,'base64url').toString()).exp>Date.now()}catch{return false}}
function log(event,detail=''){activity.unshift({id:crypto.randomUUID(),event,detail,created_at:new Date().toISOString()})}
async function app(req,res){const u=new URL(req.url,'http://localhost'),p=u.pathname,m=req.method;
 if(p==='/api/health'&&m==='GET')return send(res,200,{ok:true,app:'Quantum Leads AI',runtime:'Render',ownerPasswordConfigured:!!OWNER_PASSWORD,sessionSecretConfigured:!!SESSION_SECRET});
 if(p==='/api/login'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request.'})}if(!OWNER_PASSWORD||!SESSION_SECRET)return send(res,503,{error:'Owner access is not configured.'});if(typeof x.password!=='string'||x.password!==OWNER_PASSWORD)return send(res,401,{error:'Incorrect password.'});return send(res,200,{ok:true,token:makeToken()})}
 if(p==='/api/session'&&m==='GET')return send(res,200,{authenticated:validToken(req),authMethod:validToken(req)?'bearer':'none'});
 if(!p.startsWith('/api/')){let rel=decodeURIComponent(p==='/'?'/index.html':p);let file=path.resolve(pub,'.'+rel);if(!file.startsWith(pub+path.sep))return send(res,403,{error:'Forbidden'});try{if(!(await stat(file)).isFile())throw Error();const data=await readFile(file);res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream','cache-control':rel.endsWith('.html')?'no-cache':'public, max-age=300'});return res.end(data)}catch{return send(res,404,{error:'Not found'})}}
 if(!validToken(req))return send(res,401,{error:'Authentication required.'});
 if(p==='/api/logout'&&m==='POST')return send(res,200,{ok:true});
 if(p==='/api/leads'&&m==='GET')return send(res,200,leads);
 if(p==='/api/leads'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}if(!x.name?.trim())return send(res,400,{error:'Lead name is required.'});const t=new Date().toISOString(),v={id:crypto.randomUUID(),name:x.name.trim(),company:x.company||'',email:x.email||'',source:x.source||'',status:x.status||'New',notes:x.notes||'',created_at:t,updated_at:t};leads.unshift(v);log('lead.created',v.name);return send(res,201,v)}
 let lm=p.match(/^\/api\/leads\/([\w-]+)$/);if(lm){const i=leads.findIndex(x=>x.id===lm[1]);if(i<0)return send(res,404,{error:'Lead not found'});if(m==='DELETE'){leads.splice(i,1);log('lead.deleted',lm[1]);return send(res,200,{ok:true})}if(m==='PUT'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}leads[i]={...leads[i],...x,updated_at:new Date().toISOString()};return send(res,200,{ok:true})}}
 if(p==='/api/campaigns'&&m==='GET')return send(res,200,campaigns);
 if(p==='/api/campaigns'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}if(!x.name?.trim())return send(res,400,{error:'Campaign name is required.'});const t=new Date().toISOString(),v={id:crypto.randomUUID(),name:x.name,audience:x.audience||'',message:x.message||'',approved:0,created_at:t,updated_at:t};campaigns.unshift(v);return send(res,201,v)}
 const cm=p.match(/^\/api\/campaigns\/([\w-]+)\/(approve|delete)$/);if(cm&&m==='POST'){const i=campaigns.findIndex(x=>x.id===cm[1]);if(i<0)return send(res,404,{error:'Campaign not found'});if(cm[2]==='approve'){campaigns[i].approved=1;campaigns[i].updated_at=new Date().toISOString();log('campaign.approved',cm[1]);return send(res,200,{ok:true,note:'Approved for a future connected channel; nothing is sent.'})}campaigns.splice(i,1);return send(res,200,{ok:true})}
 if(p==='/api/activity'&&m==='GET')return send(res,200,activity.slice(0,100));
 if(p==='/api/ai'&&m==='POST')return send(res,503,{error:'AI is not configured on this Render test deployment yet.'});
 return send(res,404,{error:'API route not found.'});
}
http.createServer((req,res)=>app(req,res).catch(e=>{console.error(e);if(!res.headersSent)send(res,500,{error:'Internal server error'})})).listen(PORT,'0.0.0.0',()=>console.log('Quantum Leads AI listening on '+PORT));
