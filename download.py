import json, subprocess, time, os, re, sys, urllib.parse
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://htsfwb.samr.gov.cn"
ROOT = "/var/minis/workspace/samr_contracts/dl"

items = json.load(open("/var/minis/workspace/samr_contracts/catalog.json"))


def safe(s):
    s = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", s).strip().strip(".")
    return s[:120] or "untitled"


def parse_name(hdr):
    m = re.search(r"filename\*=UTF-8''([^;\r\n]+)", hdr or "")
    if m:
        return urllib.parse.unquote(m.group(1))
    return None


def one(args):
    it, typ = args
    iid = it["Id"]
    dept = safe(it.get("Department") or "未知部门")
    if it.get("IsLocal"):
        sub = "地方_" + safe(it.get("Region") or "未知地区")
    else:
        sub = "部委"
    d = os.path.join(ROOT, sub, dept)
    os.makedirs(d, exist_ok=True)
    tagext = ".doc" if typ == 1 else ".pdf"
    url = f"{BASE}/api/File/DownTemplate?id={iid}&type={typ}"
    tmp = f"/tmp/dl_{iid}_{typ}.part"
    for attempt in range(4):
        r = subprocess.run(["curl", "-sL", "--max-time", "180", "-A", UA,
                            "-H", "Referer: " + BASE + "/View?id=" + iid,
                            "-D", tmp + ".hdr", "-o", tmp, url],
                           capture_output=True, text=True)
        if os.path.exists(tmp) and os.path.getsize(tmp) > 1000:
            hdr = open(tmp + ".hdr", errors="ignore").read()
            if "attachment" in hdr or "octet-stream" in hdr or "/pdf" in hdr or "msword" in hdr:
                name = parse_name(hdr) or (safe(it["Title"]) + tagext)
                ext = os.path.splitext(name)[1] or tagext
                fn = safe(it["Title"]) + ext
                # avoid collisions
                final = os.path.join(d, fn)
                k = 1
                while os.path.exists(final) and os.path.getsize(final) > 1000:
                    base, e = os.path.splitext(fn)
                    final = os.path.join(d, f"{base}_{k}{e}")
                    k += 1
                os.replace(tmp, final)
                for f in (tmp + ".hdr",):
                    if os.path.exists(f):
                        os.remove(f)
                return ("ok", sub, fn, os.path.getsize(final))
        time.sleep(2 + attempt * 2)
    return ("fail", sub, it["Title"], typ)


jobs = [(it, t) for it in items for t in (1, 2)]
print("jobs:", len(jobs), flush=True)
ok = fail = 0
fails = []
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    for i, res in enumerate(ex.map(one, jobs), 1):
        if res[0] == "ok":
            ok += 1
        else:
            fail += 1
            fails.append(res)
        if i % 50 == 0:
            print(f"{i}/{len(jobs)} ok={ok} fail={fail} {time.time()-t0:.0f}s", flush=True)

json.dump(fails, open("/var/minis/workspace/samr_contracts/fails.json", "w"), ensure_ascii=False, indent=1)
print("DONE ok=", ok, "fail=", fail, flush=True)
