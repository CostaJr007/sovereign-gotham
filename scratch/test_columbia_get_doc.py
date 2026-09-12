import json

import httpx

headers = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
payload = {
    'jsonrpc': '2.0',
    'id': 3,
    'method': 'tools/call',
    'params': {
        'name': 'get_document',
        'arguments': {
            'doc_id': 'CIA-RDP78T03194A000100010001-2'
        }
    }
}
r = httpx.post('https://mcp.declassification-engine.org/mcp', json=payload, headers=headers, timeout=15)
lines = [l for l in r.text.split('\n') if l.startswith('data: ')]
if lines:
    res = json.loads(lines[0][6:])
    text_content = res.get('result', {}).get('content', [{}])[0].get('text', '')
    print("Fetched Full Doc Length:", len(text_content), "chars")
    print("Preview:\n", text_content[:400])
