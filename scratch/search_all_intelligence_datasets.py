import httpx

queries = ['cia', 'crest', 'nsa', 'fbi', 'foia', 'declassified', 'pentagon', 'cointelpro', 'mkultra', 'diplomatic']
found = {}

print("Scanning Hugging Face for all intelligence and declassified datasets...")
for q in queries:
    try:
        r = httpx.get(f"https://huggingface.co/api/datasets?search={q}&limit=25", timeout=10)
        data = r.json()
        if isinstance(data, list):
            for d in data:
                did = d.get('id')
                if did and did not in found:
                    found[did] = {
                        'gated': d.get('gated', False),
                        'downloads': d.get('downloads', 0),
                        'likes': d.get('likes', 0),
                        'query': q
                    }
    except Exception as e:
        print(f"Error querying {q}: {e}")

print(f"\nFound {len(found)} intelligence datasets on Hugging Face.")
sorted_ds = sorted(found.items(), key=lambda x: x[1]['downloads'], reverse=True)

print("\n--- TOP HUGGING FACE INTELLIGENCE DATASETS ---")
for k, v in sorted_ds[:30]:
    gated_str = "LOCKED (Gated)" if v['gated'] else "OPEN (Ungated)"
    print(f" - {k:50} | {gated_str:15} | DLs: {v['downloads']:6} | Likes: {v['likes']:3}")
