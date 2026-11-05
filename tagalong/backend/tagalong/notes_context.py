"""Bounded, request-local excerpts of saved Notes; no indexing dependency."""
import copy
import re


def merge_evidence(notes, history, documents_total):
    """Reserve two slots for verified history, using spare slots for Notes."""
    history_slots = min(2, len(history))
    selected_notes = notes[:6 - history_slots]
    selected = selected_notes + history[:6 - len(selected_notes)]
    included = [item for item in selected if item.get('kind') == 'document']
    return selected, {'documents_total': documents_total, 'documents_included': len(included),
                      'context_truncated': len(included) < documents_total or any(item.get('excerpt_truncated', False) for item in included)}


def notes_context(documents, message):
    terms = set(re.findall(r'\w{3,}', message.casefold()))

    def score(document):
        text = (document['title'] + ' ' + document['text']).casefold()
        return sum(term in text for term in terms)

    ranked = sorted(documents, key=score, reverse=True)
    sources = []
    for document in ranked[:6]:
        item = copy.deepcopy(document)
        text = item['text']
        # Keep a relevant window even when the matching fact is late in a Note.
        positions = [text.casefold().find(term) for term in terms]
        positions = [position for position in positions if position >= 0]
        start = max(0, min(positions) - 750) if positions and len(text) > 3000 else 0
        start = min(start, max(0, len(text) - 3000))
        item['text'] = text[start:start + 3000]
        item['excerpt_truncated'] = len(item['text']) < len(text)
        item['excerpt_start'] = start
        sources.append(item)
    return sources, {'documents_total': len(documents), 'documents_included': len(sources),
                     'context_truncated': len(documents) > len(sources) or any(x['excerpt_truncated'] for x in sources)}
