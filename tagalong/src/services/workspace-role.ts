export type WorkspaceRole='member'|'admin';
const key='tagalong-access-mode';
export function readWorkspaceRole(userId:string):WorkspaceRole{try{const value=JSON.parse(sessionStorage.getItem(key)||'null');return value?.userId===userId&&value.role==='admin'?'admin':'member';}catch{return 'member';}}
export function writeWorkspaceRole(userId:string,role:WorkspaceRole){try{sessionStorage.setItem(key,JSON.stringify({userId,role}));}catch{if(role==='admin')throw new Error('Admin mode needs session storage enabled.');}}
export function clearWorkspaceRole(){try{sessionStorage.removeItem(key);}catch{}}
