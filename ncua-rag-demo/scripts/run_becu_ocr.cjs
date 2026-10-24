const fs=require('fs');
const {createWorker}=require(process.env.TESSERACT_JS_MODULE || 'tesseract.js');
(async()=>{
 fs.mkdirSync('data/supplemental/ocr-raw',{recursive:true});
 const jobs=JSON.parse(fs.readFileSync('data/supplemental/ocr-work/jobs.json','utf8'));
 const worker=await createWorker('eng',1,{cachePath:'data/supplemental/ocr-work'});
 await worker.setParameters({preserve_interword_spaces:'1'});
 for(const job of jobs){
  const path=`data/supplemental/ocr-raw/${job.report_year}-${job.pdf_page}.json`;
  if(fs.existsSync(path))continue;
  const {data}=await worker.recognize(job.image);
  fs.writeFileSync(path,JSON.stringify({...job,text:data.text,confidence:data.confidence,engine:'tesseract.js 7.0.0',reviewed:false},null,2));
  console.log(job.report_year,job.pdf_page,'confidence',data.confidence);
 }
 await worker.terminate();
})().catch(e=>{console.error(e.message);process.exit(1)});
