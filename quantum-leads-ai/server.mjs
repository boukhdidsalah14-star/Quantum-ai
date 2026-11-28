import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import pg from 'pg';
const {Pool}=pg;
const root=path.dirname(fileURLToPath(import.meta.url)),pub=path.join(root,'public');
const PORT=Number(process.env.PORT||3000);
const pool=process.env.DATABASE_URL?new Pool({connectionString:process.env.DATABASE_URL,ssl:{rejectUnauthorized:false},max:5,idleTimeoutMillis:10000,connectionTimeoutMillis:10000}):null;
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.webmanifest':'application/manifest+json','.json':'application/json','.png':'image/png','.ico':'image/x-icon'};
const send=(res,status,data,headers={})=>{res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store',...headers});res.end(JSON.stringify(data))};
const readBody=req=>new Promise((resolve,reject)=>{let s='';req.on('data',c=>{s+=c;if(s.length>1e6)reject(Error('Request too large'))});req.on('end',()=>{try{resolve(s?JSON.parse(s):{})}catch{reject(Error('Invalid JSON'))}});req.on('error',reject)});
async function log(event,detail=''){if(pool)await pool.query('INSERT INTO activity(event,detail) VALUES($1,$2)',[event,detail])}
async function initDb(){if(!pool)throw Error('DATABASE_URL is not configured');await pool.query(`CREATE TABLE IF NOT EXISTS leads(id UUID PRIMARY KEY DEFAULT gen_random_uuid(),name TEXT NOT NULL,company TEXT DEFAULT '',email TEXT DEFAULT '',source TEXT DEFAULT '',source_url TEXT UNIQUE,status TEXT DEFAULT 'New',score INTEGER DEFAULT 0,intent TEXT DEFAULT '',notes TEXT DEFAULT '',created_at TIMESTAMPTZ DEFAULT NOW(),updated_at TIMESTAMPTZ DEFAULT NOW());CREATE TABLE IF NOT EXISTS campaigns(id UUID PRIMARY KEY DEFAULT gen_random_uuid(),name TEXT NOT NULL,audience TEXT DEFAULT '',message TEXT DEFAULT '',approved BOOLEAN DEFAULT FALSE,created_at TIMESTAMPTZ DEFAULT NOW(),updated_at TIMESTAMPTZ DEFAULT NOW());CREATE TABLE IF NOT EXISTS activity(id UUID PRIMARY KEY DEFAULT gen_random_uuid(),event TEXT NOT NULL,detail TEXT DEFAULT '',created_at TIMESTAMPTZ DEFAULT NOW());CREATE TABLE IF NOT EXISTS tracking_links(id UUID PRIMARY KEY DEFAULT gen_random_uuid(),code TEXT UNIQUE NOT NULL,name TEXT NOT NULL,destination TEXT NOT NULL,clicks INTEGER NOT NULL DEFAULT 0,created_at TIMESTAMPTZ DEFAULT NOW());CREATE TABLE IF NOT EXISTS tracking_events(id UUID PRIMARY KEY DEFAULT gen_random_uuid(),link_id UUID NOT NULL REFERENCES tracking_links(id) ON DELETE CASCADE,created_at TIMESTAMPTZ DEFAULT NOW());CREATE INDEX IF NOT EXISTS leads_created_at_idx ON leads(created_at DESC);CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);`);await pool.query("ALTER TABLE leads ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0, ADD COLUMN IF NOT EXISTS intent TEXT DEFAULT '', ADD COLUMN IF NOT EXISTS source_url TEXT");await pool.query('CREATE UNIQUE INDEX IF NOT EXISTS leads_source_url_unique ON leads(source_url) WHERE source_url IS NOT NULL')}
const topicPattern=/\\b(forex|fx trading|forex bot|trading bot|trading signals|automated trading|algorithmic trading|crypto trading|trading platform|metatrader|mt4|binary options|ai trading)\\b/i;
const buyerPatterns=[
 /\\b(can anyone|could anyone|does anyone|anyone)\\s+(recommend|suggest|know)\\b/i,
 /\\b(any recommendations|recommendations for|suggestions for)\\b/i,
 /\\b(looking for|searching for|trying to find)\\b.{0,70}\\b(tool|platform|bot|software|signals|service)\\b/i,
 /\\b(which|what)\\s+(tool|platform|bot|service)\\b.{0,70}\\b(use|recommend|choose|best)\\b/i,
 /\\b(need|want)\\s+(a|an)\\s+.{0,45}\\b(bot|platform|tool|signals|trading software)\\b/i,
 /\\b(alternative to|anyone using|what do you use for)\\b/i
];
function scorePost(title,text){
 const t=(String(title||'')+' '+String(text||'')).toLowerCase();
 const isShowHn=/^\\s*show hn\\s*:/i.test(String(title||''));
 const isPromo=/\\b(we built|i built|launching|introducing|our product|my product|now available|check out)\\b/i.test(t);
 const topic=topicPattern.test(t);
 const intent=buyerPatterns.some(rx=>rx.test(t));
 if(isShowHn||isPromo||!topic||!intent)return {score:0,intent:'No verified buyer request'};
 return {score:85,intent:'Explicit request for a trading tool recommendation'};
}
async function fetchJson(url){const r=await fetch(url,{headers:{'user-agent':'QuantumLeadsAI/1.0 (public prospect research; contact: owner)'},signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error('Source returned '+r.status);return r.json()}
async function discover(query){
 const defaults=['AI forex trading tools','crypto trading bots','trading signals','automated trading','algorithmic trading'];
 const custom=String(query||'').trim();
 const queries=[...defaults,...(custom&&!defaults.includes(custom)?[custom]:[])];
 const found=[],errors=[],seen=new Set();
 for(const q of queries.slice(0,8)){
  try{
   const url='https://hn.algolia.com/api/v1/search_by_date?query='+encodeURIComponent(q)+'&tags=story&hitsPerPage=100';
   const data=await fetchJson(url);
   for(const p of data?.hits||[]){
    const body=(p.title||'')+' '+(p.story_text||'');
    const s=scorePost(body);
    if(s.score<45)continue;
    const sourceUrl=p.url||'https://news.ycombinator.com/item?id='+p.objectID;
    if(seen.has(sourceUrl))continue;seen.add(sourceUrl);
    found.push({name:p.author?'@'+p.author:'Hacker News member',company:'Hacker News',source:'Hacker News public search',source_url:sourceUrl,score:s.score,intent:s.intent+' | '+s.topic,notes:(p.title||'').slice(0,500),created_at:p.created_at||new Date().toISOString()});
   }
  }catch(e){errors.push('Hacker News ('+q+'): '+e.message)}
 }
 let added=0,duplicates=0;
 for(const x of found){
  const r=await pool.query(`INSERT INTO leads(name,company,email,source,source_url,status,score,intent,notes,created_at,updated_at) VALUES($1,$2,'',$3,$4,$5,$6,$7,$8,$9,NOW()) ON CONFLICT(source_url) DO NOTHING RETURNING id`,[x.name,x.company,x.source,x.source_url,x.score>=70?'Qualified':'New',x.score,x.intent,x.notes,x.created_at]);
  if(r.rowCount)added++;else duplicates++;
 }
 await log('discovery.completed',`queries=${queries.slice(0,8).join(';')}; added=${added}; duplicates=${duplicates}`);
 return {query:queries.join(' | '),scanned:found.length,added,duplicates,results:found.slice(0,50),sources:['Hacker News public search (5 targeted queries)'],errors,note:'Searches Hacker News discussions only. Saves only genuine question posts with an explicit request for a trading-tool recommendation and a matching Forex/crypto topic. Product launches and Show HN promotions are excluded. Every review link opens the original discussion. Reddit is not used because its public endpoint is returning 403. Results are research signals, not confirmed buyers. No email addresses, private data or outreach are collected.'}
}
async function app(req,res){const u=new URL(req.url,'http://localhost'),p=u.pathname,m=req.method;
 if(p==='/api/health'&&m==='GET'){let db='not_configured';try{if(pool){await pool.query('SELECT 1');db='connected'}}catch{db='error'}return send(res,db==='connected'?200:503,{ok:db==='connected',app:'Quantum Leads AI',runtime:'Render',database:db,discoverySources:['Reddit public search','Hacker News public search']})}
 if(p==='/api/internal/daily-discovery'&&m==='POST'){try{const prior=await pool.query("SELECT 1 FROM activity WHERE event='discovery.daily' AND created_at::date=CURRENT_DATE LIMIT 1");if(prior.rowCount)return send(res,200,{ok:true,skipped:true,note:'Daily discovery already ran today.'});const result=await discover('people actively looking for AI forex trading tools, crypto trading platforms, automated trading and trading signals');await log('discovery.daily',`added=${result.added}; duplicates=${result.duplicates}`);return send(res,200,{ok:true,run_at:new Date().toISOString(),...result})}catch(e){console.error('Daily discovery failed',e);return send(res,502,{ok:false,error:e.message})}}
 const redirectMatch=p.match(/^\/r\/([a-zA-Z0-9_-]{8,24})$/);if(redirectMatch&&m==='GET'){if(!pool){res.writeHead(503);return res.end('Tracking unavailable')}const r=await pool.query('UPDATE tracking_links SET clicks=clicks+1 WHERE code=$1 RETURNING id,destination',[redirectMatch[1]]);if(!r.rowCount){res.writeHead(404);return res.end('Link not found')}await pool.query('INSERT INTO tracking_events(link_id) VALUES($1)',[r.rows[0].id]);res.writeHead(302,{location:r.rows[0].destination,'cache-control':'no-store'});return res.end()}
 if(!p.startsWith('/api/')){let rel=decodeURIComponent(p==='/'?'/index.html':p),file=path.resolve(pub,'.'+rel);if(!file.startsWith(pub+path.sep))return send(res,403,{error:'Forbidden'});try{if(!(await stat(file)).isFile())throw Error();const data=await readFile(file);res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream','cache-control':rel.endsWith('.html')?'no-cache':'public, max-age=300'});return res.end(data)}catch{return send(res,404,{error:'Not found'})}}
 if(!pool)return send(res,503,{error:'Database unavailable.'});
 if(p==='/api/logout'&&m==='POST')return send(res,200,{ok:true});
 if(p==='/api/tracking'&&m==='GET'){const r=await pool.query("SELECT id,name,code,destination,clicks,created_at,'https://quantum-leads-ai-app.onrender.com/r/'||code AS short_url FROM tracking_links ORDER BY created_at DESC LIMIT 100");return send(res,200,r.rows)}
 if(p==='/api/tracking'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}let destination;try{destination=new URL(x.destination)}catch{return send(res,400,{error:'Enter a valid destination URL.'})}if(destination.protocol!=='https:'||!['quantum-ai-iqoption-preview.onrender.com','quantum-ai-landing.onrender.com'].includes(destination.hostname))return send(res,400,{error:'Destination must be an approved QUANTUM AI app or landing-page domain.'});const name=String(x.name||'').trim().slice(0,80);if(!name)return send(res,400,{error:'Campaign name is required.'});const code=crypto.randomBytes(6).toString('base64url');const r=await pool.query('INSERT INTO tracking_links(code,name,destination) VALUES($1,$2,$3) RETURNING id,name,code,destination,clicks,created_at',[code,name,destination.toString()]);await log('tracking.created',name);return send(res,201,{...r.rows[0],short_url:'https://quantum-leads-ai-app.onrender.com/r/'+code})}
 if(p==='/api/leads'&&m==='GET'){const r=await pool.query('SELECT * FROM leads ORDER BY created_at DESC LIMIT 2000');return send(res,200,r.rows)}
 if(p==='/api/leads'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}if(!x.name?.trim())return send(res,400,{error:'Lead name is required.'});const r=await pool.query("INSERT INTO leads(name,company,email,source,status,score,intent,notes) VALUES($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *",[x.name.trim(),x.company||'',x.email||'',x.source||'Manual',x.status||'New',Number(x.score)||0,x.intent||'',x.notes||'']);await log('lead.created',x.name.trim());return send(res,201,r.rows[0])}
 const lm=p.match(/^\/api\/leads\/([\w-]+)$/);if(lm){if(m==='DELETE'){const r=await pool.query('DELETE FROM leads WHERE id=$1 RETURNING id',[lm[1]]);if(!r.rowCount)return send(res,404,{error:'Lead not found'});await log('lead.deleted',lm[1]);return send(res,200,{ok:true})}if(m==='PUT'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}const r=await pool.query('UPDATE leads SET name=COALESCE($2,name),company=COALESCE($3,company),email=COALESCE($4,email),source=COALESCE($5,source),status=COALESCE($6,status),score=COALESCE($7,score),intent=COALESCE($8,intent),notes=COALESCE($9,notes),updated_at=NOW() WHERE id=$1 RETURNING *',[lm[1],x.name??null,x.company??null,x.email??null,x.source??null,x.status??null,x.score??null,x.intent??null,x.notes??null]);return r.rowCount?send(res,200,r.rows[0]):send(res,404,{error:'Lead not found'})}}
 if(p==='/api/discover'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}try{return send(res,200,await discover(x.query))}catch(e){console.error('Discovery failed',e);return send(res,502,{error:'Discovery failed. '+e.message})}}
 if(p==='/api/campaigns'&&m==='GET'){const r=await pool.query('SELECT * FROM campaigns ORDER BY created_at DESC');return send(res,200,r.rows)}
 if(p==='/api/campaigns'&&m==='POST'){let x;try{x=await readBody(req)}catch{return send(res,400,{error:'Invalid request'})}if(!x.name?.trim())return send(res,400,{error:'Campaign name is required.'});const r=await pool.query('INSERT INTO campaigns(name,audience,message) VALUES($1,$2,$3) RETURNING *',[x.name.trim(),x.audience||'',x.message||'']);return send(res,201,r.rows[0])}
 const cm=p.match(/^\/api\/campaigns\/([\w-]+)\/(approve|delete)$/);if(cm&&m==='POST'){if(cm[2]==='approve'){const r=await pool.query('UPDATE campaigns SET approved=TRUE,updated_at=NOW() WHERE id=$1 RETURNING id',[cm[1]]);if(!r.rowCount)return send(res,404,{error:'Campaign not found'});await log('campaign.approved',cm[1]);return send(res,200,{ok:true,note:'Approved for a future connected channel; nothing is sent.'})}await pool.query('DELETE FROM campaigns WHERE id=$1',[cm[1]]);return send(res,200,{ok:true})}
 if(p==='/api/activity'&&m==='GET'){const r=await pool.query('SELECT * FROM activity ORDER BY created_at DESC LIMIT 100');return send(res,200,r.rows)}
 return send(res,404,{error:'API route not found.'});
}
const server=http.createServer((req,res)=>app(req,res).catch(e=>{console.error(e);if(!res.headersSent)send(res,500,{error:'Internal server error'})}));
initDb().then(()=>{console.log('Quantum Leads AI database connected');server.listen(PORT,'0.0.0.0',()=>console.log('Quantum Leads AI listening on '+PORT))}).catch(e=>{console.error('Database startup failed:',e);process.exit(1)});
