import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
for(const [source,target] of [['public','.next/standalone/public'],['.next/static','.next/standalone/.next/static']]){
 fs.cpSync(path.join(root,source),path.join(root,target),{recursive:true});
}
