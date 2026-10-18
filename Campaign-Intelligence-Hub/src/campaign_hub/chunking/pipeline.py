import hashlib
import tiktoken
from campaign_hub.models import Chunk
from campaign_hub.ingestion.markdown import sections, anchor


def tokens(text):
    return tiktoken.get_encoding('cl100k_base').encode(text)


def chunk_documents(documents, strategy='semantic'):
    if strategy not in ('fixed','semantic'):
        raise ValueError('Unknown chunking strategy')
    encoder = tiktoken.get_encoding('cl100k_base')
    result = []
    for doc in documents:
        parts = list(sections(doc.text))
        groups = parts if strategy == 'semantic' else [('Document', '\n\n'.join(f'## {h}\n{b}' for h,b in parts))]
        for heading, body in groups:
            encoded = tokens(body)
            for start in range(0, len(encoded), 450):
                text = encoder.decode(encoded[start:start+500])
                # Fixed chunks may span sections; keep all matching anchors for audit.
                names = [h for h,b in parts if h in text or (text[:40].strip() and text[:40].strip() in b)] if strategy=='fixed' else [heading]
                if not names:
                    names = [heading]
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                cid = f"{doc.metadata['document_id']}:{strategy}:{anchor(heading)}:{start}:{content_hash[:8]}"
                result.append(Chunk(chunk_id=cid, text=text, metadata={**doc.metadata, 'section_name': heading,
                    'section_anchor': anchor(heading), 'section_anchors': '|'.join(anchor(n) for n in names),
                    'token_count': len(tokens(text)), 'chunking': strategy, 'tokenizer': 'cl100k_base', 'chunk_hash':content_hash}))
                if start+500 >= len(encoded):
                    break
    return result
