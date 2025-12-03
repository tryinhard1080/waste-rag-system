"""Test the RAG API"""
import requests
import json

url = 'http://localhost:5000/api/query'
data = {
    "question": "What are the main waste management issues?",
    "max_chunks": 5
}

print("Testing RAG API...")
print(f"URL: {url}")
print(f"Question: {data['question']}")
print("")

try:
    response = requests.post(url, json=data)
    result = response.json()

    print(f"Status: {result.get('status')}")
    print(f"Question: {result.get('question')}")
    print(f"Chunks found: {result.get('chunks_found')}")
    print("")
    print("Answer:")
    print("=" * 80)
    print(result.get('answer', 'No answer'))[:500]
    print("=" * 80)

except Exception as e:
    print(f"Error: {e}")
