from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    campaign_id: str
    period: str
    options: object
    use_llm: bool
    report: object
    plan: list[str]


def build_workflow(service):
    graph=StateGraph(State)
    def understand(state):
        return {'plan':['brief','success_plan','performance_report','historical_deck','best_practice']}
    def generate(state):
        return {'report':service.report_sections(state['campaign_id'],state['period'],state['options'],state.get('use_llm',True))}
    def validate(state):
        r=state['report']
        allowed=set(r.evidence)
        for section in r.sections:
            for claim in section.claims:
                if not claim.citations or not set(claim.citations)<=allowed:
                    raise ValueError('Unsupported citation in generated report')
        return {'report':r}
    graph.add_node('query_understanding',understand)
    graph.add_node('retrieve_rerank_generate_sections',generate)
    graph.add_node('citation_validation',validate)
    graph.add_edge(START,'query_understanding')
    graph.add_edge('query_understanding','retrieve_rerank_generate_sections')
    graph.add_edge('retrieve_rerank_generate_sections','citation_validation')
    graph.add_edge('citation_validation',END)
    return graph.compile()
