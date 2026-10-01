"""Diff every DataTable in build/visions_mod/assets against extracted/rows: pre-existing rows must be unchanged
unless they are listed in EXPECTED (rows the mod edits on purpose). Exit code 1 on unexpected changes.
usage: python tools/verify_mod.py"""
import glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools")); import ffrenv
BASE = os.path.join(ROOT, "build", "visions_mod", "assets", "FFRS", "Content", "Datatable")
TMP = os.path.join(ROOT, "build", "visions_mod", "verify")
UNUSED_ICON_TAGS = [13104, 13106, 13107, 13109, 13111, 13112, 13114, 13115, 13117, 13119, 13121, 13122, 13126, 13129, 13131, 13132]
def icon_rows(rel):
    """placeholder icon rows the generator overwrites: one per unit in units.json (borrowed unused command-icon tags)"""
    spec = os.path.join(ROOT, "mods", "EstherTsukiko", "units.json")
    n = len(json.load(open(spec, encoding="utf-8"))) if os.path.exists(spec) else 5
    tags = {f"UI.Skill.Command.Icon.{t}" for t in UNUSED_ICON_TAGS[:n]}
    rows = json.load(open(os.path.join(ROOT, "extracted", "rows", rel + ".json"), encoding="utf-8"))["rows"]
    return {k for k, v in rows.items() if v.get("Tag", {}).get("TagName") in tags}
def expected_rows():
    return {   # table -> rows the generator edits in place
        "Shop/DT_ShopList": {"ミトラ_道具　1章"},
        "UI/Skill/DT_CommandSkillIcon": icon_rows("UI/Skill/DT_CommandSkillIcon"),
        "UI/Skill/CDT_SkillIcon": icon_rows("UI/Skill/CDT_SkillIcon"),
    }


def equivalent(a, b):
    """UAssetAPI may serialize signed floating zero as a string or a number."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    if type(a) is str and a in ("+0", "-0") and type(b) in (int, float):
        return b == 0
    if type(b) is str and b in ("+0", "-0") and type(a) in (int, float):
        return a == 0
    return a == b

def main():
    expected = expected_rows()
    os.makedirs(TMP, exist_ok=True)
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    bad = 0
    for ua in sorted(glob.glob(os.path.join(BASE, "**", "*.uasset"), recursive=True)):
        rel = os.path.relpath(ua, BASE).replace("\\", "/")[:-7]
        orig_p = os.path.join(ROOT, "extracted", "rows", rel + ".json")
        if not os.path.exists(orig_p):
            print(f"[new package] {rel}"); continue
        orig = json.load(open(orig_p, encoding="utf-8"))
        if "rows" not in orig:
            print(f"[not a table] {rel}"); continue
        out = os.path.join(TMP, rel.replace("/", "_") + ".json")
        r = subprocess.run(ffrenv.FFRDT + ["rows", ua, out, "--usmap", os.path.join(ROOT, "extracted", "Mappings.usmap")],
                           capture_output=True, text=True, env=env)
        if r.returncode:
            print(f"ROWS FAILED {rel}: {r.stderr[-300:]}"); bad += 1; continue
        built = json.load(open(out, encoding="utf-8"))["rows"]; orig = orig["rows"]
        changed = [k for k in orig if k in built and not equivalent(built[k], orig[k])]
        missing = [k for k in orig if k not in built]
        added = [k for k in built if k not in orig]
        unexpected = [k for k in changed if k not in expected.get(rel, set())] + missing
        flag = "  !! UNEXPECTED: " + ", ".join(unexpected) if unexpected else ""
        print(f"{rel}: {len(orig)}->{len(built)} rows, +{len(added)}, changed {len(changed)}{flag}")
        if unexpected: bad += 1
    print("OK: no pre-existing row changed unexpectedly" if not bad else f"FAILED: {bad} table(s) with unexpected changes")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
