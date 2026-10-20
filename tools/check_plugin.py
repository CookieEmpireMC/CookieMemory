#!/usr/bin/env python3
"""Check the cookie-memory marketplace and the bakery-team plugin (standard library only)."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "bakery-team")
AGENT_FIELDS = {"name", "description", "tools", "model", "isolation", "memory", "skills", "color"}
problems = []


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{path}: no frontmatter")
        return {}
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+- ", line) and key:
            fields[key] = (fields[key] or []) + [line.strip()[2:]]
        elif ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip() or None
    return fields


market = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
plugin = json.load(open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")))
json.load(open(os.path.join(PLUGIN, "hooks", "hooks.json")))
entries = {p["name"]: p for p in market.get("plugins", [])}
if market.get("name") != "cookie-memory":
    problems.append("marketplace name must be cookie-memory")
if "bakery-team" not in entries or plugin.get("name") != "bakery-team":
    problems.append("marketplace entry and plugin.json must both be named bakery-team")
if "version" in plugin or "version" in entries.get("bakery-team", {}):
    problems.append("no version field: every commit is a new version")

skills = set(os.listdir(os.path.join(PLUGIN, "skills")))
for name in sorted(skills):
    fm = frontmatter(os.path.join(PLUGIN, "skills", name, "SKILL.md"))
    if fm.get("name") != name:
        problems.append(f"skill {name}: frontmatter name must be {name}")
for f in sorted(os.listdir(os.path.join(PLUGIN, "agents"))):
    fm = frontmatter(os.path.join(PLUGIN, "agents", f))
    if fm.get("name") != f[:-3]:
        problems.append(f"agent {f}: name must match the file name")
    if not fm.get("description"):
        problems.append(f"agent {f}: description missing")
    unknown = set(fm) - AGENT_FIELDS
    if unknown:
        problems.append(f"agent {f}: fields ignored for plugin agents or unknown: {sorted(unknown)}")
    for s in fm.get("skills") or []:
        if s not in skills:
            problems.append(f"agent {f}: preloads missing skill {s}")
    if fm.get("memory") != "project":
        problems.append(f"agent {f}: memory must be project")

for p in problems:
    print("problem:", p)
print(f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
