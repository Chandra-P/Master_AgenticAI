import './typing-suggestions.css';

export function TypingSuggestions({enabled,onEnabled,suggestion,onAccept}:{enabled:boolean;onEnabled:(value:boolean)=>void;suggestion:string;onAccept:()=>void}) {
 return <div className="typing-suggestions"><label><input type="checkbox" checked={enabled} onChange={event=>onEnabled(event.target.checked)}/> Typing suggestions</label><span className="typing-local">On this device only</span>{enabled&&suggestion&&<div className="typing-choice"><span>Continue with <b>{suggestion}</b></span><button type="button" aria-label={`Accept suggestion: ${suggestion}`} onClick={onAccept}>Accept <span aria-hidden="true">↹</span></button><small>Tab to accept · Esc to dismiss</small></div>}</div>;
}
