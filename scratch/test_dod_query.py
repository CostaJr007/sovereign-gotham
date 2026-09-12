import httpx

q = 'mediatype:(texts) AND title:(Department of Defense)'
r = httpx.get(
    'https://archive.org/advancedsearch.php',
    params={'q': q, 'fl[]': ['identifier', 'title', 'date'], 'rows': 5, 'page': 1, 'output': 'json'},
    timeout=15
)
docs = r.json().get('response', {}).get('docs', [])
for d in docs:
    ident = d['identifier']
    url = f"https://archive.org/download/{ident}/{ident}_djvu.txt"
    try:
        head = httpx.head(url, timeout=10, follow_redirects=True)
        print(ident, head.status_code, d.get('title', '')[:40])
    except Exception as e:
        print(ident, 'error', e)
