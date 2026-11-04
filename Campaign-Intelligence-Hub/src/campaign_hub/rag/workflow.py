"""Question-only LangGraph orchestration with an explicit refusal branch."""
import time
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from campaign_hub.models import FALLBACK, SearchHit
from campaign_hub.rag.grounding import grounded_answer


class QuestionState(TypedDict, total=False):
    analysis: dict
    result: dict
    steps: list[str]
    retrieval_seconds: float


def answer_workflow(service, question, campaign_id, options, filters, automatic,
                    classification_provider, classification_model):
    started = time.perf_counter()

    def retrieve(state):
        tick = time.perf_counter()
        analysis = service.analyze_query(question, options, filters, campaign_id, automatic,
                                        classification_provider, classification_model, answer_mode=True)
        return {'analysis': analysis, 'steps': ['retrieve'],
                'retrieval_seconds': time.perf_counter() - tick}

    def generate_and_validate(state):
        hits = [SearchHit.model_validate(hit) for hit in state['analysis']['hits']]
        return {'result': grounded_answer(service.settings, question, hits),
                'steps': state['steps'] + ['generate_and_validate']}

    def refuse(state):
        return {'result': {'answer': FALLBACK, 'faithfulness': None},
                'steps': state['steps'] + ['refuse']}

    def finalize(state):
        return {'result': {**state['analysis'], **state['result'],
                           'workflow_steps': state['steps'] + ['finalize'],
                           'retrieval_seconds': state['retrieval_seconds'],
                           'latency_seconds': time.perf_counter() - started}}

    graph = StateGraph(QuestionState)
    graph.add_node('retrieve', retrieve)
    graph.add_node('generate_and_validate', generate_and_validate)
    graph.add_node('refuse', refuse)
    graph.add_node('finalize', finalize)
    graph.add_edge(START, 'retrieve')
    graph.add_conditional_edges('retrieve', lambda state: 'generate_and_validate'
                               if state['analysis']['hits'] else 'refuse')
    graph.add_edge('generate_and_validate', 'finalize')
    graph.add_edge('refuse', 'finalize')
    graph.add_edge('finalize', END)
    return graph.compile().invoke({})['result']
