import json

p = r"C:/Users/27390/.claude/projects/d--Short-drama-delivery-platform/032abe3e-36f0-4068-b017-bf1215845a45.jsonl"

# response-format edit line numbers to dump fully
want = {1311,1316,1319,1320,1321,1332,1333,1334,1335,1336,1337,1338,1339,1340,
        1375,1376,1413,1422,1441,1442,1443,1444,1445,1446,1477,1478,1479,
        1480,1481,1482,1483,1484,1485,1518,1519,1520,1521,1522,1523,1524,
        1525,1526,1527,1528,1529,1530,1531,1601,1602}

out = []
with open(p, encoding="utf-8") as f:
    for i, line in enumerate(f):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        content = (o.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for it in content:
            if not isinstance(it, dict):
                continue
            if it.get("type") != "tool_use" or it.get("name") != "Edit":
                continue
            inp = it.get("input", {})
            fp = inp.get("file_path", "") or ""
            # capture tests.py edits + wanted indices
            if i in want or (fp and "tests.py" in fp):
                out.append({"idx": i, "file": fp,
                            "old": inp.get("old_string", ""),
                            "new": inp.get("new_string", "")})

with open(r"d:/Short drama delivery platform/_revert_edits.json", "w", encoding="utf-8") as g:
    json.dump(out, g, ensure_ascii=False, indent=1)

for r in out:
    print(f"[{r['idx']}] {r['file']} | old_len={len(r['old'])} new_len={len(r['new'])}")