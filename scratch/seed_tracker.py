import json
import re
from pathlib import Path

p = Path("D:/sovereign_distillation/curated_dataset/distilled_sovereign_r1.jsonl")
t = Path("D:/sovereign_distillation/processed_files.json")

s = set()
if p.exists():
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                data = json.loads(line)
                convs = data.get("conversations", [])
                if len(convs) > 1:
                    human_txt = convs[1]["value"]
                    m = re.search(r"record\s+([A-Za-z0-9_\-]+)", human_txt)
                    if m:
                        s.add(m.group(1))
            except Exception:
                pass

print(f"Discovered {len(s)} existing documents already in dataset: {list(s)[:5]}")
t.write_text(json.dumps(sorted(list(s)), indent=2), encoding="utf-8")
