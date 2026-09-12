import json

import httpx

headers = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
r = httpx.post('https://mcp.declassification-engine.org/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}, headers=headers, timeout=10)
lines = [l for l in r.text.split('\n') if l.startswith('data: ')]
if lines:
    data = json.loads(lines[0][6:])
    tools = data['result']['tools']
    for t in tools:
        print(f" - {t['name']}: {t['description'][:80]}...")
