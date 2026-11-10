"""Keep operational tasks distinct from the structured group decisions."""
import re
from collections import Counter

_DECISION_ACTION=re.compile(r'\b(?:agree|decide|choose|pick|select|finali[sz]e|set|confirm|settle)\b',re.I)
_CORE_DECISION=re.compile(r'\b(?:budget|spending limit|destination|where to go|location|meeting place|travel dates?|date range|lodging|accommodation|hotel|stay|itinerary|activities|activity|restaurant|meal)\b',re.I)


def distinct_planning_tasks(tasks):
    """Remove repeated labels and tasks that duplicate a structured decision."""
    result=[];seen=set()
    for task in tasks:
        label=' '.join(task.split());key=label.casefold()
        if key in seen:continue
        seen.add(key)
        if _DECISION_ACTION.search(label) and _CORE_DECISION.search(label):continue
        result.append(label)
    return result


def distinct_task_records(tasks):
    remaining=Counter(distinct_planning_tasks([task.get('label','') for task in tasks]))
    result=[]
    for task in tasks:
        label=' '.join(task.get('label','').split())
        if remaining[label]:
            remaining[label]-=1
            result.append({**task,'label':label})
    return result
