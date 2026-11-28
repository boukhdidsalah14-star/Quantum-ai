const endpoint=process.env.DAILY_DISCOVERY_URL;
const token=process.env.DAILY_DISCOVERY_TOKEN;
if(!endpoint||!token){console.error('Missing DAILY_DISCOVERY_URL or DAILY_DISCOVERY_TOKEN');process.exit(1)}
try{
  const response=await fetch(endpoint,{method:'POST',headers:{'x-automation-token':token,'content-type':'application/json'},body:'{}',signal:AbortSignal.timeout(60000)});
  const result=await response.json().catch(()=>({}));
  console.log(JSON.stringify({status:response.status,...result}));
  if(!response.ok||!result.ok)process.exit(1);
}catch(error){console.error('Daily discovery request failed:',error.message);process.exit(1)}
