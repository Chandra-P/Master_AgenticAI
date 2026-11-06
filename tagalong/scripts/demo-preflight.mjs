// Read-only warm-up and readiness check. Never prints public config values or keys.
const frontend=process.argv[2]||'https://tagalong-web-clbe.onrender.com';
const api=process.argv[3]||'https://tagalong-api-7pdn.onrender.com';
async function check(name,url){
 for(let attempt=1;attempt<=3;attempt++){
  try{const response=await fetch(url,{signal:AbortSignal.timeout(25000),cache:'no-store'});const value=await response.json();
   const ready=name==='API'
    ? value.status==='ok'&&value.capabilities?.plans===true&&value.capabilities?.assistant===true
    : value.connectedReady===true;
   if(response.ok&&ready){console.log(`${name}: ready (attempt ${attempt})`);return true;}
   console.log(`${name}: not ready, HTTP ${response.status} (attempt ${attempt})`);
  }catch{console.log(`${name}: temporarily unavailable (attempt ${attempt})`);}
 }
 return false;
}
const results=await Promise.all([check('API',api+'/health'),check('Frontend',frontend+'/api/config')]);
if(results.every(Boolean))console.log('Readiness checks passed. Open the app and sign in before the presentation.');
else{console.log('Readiness checks did not pass. Use the recorded demo while investigating hosting.');process.exitCode=1;}
