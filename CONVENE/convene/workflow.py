from typing import TypedDict
from datetime import datetime, timedelta
from uuid import uuid4
from langgraph.graph import StateGraph, START, END
from convene.integrations import validate_mode, retrieve_vendors, creative_ideas

class State(TypedDict, total=False):
    brief: dict
    mode: str
    agent_steps: list[str]
    allocations: dict
    vendors: list[dict]
    estimated_total: float
    schedule: list[dict]
    creative: str
    review: dict
    id: str


def requirements(state):
    return {'id': str(uuid4()), 'mode': validate_mode(), 'agent_steps': ['Requirements']}

def budget(state):
    amount = state['brief']['budget']
    return {'allocations': {'venue': round(amount * .45, 2), 'catering': round(amount * .45, 2),
                            'reserve': round(amount * .10, 2)},
            'agent_steps': state['agent_steps'] + ['Budget']}

def vendor(state):
    candidates = retrieve_vendors(state['brief'], state['mode'])
    selected = []
    for category in ('venue', 'catering'):
        options = [dict(v, estimated_cost=round(v['base_cost'] + v['per_guest'] * state['brief']['guests'], 2))
                   for v in candidates if v['category'] == category]
        affordable = [v for v in options if v['estimated_cost'] <= state['allocations'][category]]
        if affordable:
            selected.append(min(affordable, key=lambda v: v['estimated_cost']))
    return {'vendors': selected, 'estimated_total': round(sum(v['estimated_cost'] for v in selected), 2),
            'agent_steps': state['agent_steps'] + ['Vendor']}

def schedule(state):
    start = datetime.fromisoformat(state['brief']['event_date'] + 'T10:00:00')
    minutes = state['brief']['duration_hours'] * 60
    slots = [(0, 'Welcome and introductions'), (int(minutes * .15), 'Main activity'),
             (int(minutes * .6), 'Food and networking'), (int(minutes * .9), 'Closing reflection')]
    return {'schedule': [{'time': (start + timedelta(minutes=offset)).strftime('%H:%M'), 'activity': label}
                         for offset, label in slots], 'agent_steps': state['agent_steps'] + ['Schedule']}

def creative(state):
    return {'creative': creative_ideas(state['brief'], state['mode']),
            'agent_steps': state['agent_steps'] + ['Creative']}

def review(state):
    warnings = []
    categories = {v['category'] for v in state['vendors']}
    for category in ('venue', 'catering'):
        if category not in categories:
            warnings.append(f'No affordable synthetic {category} match for this city and guest count.')
    warnings.append('Confirm accessibility, dietary needs, local time, taxes and actual availability with a human.')
    status = 'ready_for_human_review' if len(categories) == 2 else 'needs_revision'
    return {'review': {'status': status, 'warnings': warnings,
                       'disclaimer': 'Synthetic estimates only. No reservations or payments made.'},
            'agent_steps': state['agent_steps'] + ['Review']}

def build_graph():
    graph = StateGraph(State)
    nodes = [('requirements', requirements), ('budget', budget), ('vendor', vendor),
             ('schedule', schedule), ('creative', creative), ('review', review)]
    previous = START
    for name, function in nodes:
        graph.add_node(name, function)
        graph.add_edge(previous, name)
        previous = name
    graph.add_edge(previous, END)
    return graph.compile()

def plan_event(brief):
    return build_graph().invoke({'brief': brief})
