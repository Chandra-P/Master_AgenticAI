'use client';
export default function ErrorPage({reset}:{error:Error;reset:()=>void}){return <main className="page-content empty-state"><h1>Something interrupted your plan.</h1><p>Please retry. Your saved plans remain in your workspace.</p><button className="btn btn-primary" onClick={reset}>Try again</button></main>;}
