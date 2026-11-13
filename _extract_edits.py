import json
import os

p = r"C:/Users/27390/.claude/projects/d--Short-drama-delivery-platform/032abe3e-36f0-4068-b017-bf1215845a45.jsonl"
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
            name = it.get("name")
            if it.get("type") == "tool_use" and name in ("Edit", "Write", "Bash"):
                inp = it.get("input", {})
                fp = inp.get("file_path") or inp.get("path") or inp.get("command")[:60] if "command" in inp else ""
                old = inp.get("old_string") or ""
                new = inp.get("new_string") or ""
                old1 = old[:140].replace("\n", "\\n")
                new1 = new[:140].replace("\n", "\\n")
                print(f"[{i}] {name} | {fp} | old: {old1!r} | new: {new1!r}")