import json

import httpx

headers = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
payload = {
    'jsonrpc': '2.0',
    'id': 2,
    'method': 'tools/call',
    'params': {
        'name': 'corpus_search',
        'arguments': {
            'query': 'covert action assassination',
            'corpus': 'cia',
            'limit': 2
        }
    }
}
r = httpx.post('https://mcp.declassification-engine.org/mcp', json=payload, headers=headers, timeout=15)
lines = [l for l in r.text.split('\n') if l.startswith('data: ')]
if lines:
    res = json.loads(lines[0][6:])
    print("Search Result:", json.dumps(res, indent=2)[:800])
