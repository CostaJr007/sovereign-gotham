import json

import httpx

headers = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
payload = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/call',
    'params': {'name': 'list_corpora', 'arguments': {}}
}
r = httpx.post('https://mcp.declassification-engine.org/mcp', json=payload, headers=headers, timeout=15)
lines = [l for l in r.text.split('\n') if l.startswith('data: ')]
if lines:
    res = json.loads(lines[0][6:])
    print("Corporas Result:", json.dumps(res, indent=2)[:800])
