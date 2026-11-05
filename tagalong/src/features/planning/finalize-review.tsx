'use client';
import {Dialog} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import type {Plan} from '@/services/types';
import {publicWebUrl as sourceLink} from '@/services/place-links';
import {orderActivities} from '@/services/itinerary-order';

export function FinalizeReview({plan,open,onOpenChange,onItinerary,onFinish}:{plan:Plan;open:boolean;onOpenChange:(open:boolean)=>void;onItinerary:()=>void;onFinish:()=>void}){
 const days=new Map<string,Plan['itinerary']>();
 for(const activity of plan.itinerary){
  const day=activity.day||'Date not assigned';
  days.set(day,[...(days.get(day)||[]),activity]);
 }
 const outstanding=plan.tasks.filter(task=>!task.done);
 return <Dialog open={open} onOpenChange={onOpenChange} title="Here is your final itinerary" description="Your final planning outline is ready for review. Reservations and availability still need confirmation.">
  <div className="finalize-review">
   <p className="finalize-assurance">Ready for review. Nothing is booked.</p>
   <dl className="finalize-facts"><div><dt>Working dates</dt><dd>{plan.start===plan.end?plan.start:`${plan.start} – ${plan.end}`}</dd></div><div><dt>Destination</dt><dd>{plan.location||'Not set'}</dd></div><div><dt>Working budget (USD)</dt><dd>{plan.budget>0?`$${plan.budget.toLocaleString('en-US')} per person`:'Not set'}</dd></div></dl>
   <h3>Your itinerary</h3>
   {days.size?[...days].sort(([a],[b])=>a.localeCompare(b)).map(([day,activities])=><section className="finalize-day" key={day} aria-label={'Itinerary for '+day}><h4>{day}</h4><ul>{orderActivities(activities).map(activity=>{const source=sourceLink(activity.source_url);return <li key={activity.id}><strong>{activity.time||'Time to confirm'} · {activity.title}</strong><p>{activity.location||'Location to confirm'}{activity.day&&(activity.day<plan.start||activity.day>plan.end)&&' · Outside working trip dates — review this date'}</p>{source&&<a href={source} target="_blank" rel="noopener noreferrer">Venue details for {activity.title}</a>}</li>;})}</ul></section>):<p>No activities recorded yet. Add places and times in the itinerary.</p>}
   <h3>What to do next</h3><ol className="finalize-next">
    {outstanding.map(task=><li key={task.label}>{task.label}</li>)}
    <li>Check venue opening hours, prices and availability for your dates.</li>
    <li>Confirm any reservations directly with the venue before you travel.</li>
    <li>Arrange transport between activities and allow travel time.</li>
    <li>Share the itinerary with existing plan members and confirm everyone&apos;s preferences.</li>
   </ol>
   <h3>Tasks</h3>{plan.tasks.length?<ul>{plan.tasks.map(task=><li key={task.label}>{task.done?'Done':'Still to do'}: {task.label}</li>)}</ul>:<p>No tasks recorded.</p>}
   <h3>Group votes</h3><p>Recorded votes are preferences; they do not confirm reservations or unanimous agreement.</p>
   {plan.polls.length?plan.polls.map(poll=><section key={poll.id} className="finalize-poll"><h4>{poll.question}</h4><ul>{poll.options.map((option,index)=>{const count=Object.values(poll.votes).filter(vote=>vote===index).length;return <li key={index}>{option}: {count} {count===1?'vote':'votes'}</li>;})}</ul></section>):<p>No polls recorded.</p>}
   <p className="muted">Finishing this review acknowledges what you have read. It does not change the shared plan or make bookings.</p>
   <div className="finalize-actions"><Button variant="outline" onClick={onItinerary}>View full itinerary</Button><Button onClick={onFinish}>Finish review</Button></div>
  </div>
 </Dialog>;
}
