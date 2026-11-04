"""Explicitly seed a pre-created 1536-dimensional cosine Pinecone index.
Run from project root: python -m scripts.seed_pinecone
This incurs OpenAI embedding and Pinecone usage charges.
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from convene.integrations import DATA

def main():
    load_dotenv()
    vendors = json.loads(DATA.read_text(encoding='utf-8'))
    client = OpenAI()
    vectors = []
    for vendor in vendors:
        embedding = client.embeddings.create(model='text-embedding-3-small',
            input=json.dumps(vendor)).data[0].embedding
        vectors.append({'id': vendor['id'], 'values': embedding, 'metadata': vendor})
    index = Pinecone(api_key=os.environ['PINECONE_API_KEY']).Index(os.environ['PINECONE_INDEX'])
    index.upsert(vectors=vectors, namespace='convene-synthetic')
    print(f'Seeded {len(vectors)} synthetic vendors. Index visibility may be delayed.')

if __name__ == '__main__':
    main()
