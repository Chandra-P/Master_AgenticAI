const key='tagalong-pending-invitation';
export const validInvitation=(token:string)=>/^[A-Za-z0-9_-]{43}$/.test(token);
export function pendingInvitation(){try{return sessionStorage.getItem(key)||'';}catch{return '';}}
export function rememberInvitation(token:string){try{sessionStorage.setItem(key,token);}catch{/* The original URL remains usable. */}}
export function clearInvitation(){try{sessionStorage.removeItem(key);}catch{}}
