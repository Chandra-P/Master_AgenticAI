import './decisions.css';
export function ConsensusMeter({score,finalized}:{score:number;finalized:boolean}) {
 const value=finalized?100:Math.min(99,Math.max(0,Number.isFinite(score)?Math.round(score):0));
 const label=value===100?'Finalized':value>70?'Almost Ready':value>30?'Narrowing Options':'Early Discussion';
 return <div className="decision-consensus" title="Agreement toward required decisions. 100% means this plan was explicitly finalized; it does not mean everything is booked."><div className="decision-row"><strong>Consensus progress {value}%</strong><span>{label}</span></div><div role="progressbar" aria-label="Group consensus" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value} aria-valuetext={`${value}% — ${label}`} className="decision-progress"><span style={{width:value+'%'}}/></div></div>;
}
