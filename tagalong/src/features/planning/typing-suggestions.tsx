import './typing-suggestions.css';

export function TypingSuggestions({enabled,onEnabled,suggestion,onAccept,model=false,status=''}:{enabled:boolean;onEnabled:(value:boolean)=>void;suggestion:string;onAccept:()=>void;model?:boolean;status?:string}) {
 return <div className="typing-suggestions">
   <label><input type="checkbox" checked={enabled} onChange={event=>onEnabled(event.target.checked)}/> Typing suggestions</label>
   <span className="typing-local">{model?'Uses OpenAI after a pause · your draft and recent plan context are sent for suggestions':'On this device only'}</span>
   {enabled&&(suggestion?<div className="typing-choice">
     <span>Continue with <b>{suggestion}</b></span>
     <button type="button" aria-label={`Accept suggestion: ${suggestion}`} onClick={onAccept}>Accept <span aria-hidden="true">↹</span></button>
     <small>Tab to accept · Esc to dismiss</small>
   </div>:<span className="typing-help">{model?'Suggestions appear for common planning phrases or after you pause.':'Try “Let” or a planning word. Suggestions stay on this device.'}</span>)}
   {enabled&&status&&<span className="typing-help">{status}</span>}
 </div>;
}
