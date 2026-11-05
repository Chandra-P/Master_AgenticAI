"""Authored fictional storyboards, isolated from real plans and auth accounts."""
import copy


def build(story_id,title,people,summary,rows):
    snapshot={'budget':None,'preferences':[],'poll':None,'itinerary':[],'tasks':[],'finalized':False}
    events=[]
    for stage,author,text,changes in rows:
        snapshot.update(copy.deepcopy(changes))
        events.append({'stage':stage,'author':author,'assistant':author=='Tagalong','text':text,'snapshot':copy.deepcopy(snapshot)})
    return {'id':story_id,'title':title,'people':people,'summary':summary,'simulated':True,'disclaimer':'Fictional people and conversation. AI replies are scripted illustrations, not live model outputs. Prices are sample estimates, not quotes. No booking, invitation, weather or availability check has occurred.','events':events}


SF=build('sf-christmas','Christmas weekend in San Francisco',['Shyam Srinivas','Arjun'],
 'Two friends turn a Christmas-weekend idea into an agreed three-day plan.',[
 ('The first idea','Shyam Srinivas','Arjun, shall we spend December 25–27 in San Francisco? I want a Christmas weekend away, but not a rushed one.',{}),
 ('The first idea','Arjun','Yes. I would like time by the water and good food. How much are we spending?',{}),
 ('Gather constraints','Shyam Srinivas','@Tagalong help us plan. I can spend at most $600 per person, excluding travel to San Francisco.',{}),
 ('Gather constraints','Tagalong','I have a proposed cap of $600 per person for the three-day local plan. Before suggesting an itinerary: what dietary needs, pace, and transport preferences should I consider?',{'budget':600}),
 ('Gather constraints','Arjun','Vegetarian options, please. I would rather use public transport than rent a car.',{}),
 ('Gather constraints','Shyam Srinivas','Agreed. One main activity each day, and free time in the afternoon.',{}),
 ('AI organizes the plan','Tagalong','Proposed constraints: vegetarian-friendly meals, public transport, and a relaxed pace. Please confirm these; I will not treat suggestions as final decisions.',{'preferences':['Vegetarian meals — proposed','Public transport — proposed','Relaxed pace — proposed']}),
 ('AI organizes the plan','Arjun','Confirmed: vegetarian meals and public transport.',{}),
 ('AI organizes the plan','Shyam Srinivas','I confirm the relaxed pace. Keep our $600 cap visible.',{'preferences':['Vegetarian meals — confirmed','Public transport — confirmed','Relaxed pace — confirmed']}),
 ('Compare choices','Tagalong','Two fictional itinerary directions: A, waterfront and neighborhood walks; B, more indoor attractions. Holiday openings and prices need checking. Which direction should we build around?',{'poll':{'question':'Which itinerary direction?','options':['Waterfront and neighborhoods','Indoor attractions'],'votes':{}}}),
 ('Compare choices','Arjun','I vote waterfront and neighborhoods, with an indoor fallback if needed.',{'poll':{'question':'Which itinerary direction?','options':['Waterfront and neighborhoods','Indoor attractions'],'votes':{'Arjun':'Waterfront and neighborhoods'}}}),
 ('Compare choices','Shyam Srinivas','Same vote. How does the budget look?',{'poll':{'question':'Which itinerary direction?','options':['Waterfront and neighborhoods','Indoor attractions'],'votes':{'Arjun':'Waterfront and neighborhoods','Shyam Srinivas':'Waterfront and neighborhoods'}}}),
 ('Refine the draft','Tagalong','Illustrative per-person allocation: lodging $300, meals $150, local transport $40, activities $30, reserve $80. Total $600. These are sample allocations, not checked prices.',{}),
 ('Refine the draft','Arjun','Can day two have a late start? I do not want an early alarm on vacation.',{}),
 ('Refine the draft','Tagalong','Yes. Draft: Dec 25 arrival and a short waterfront walk; Dec 26 late breakfast and neighborhood exploring; Dec 27 a flexible morning before departure. Indoor alternatives depend on confirmed holiday opening hours.',{'itinerary':['Dec 25 · Arrival, check-in, short waterfront walk, vegetarian dinner','Dec 26 · Late breakfast, neighborhood exploring, free afternoon','Dec 27 · Flexible morning, pack and depart']}),
 ('Confirm responsibilities','Shyam Srinivas','I will check lodging options and holiday opening hours. Arjun, can you check vegetarian menus and local transport costs?',{'tasks':['Shyam: check lodging and holiday opening hours','Arjun: check vegetarian menus and transport costs']}),
 ('Confirm responsibilities','Arjun','Yes. I approve the draft dates, $600 cap, and relaxed itinerary. Nothing should be booked yet.',{}),
 ('Final agreement','Shyam Srinivas','I approve too. This is our agreed planning outline; purchases wait until we verify actual prices and availability.',{'finalized':True}),
 ('Final agreement','Tagalong','Agreed outline: Dec 25–27, two travelers, $600 per person, vegetarian meals, public transport, and a relaxed itinerary. Both have approved it. The assigned checks remain open; no reservations have been made.',{}),
])

YOSEMITE=build('yosemite-friends','Three days in Yosemite',['Shyam Srinivas','Arjun','Neha','Kavya'],
 'Four friends reconcile pace, accessibility, weather contingencies, and a shared budget.',[
 ('The first idea','Neha','Can the four of us plan a three-day Yosemite trip for May 14–16, 2027?',{}),
 ('The first idea','Shyam Srinivas','I am in. @Tagalong help us turn this into a plan instead of another endless chat.',{}),
 ('Gather constraints','Arjun','My cap is $450 per person, excluding travel to our meeting point.',{}),
 ('Gather constraints','Kavya','I prefer short walks and frequent breaks. Please do not assume everyone wants a demanding hike.',{}),
 ('Gather constraints','Neha','I want photography time. We need a backup if conditions or access change.',{}),
 ('AI organizes the plan','Tagalong','Proposed constraints: $450 per person, gentle activities, photography time, and a flexible backup. Before confirming routes, someone must verify access requirements, conditions, and suitability. Do you all agree?',{'budget':450,'preferences':['Gentle activities — proposed','Photography time — proposed','Flexible backup — proposed']}),
 ('AI organizes the plan','Shyam Srinivas','Yes. We will verify current park requirements rather than assuming a route is accessible.',{}),
 ('AI organizes the plan','Kavya','Confirmed. A relaxed plan is important to me.',{'preferences':['Gentle activities — confirmed','Photography time — confirmed','Flexible backup — confirmed']}),
 ('Resolve the disagreement','Arjun','I would like one more active outing. Could we split briefly instead of making everyone do the same thing?',{}),
 ('Resolve the disagreement','Tagalong','Two draft approaches: A, stay together for gentle activities; B, optional small-group activities with an agreed meeting point. Vote before I adjust the itinerary.',{'poll':{'question':'Day-two activity style?','options':['Stay together, gentle pace','Optional split activities'],'votes':{}}}),
 ('Group decision','Shyam Srinivas','I vote optional split activities, provided nobody is left alone.',{'poll':{'question':'Day-two activity style?','options':['Stay together, gentle pace','Optional split activities'],'votes':{'Shyam Srinivas':'Optional split activities'}}}),
 ('Group decision','Neha','Same. Kavya and I can photograph at a gentle pace.',{'poll':{'question':'Day-two activity style?','options':['Stay together, gentle pace','Optional split activities'],'votes':{'Shyam Srinivas':'Optional split activities','Neha':'Optional split activities'}}}),
 ('Group decision','Kavya','That works. My vote is optional split activities with a clear meeting time.',{'poll':{'question':'Day-two activity style?','options':['Stay together, gentle pace','Optional split activities'],'votes':{'Shyam Srinivas':'Optional split activities','Neha':'Optional split activities','Kavya':'Optional split activities'}}}),
 ('Group decision','Arjun','Agreed. I vote for that too.',{'poll':{'question':'Day-two activity style?','options':['Stay together, gentle pace','Optional split activities'],'votes':{'Shyam Srinivas':'Optional split activities','Neha':'Optional split activities','Kavya':'Optional split activities','Arjun':'Optional split activities'}}}),
 ('Refine the draft','Tagalong','Illustrative allocation per person: lodging $220, food $100, shared transport $70, activities/access allowance $20, reserve $40: $450 total. Confirm actual costs before committing.',{}),
 ('Refine the draft','Tagalong','Draft: day one arrive and orient; day two optional paired activities followed by a group meal; day three a short flexible stop and return. Specific locations depend on verified access, conditions, and everyone’s comfort.',{'itinerary':['May 14 · Shared arrival, orientation, gentle activity, group dinner','May 15 · Optional paired activities, agreed regroup time, group meal','May 16 · Flexible short stop, pack, return travel']}),
 ('Confirm responsibilities','Neha','I will verify park access requirements and conditions. Kavya will review activity suitability.',{'tasks':['Neha: verify park access requirements and conditions','Kavya: review activity suitability','Arjun: compare lodging and transport estimates','Shyam: coordinate meeting point and regroup time']}),
 ('Confirm responsibilities','Arjun','I will compare lodging and transport estimates. I approve the cap and draft.',{}),
 ('Confirm responsibilities','Kavya','I approve the gentle options, paired groups, and fallback. The actual activity choices still need checking.',{}),
 ('Confirm responsibilities','Neha','I approve the draft dates and plan.',{}),
 ('Final agreement','Shyam Srinivas','I approve too and will coordinate meeting points. We have a plan and clear next steps, without pretending anything is booked.',{'finalized':True}),
 ('Final agreement','Tagalong','All four have approved the draft: three days, $450 per person, optional paired activities, and a flexible backup. Verification tasks remain assigned. No availability, park access, or reservations have been confirmed.',{}),
])

DATE=build('sf-date-night','A San Francisco date night',['Shyam Srinivas','Priya'],
 'A fictional couple turns competing ideas into a mutually approved one-day date.',[
 ('The first idea','Shyam Srinivas','Priya, can we plan a date in San Francisco on December 12? I want it to feel thoughtful without scheduling every minute.',{}),
 ('The first idea','Priya','Yes. Somewhere quiet for dinner and enough time to talk. I am free from 4 pm.',{}),
 ('Gather constraints','Shyam Srinivas','@Tagalong help us choose. Our total budget for both of us is $180.',{}),
 ('Gather constraints','Tagalong','I will treat $180 as the total for two, not per person. Any food preferences or latest finish time?',{'budget':180}),
 ('Gather constraints','Priya','Vegetarian options and home by 10 pm. I would like a short walk if conditions allow.',{}),
 ('Gather constraints','Shyam Srinivas','I was thinking of a busy evening attraction, but a quieter evening sounds better for conversation.',{}),
 ('AI organizes the plan','Tagalong','Proposed preferences: quiet dinner, vegetarian options, flexible short walk, finish by 10 pm. Please confirm before I build around them.',{'preferences':['Quiet dinner — proposed','Vegetarian options — proposed','Finish by 10 pm — proposed']}),
 ('AI organizes the plan','Priya','I confirm those preferences. Keep the walk optional.',{}),
 ('AI organizes the plan','Shyam Srinivas','Confirmed. Can we compare a walk-and-dinner option against an indoor option?',{'preferences':['Quiet dinner — confirmed','Vegetarian options — confirmed','Finish by 10 pm — confirmed']}),
 ('Compare choices','Tagalong','Option A: optional walk, then dinner. Option B: indoor conversation activity, then dinner. Both are draft concepts; I have not checked venues, weather, hours, or availability.',{'poll':{'question':'Preferred date-night outline?','options':['Optional walk and dinner','Indoor activity and dinner'],'votes':{}}}),
 ('Group decision','Priya','I vote optional walk and dinner, with the indoor option as a backup.',{'poll':{'question':'Preferred date-night outline?','options':['Optional walk and dinner','Indoor activity and dinner'],'votes':{'Priya':'Optional walk and dinner'}}}),
 ('Group decision','Shyam Srinivas','Same vote. Please keep enough buffer so we do not rush.',{'poll':{'question':'Preferred date-night outline?','options':['Optional walk and dinner','Indoor activity and dinner'],'votes':{'Priya':'Optional walk and dinner','Shyam Srinivas':'Optional walk and dinner'}}}),
 ('Refine the draft','Tagalong','Illustrative allocation for both people: dinner $110, local transport $30, dessert $20, reserve $20, total $180. Actual menu prices, taxes, and other costs need checking.',{}),
 ('Refine the draft','Tagalong','Draft: meet at 4 pm, optional short walk or indoor backup, dinner around 6 pm, optional dessert, then leave enough time to be home by 10 pm.',{'itinerary':['4:00 pm · Meet and check conditions together','4:30 pm · Optional short walk or indoor backup','6:00 pm · Quiet vegetarian-friendly dinner, venue to confirm','7:30 pm · Optional dessert and conversation','Before 10:00 pm · Return home']}),
 ('Confirm responsibilities','Priya','I will shortlist quiet dinner options and check vegetarian menus. Can you handle transport and the backup?',{'tasks':['Priya: verify menus, hours and dinner availability','Shyam: check transport time and indoor backup']}),
 ('Confirm responsibilities','Shyam Srinivas','Yes. I approve the outline and the $180 total cap.',{}),
 ('Final agreement','Priya','I approve too. Let us confirm the venue separately after checking the real details.',{'finalized':True}),
 ('Final agreement','Tagalong','Both have approved the outline. The $180 budget is for the couple, the walk stays optional, and you aim to be home by 10 pm. Venue and transport checks remain open. Nothing has been booked.',{}),
])

STORIES=[SF,YOSEMITE,DATE]
