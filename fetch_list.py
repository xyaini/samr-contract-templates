import json, subprocess, time, os, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://htsfwb.samr.gov.cn"
OUT = "/var/minis/workspace/samr_contracts"

def get(url, ref=BASE + "/List"):
    for attempt in range(4):
        r = subprocess.run(["curl", "-sL", "--max-time", "60", "-A", UA,
                            "-H", "Referer: " + ref, url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try:
                return json.loads(r.stdout)
            except Exception:
                pass
        time.sleep(2)
    return None

items = []
for loc in ("false", "true"):
    first = get(f"{BASE}/api/content/SearchTemplates?loc={loc}&p=1")
    if not first:
        print("FAIL", loc); continue
    tp = first["TotalPage"]
    print(loc, "total", first["Total"], "pages", tp, flush=True)
    items.extend(first["Data"])
    for p in range(2, tp + 1):
        d = get(f"{BASE}/api/content/SearchTemplates?loc={loc}&p={p}")
        if not d:
            print("  page fail", p); continue
        items.extend(d["Data"])
    time.sleep(0.5)

# dedupe by Id
seen = {}
for it in items:
    seen[it["Id"]] = it
items = list(seen.values())
json.dump(items, open(f"{OUT}/catalog.json", "w"), ensure_ascii=False, indent=1)
print("unique items:", len(items))
from collections import Counter
print(Counter(i["IsLocal"] for i in items))
