import type {Plan} from '@/services/types';
import {decisionParticipation,type DecisionSnapshot} from '@/services/decisions';

export function homePlanModel(plan:Plan,snapshot:DecisionSnapshot,currentMemberId:string){
 const required=snapshot.decisions.filter(d=>d.required);
 const pending=required.filter(d=>d.status!=='confirmed');
 const ownVote=pending.find(d=>d.options.length&&decisionParticipation(d).missing.includes(currentMemberId));
 const decision=ownVote||pending.find(d=>d.options.length&&decisionParticipation(d).missing.length)||pending[0];
 const missing=decision?decisionParticipation(decision).missing:[];
 const waitingOn=missing.map(id=>plan.members.find((m,index)=>(m.user_id||`demo-member-${index}`)===id)?.name||'Participant');
 const href='/plans/'+encodeURIComponent(plan.id)+'?tab=Decisions'+(decision?'#decision-'+encodeURIComponent(decision.id):'#final-review');
 const label=ownVote?'Add your response':decision?(decision.options.length?'Review '+decision.title.toLowerCase():'Propose '+decision.title.toLowerCase()):snapshot.finalized?'View finalized plan':'Review final plan';
 const status=ownVote?'Your response needed':decision?(missing.length&&decision.options.length?'Waiting on votes':decision.category==='destination'||decision.category==='place'?'Location undecided':'Decision needed'):snapshot.finalized?'Finalized':'Ready to finalize';
 return {completed:required.filter(d=>d.status==='confirmed').map(d=>d.title),pending:pending.map(d=>d.title),waitingOn,href,label,status,priority:ownVote?0:decision?1:2,
  participation:decision?`${decisionParticipation(decision).ballots.length} of ${decision.eligibleMemberIds.length} responded`:'All required decisions confirmed',
  activity:snapshot.last_activity_at&&!Number.isNaN(Date.parse(snapshot.last_activity_at))?'Last activity '+new Date(snapshot.last_activity_at).toLocaleString():'Activity not available'};
}
