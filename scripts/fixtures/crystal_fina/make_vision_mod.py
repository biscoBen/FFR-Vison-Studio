#!/usr/bin/env python
r"""make_vision_mod.py - build the "Esther & Tsukiko" Vision mod.

Generates build/visions_mod/patch.json from the unit specs below, runs `ffr-dt patch` (clones/edits DataTable rows and
renames copied menu/icon packages), then packs + installs the mod with tools/build_mod.py.

usage: python tools/make_vision_mod.py [--no-install]

Each new Vision borrows a donor Vision's sprites (Ss6Project + textures), level table and battle visuals, and gets its own
rows in: UNIT_PARAMETER, VISION_ITEM_DATA, COMMAND_SKILL_DATA, MASTER_SKILL_DATA, SKILL_DATA (cloned skills),
SKILL_ASSET_DATA, VISION_AWAKENING/SYNCHRO_MASTERY, UNIT_ASSET_DATA, BTL_UNIT_DESIGN_PARAMETER, VisionUpgradeData,
plus a slot in the Mitra tool shop. Names are written as literal (culture-invariant) text so no locres edit is needed.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS = os.path.join(ROOT, "extracted", "rows")
LEGACY = os.path.join(ROOT, "extracted", "legacy")
USMAP = os.path.join(ROOT, "extracted", "Mappings.usmap")
BUILD = os.path.join(ROOT, "build", "visions_mod")
OUT = os.path.join(BUILD, "assets")
sys.path.insert(0, os.path.join(ROOT, "tools")); import ffrenv
import ffbe_resonance
import ffbe_lb
import ffbe_audio
FFRDT = ffrenv.FFRDT          # command prefix (dotnet + dll from the source tree, bin/ffr-dt.exe when packaged)
DT = "FFRS/Content/Datatable/"

def rows(rel):
    p = os.path.join(ROWS, rel + ".json")
    if not os.path.exists(p):                                 # a dump the preparation lost: make it now, or say exactly what is missing
        legacy = os.path.join(LEGACY, "FFRS", "Content", "Datatable", rel + ".uasset")
        if os.path.exists(legacy):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            r = subprocess.run(FFRDT + ["rows", legacy, p, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0 or not os.path.exists(p):
                sys.exit(f"the game table {rel} could not be read: {(r.stderr or r.stdout).strip()[-300:]}. Prepare the game's data again from the studio.")
        else:
            sys.exit(f"the game table {rel} was never extracted (extracted/legacy/.../Datatable/{rel}.uasset is missing). Prepare the game's data again from the studio.")
    return json.load(open(p, encoding="utf-8"))["rows"]

def row_by(rel, field, value, extra=None):
    for k, v in rows(rel).items():
        if v.get(field) == value and (extra is None or extra(v)):
            return k, v
    raise KeyError(f"{rel}: no row with {field}={value}")

# ---------------------------------------------------------------- unit specs
UNITS = [
    {
        "key": "esther", "jp": "エスター", "en": "Esther", "id": 13201, "sort": 13270,
        "desc": "A vision of Esther, a Precursor who chases storms. Fights with lightning-fast strikes.",
        "donor": 13125,                       # Lightning: level table (10013), battle visuals, project template
        "ffbe": {"dir": "units/ffbe/esther/sprites/401006807", "id": "401006807"},   # own sprites converted from FFBE
        "attackType": "Physic", "roles": ["eUnitRole::Attacker"],
        "stats": {"MaxHitPoint": 780, "MaxMagicPoint": 100, "Attack": 29, "Defence": 27, "Intelligence": 8, "Mind": 18, "Agility": 17},
        "elemRes": {"eElement::Thunder": "eResistance::Halved"},
        "command": {"id": 301, "en": "Esther's Skills", "desc": "Skills unique to Esther."},
        "master": {"id": 1320100, "en": "Spirit of Esther", "desc": "Esther's resonance flows into the wearer. Raises lightning damage."},
        "price": 1,
        # battle visuals are keyed by skill id (Sequencer/Battle/*/<id>, Effect/03_SKL/skl<id>, Movies/Skill/MV_Skill<id>),
        # so only existing skills play animations: no clones, LB = an existing Resonance.
        "lb": 440260,                         # Zantetsuken (Lightning): Thunder physical, 10 hits (used when lb_custom is absent)
        # custom Resonance under the derived id 441020: Zantetsuken's mechanics + hit effects + caption table, own name
        # mechanics + visuals from Tronn's Hibernal Fury (414090, one of the few Resonances with a sequence in the demo); the
        # sequence packages are copied under the new id with Tronn's voice sections muted; the caption table from Zantetsuken
        "lb_custom": {"from": 414090, "clone_sequence": True, "mute": ["VO_"], "caption_from": 440260,
                      "jp": "エスター_LB 雷切", "en": "Raikiri",
                      "desc": "Esther's Resonance. A storm of lightning-fast slashes tears through the enemy line.",
                      "set": {"element": "Thunder", "DamageType": "Physic", "damageCalcType": "Physic",
                              "SkillIcon.TagName": "UI.Skill.Action.Icon.Thunder"},
                      # the copied sequence, recoloured: yellow domain, ice bursts -> Thunderga effects (Dark Fina's set)
                      "sequence_edits": {"master": [{"match": {"EventType": "OtherChangeSubSpaceColor"},
                                                     "set": {"Other_ChangeSubSpaceColor_Color": {"R": 0.62, "G": 0.46, "B": 0.04, "A": 1.0}}}]},
                      "effect_swaps": [["/Game/Effect/03_SKL/skl414090", "/Game/Effect/03_SKL/skl408030"],
                                       ["NS_EF_SKL414090_Burst_001_Weapon", "NS_EF_SKL408030_BallThunder_001"],
                                       ["NS_EF_SKL414090_Charge_001_Weapon", "NS_EF_SKL408030_Thunderga_Charge_001"],
                                       ["NS_EF_SKL414090_Root", "NS_EF_SKL408030_Thunderga_001"]]},
        "skills": {   # custom skills: mechanics cloned from "from", visuals (sequencer / hit effects) borrowed from "visuals" (default: from)
            # Sacred Wave (Warrior of Light, all enemies, 1 hit) is the donor: it is one of the few vision abilities whose battle
            # sequence ships with the demo (Lightning Strike / Thunderfall have none, see the build log warnings)
            455100: {"from": 445020, "jp": "エスター_レーゲンブラスト", "en": "Raegen Blast",   # slot 0 of Esther's derived range
                     "desc": "Test skill. Deals no damage but staggers every enemy instantly.",
                     "set": {"magnification": 0, "breakDamageValue": 9999, "accuracy": 500, "Cost": 0, "element": "Thunder",
                             "SkillIcon.TagName": "UI.Skill.Action.Icon.Thunder",
                             "effectBundleList[0].effectId": -1, "effectBundleList[1].effectId": -1, "totalDamageDisplayRule": "Hidden"}},
        },
        "awakening": [   # 4 tiers, up to 8 grants each: (type, id)
            [("ActiveSkill", 455100), ("ActiveSkill", 447500), ("ActiveSkill", 421130), ("ActiveSkill", 230100), ("PassiveSkill", 1247), ("PassiveSkill", 1273)],   # Raegen Blast, Lightning Strike, Thunder Surge, Bravery
            [("ActiveSkill", 446010), ("ActiveSkill", 421140), ("ActiveSkill", 230130), ("PassiveSkill", 1250), ("PassiveSkill", 1277)],   # Cross-Slash, Thundara Surge, Haste
            [("ActiveSkill", 447510), ("ActiveSkill", 421150), ("ActiveSkill", 210120), ("PassiveSkill", 1279), ("PassiveSkill", 1309)],   # Thunderfall, Thundaga Surge, Esuna
            [("ActiveSkill", 446000), ("PassiveSkill", 1366), ("PassiveSkill", 1357)],                                                      # Braver
        ],
        "synchro": [  # 10 levels (0..9); None = keep donor row content
            [], [("PassiveSkill", 1323)], [("BaseParameter", 5, 5)], [("ActiveSkill", 400500)], [("BaseParameter", 11, 8)],
            [("PassiveSkill", 1400)], [("BaseParameter", 9, 5)], [("PassiveSkill", 1388)], [("BaseParameter", 5, 5)],
            [("PassiveSkill", 1234, 8), ("BaseParameter", 11, 8), ("MasterSkill", 1320100)],
        ],
    },
    {
        "key": "tsukiko", "jp": "ツキコ", "en": "Tsukiko", "id": 13202, "sort": 13280,
        "desc": "A vision of Tsukiko, a shrine maiden who commands the tides under the moon.",
        "donor": 13108,                       # Terra: level table (10006), battle visuals, project template
        "ffbe": {"dir": "units/ffbe/tsukiko/sprites/401007107", "id": "401007107"},
        "attackType": "Magic", "roles": ["eUnitRole::Attacker"],
        "stats": {"MaxHitPoint": 720, "MaxMagicPoint": 120, "Attack": 16, "Defence": 26, "Intelligence": 16, "Mind": 22, "Agility": 14},
        "elemRes": {"eElement::Water": "eResistance::Halved"},
        "command": {"id": 302, "en": "Tsukiko's Skills", "desc": "Skills unique to Tsukiko."},
        "master": {"id": 1320200, "en": "Spirit of Tsukiko", "desc": "Tsukiko's resonance flows into the wearer. Raises water damage."},
        "price": 1,
        "lb": 440090,                         # Riot Blade - Lotus (Terra): non-elemental magic, 7 hits, all enemies
        "skills": {},
        "awakening": [
            [("ActiveSkill", 220130), ("ActiveSkill", 225090), ("ActiveSkill", 210220), ("PassiveSkill", 1310), ("PassiveSkill", 1251)],   # Water, Water (all), Libra
            [("ActiveSkill", 220140), ("ActiveSkill", 225100), ("ActiveSkill", 230190), ("PassiveSkill", 1311), ("PassiveSkill", 1380)],   # Watera, Watera (all), Debrave
            [("ActiveSkill", 220150), ("ActiveSkill", 225110), ("ActiveSkill", 220300), ("PassiveSkill", 1275), ("PassiveSkill", 1315)],   # Waterga, Waterga (all), Drain
            [("ActiveSkill", 220340), ("PassiveSkill", 1367), ("PassiveSkill", 1304)],                                                      # Ultima
        ],
        "synchro": [
            [], [("PassiveSkill", 1332)], [("BaseParameter", 7, 5)], [("ActiveSkill", 400530)], [("BaseParameter", 11, 8)],
            [("PassiveSkill", 1381)], [("BaseParameter", 2, 10)], [("PassiveSkill", 1382)], [("BaseParameter", 7, 5)],
            [("PassiveSkill", 1234, 8), ("BaseParameter", 11, 8), ("MasterSkill", 1320200)],
        ],
    },
    {
        "key": "ariana", "jp": "アリアナ", "en": "Dangerous Ariana", "id": 13203, "sort": 13290,
        "desc": "A vision of Ariana, a singer from a faraway world. Her songs empower allies while lightning and darkness rain on her foes.",
        "donor": 13108,                       # Terra: level table, battle visuals, project template
        "ffbe": {"dir": "units/ffbe/ariana/sprites/401000106", "id": "401000106"},
        "attackType": "Magic", "roles": ["eUnitRole::Enhancer"],
        "stats": {"MaxHitPoint": 640, "MaxMagicPoint": 130, "Attack": 14, "Defence": 24, "Intelligence": 15, "Mind": 24, "Agility": 15},
        "elemRes": {"eElement::Dark": "eResistance::Halved"},
        "command": {"id": 303, "en": "Ariana's Songs", "desc": "Songs and spells unique to Ariana."},
        "master": {"id": 1320300, "en": "Spirit of Ariana", "desc": "Ariana's resonance flows into the wearer. Raises lightning and dark damage."},
        "price": 1,
        "lb": 440240,
        "lb_custom": {"from": 414100, "clone_sequence": True, "mute": ["VO_"], "caption_from": 440240,
                      "jp": "アリアナ_LB タッチ・イット", "en": "Touch It",
                      "desc": "Ariana's Resonance. A song that mends every ally's wounds.",
                      "set": {"SkillIcon.TagName": "UI.Skill.Action.Icon.Heal"},
                      "sequence_edits": {"master": [{"match": {"EventType": "OtherChangeSubSpaceColor"},
                                                     "set": {"Other_ChangeSubSpaceColor_Color": {"R": 0.10, "G": 0.10, "B": 0.11, "A": 1.0}}}]},
                      "effect_swaps": [["/Game/Effect/03_SKL/skl210010/NS_EF_SKL210010_Root", "/Game/Effect/04_BTL/BadStatusCharm/NS_EF_BTL_BadStatusCharm_Center"],
                                       ["NS_EF_SKL210010_Root", "NS_EF_BTL_BadStatusCharm_Center"]]},                         # Colossal Shantotto II: Dark magic, 10 hits
        "skills": {},
        "awakening": [
            [("ActiveSkill", 220090), ("ActiveSkill", 220390), ("ActiveSkill", 230100), ("ActiveSkill", 210220), ("PassiveSkill", 1310), ("PassiveSkill", 1380)],   # Thunder, Dark, Bravery, Libra
            [("ActiveSkill", 220100), ("ActiveSkill", 220520), ("ActiveSkill", 230110), ("ActiveSkill", 230150), ("PassiveSkill", 1311), ("PassiveSkill", 1250)],   # Thundara, Darkra, Faith, Slow
            [("ActiveSkill", 220110), ("ActiveSkill", 220400), ("ActiveSkill", 225080), ("ActiveSkill", 230130), ("PassiveSkill", 1381), ("PassiveSkill", 1315)],   # Thundaga, Darkga, Thundaga (all), Haste
            [("ActiveSkill", 225270), ("ActiveSkill", 220300), ("PassiveSkill", 1275), ("PassiveSkill", 1304)],                                                     # Darkga (all), Drain
        ],
        "synchro": [
            [], [("PassiveSkill", 1332)], [("BaseParameter", 7, 5)], [("ActiveSkill", 400530)], [("BaseParameter", 11, 8)],
            [("PassiveSkill", 1381)], [("BaseParameter", 2, 10)], [("PassiveSkill", 1382)], [("BaseParameter", 7, 5)],
            [("PassiveSkill", 1234, 8), ("BaseParameter", 11, 8), ("MasterSkill", 1320300)],
        ],
    },
    {
        "key": "katy", "jp": "ケイティ", "en": "A.I. Katy", "id": 13204, "sort": 13300,
        "desc": "A vision of Katy, an artificial intelligence from a faraway world. Runs combat directives that strike, shield and heal.",
        "donor": 13125,                       # Lightning: level table, battle visuals, project template
        "ffbe": {"dir": "units/ffbe/katy/sprites/401007407", "id": "401007407"},
        "attackType": "Physic", "roles": ["eUnitRole::Attacker", "eUnitRole::Healer"],
        "stats": {"MaxHitPoint": 800, "MaxMagicPoint": 110, "Attack": 26, "Defence": 28, "Intelligence": 18, "Mind": 22, "Agility": 15},
        "elemRes": {"eElement::Light": "eResistance::Halved"},
        "command": {"id": 304, "en": "Katy's Directives", "desc": "Combat directives unique to Katy."},
        "master": {"id": 1320400, "en": "Spirit of Katy", "desc": "Katy's resonance flows into the wearer. Raises physical and magic attack."},
        "price": 1,
        "lb": 440290,                         # Armiger Unleashed (Noctis): physical, 10 hits
        "skills": {},
        "awakening": [
            [("ActiveSkill", 446000), ("ActiveSkill", 210220), ("ActiveSkill", 210010), ("ActiveSkill", 220300), ("PassiveSkill", 1309), ("PassiveSkill", 1311)],   # Braver, Libra, Cure, Drain
            [("ActiveSkill", 446010), ("ActiveSkill", 230190), ("ActiveSkill", 210020), ("ActiveSkill", 230040), ("PassiveSkill", 1380), ("PassiveSkill", 1273)],   # Cross-Slash, Debrave, Cura, Protect
            [("ActiveSkill", 230060), ("ActiveSkill", 210030), ("ActiveSkill", 210140), ("ActiveSkill", 220340), ("PassiveSkill", 1279), ("PassiveSkill", 1315)],   # Shell, Curaga, Raise, Ultima
            [("ActiveSkill", 220350), ("PassiveSkill", 1275), ("PassiveSkill", 1357)],                                                                              # Meteor
        ],
        "synchro": [
            [], [("PassiveSkill", 1323)], [("BaseParameter", 5, 5)], [("ActiveSkill", 400500)], [("BaseParameter", 11, 8)],
            [("PassiveSkill", 1400)], [("BaseParameter", 9, 5)], [("PassiveSkill", 1388)], [("BaseParameter", 5, 5)],
            [("PassiveSkill", 1234, 8), ("BaseParameter", 11, 8), ("MasterSkill", 1320400)],
        ],
    },
    {
        "key": "orlandeau", "jp": "オルランドゥ", "en": "Sword Saint Orlandeau", "id": 13205, "sort": 13310,
        "desc": "A vision of Orlandeau, the Thunder God of Ivalice. Holy and lightning swordplay that few can withstand.",
        "donor": 13125,                       # Lightning: level table, battle visuals, project template
        "ffbe": {"dir": "units/ffbe/orlandeau/sprites/253000807", "id": "253000807"},
        "attackType": "Physic", "roles": ["eUnitRole::Attacker", "eUnitRole::Breaker"],
        "stats": {"MaxHitPoint": 820, "MaxMagicPoint": 100, "Attack": 30, "Defence": 30, "Intelligence": 10, "Mind": 20, "Agility": 16},
        "elemRes": {"eElement::Light": "eResistance::Halved"},
        "command": {"id": 305, "en": "Orlandeau's Swordplay", "desc": "Holy swordplay unique to Orlandeau."},
        "master": {"id": 1320500, "en": "Spirit of Orlandeau", "desc": "Orlandeau's resonance flows into the wearer. Raises light and lightning damage."},
        "price": 1,
        "lb": 440040,                         # Knight of Duality (Cecil): Light physical, 8 hits
        "skills": {},
        "awakening": [
            [("ActiveSkill", 420330), ("ActiveSkill", 420070), ("ActiveSkill", 230100), ("PassiveSkill", 1247), ("PassiveSkill", 1273)],   # Banish Blade, Thunder Blade, Bravery
            [("ActiveSkill", 420340), ("ActiveSkill", 420080), ("ActiveSkill", 446010), ("PassiveSkill", 1250), ("PassiveSkill", 1277)],   # Banishra Blade, Thundara Blade, Cross-Slash
            [("ActiveSkill", 420350), ("ActiveSkill", 420090), ("ActiveSkill", 445020), ("PassiveSkill", 1279), ("PassiveSkill", 1309)],   # Banishga Blade, Thundaga Blade, Sacred Wave
            [("ActiveSkill", 445300), ("ActiveSkill", 446000), ("PassiveSkill", 1366), ("PassiveSkill", 1357)],                             # Moonlightbringer, Braver
        ],
        "synchro": [
            [], [("PassiveSkill", 1323)], [("BaseParameter", 5, 5)], [("ActiveSkill", 400500)], [("BaseParameter", 11, 8)],
            [("PassiveSkill", 1400)], [("BaseParameter", 9, 5)], [("PassiveSkill", 1388)], [("BaseParameter", 5, 5)],
            [("PassiveSkill", 1234, 8), ("BaseParameter", 11, 8), ("MasterSkill", 1320500)],
        ],
    },
]

SPEC_JSON = os.path.join(ROOT, "mods", "EstherTsukiko", "units.json")
def load_units():
    """the dev UI (tools/devui) keeps the specs in units.json; the Python list above is the fallback / seed"""
    if os.path.exists(SPEC_JSON):
        units = json.load(open(SPEC_JSON, encoding="utf-8"))
        for u in units:
            u["skills"] = {int(k): v for k, v in (u.get("skills") or {}).items()}
        return units
    return UNITS
UNITS = load_units()

SHOP_ROW = "ミトラ_道具　1章"   # Mitra item shop, chapter 1 (potion / phoenix down / antidote herb / smoke bomb)
# motions a custom skill's "motion" override rewrites in the copied sequence's Cut track
MOTION_NAMES = ["magic_idle", "magic_attack", "M_attack01", "M_attack02", "attack_A", "LB1"]
# gameplay tags UI.Skill.Command.Icon.<id> exist in DefaultGameplayTags.ini for vision ids that are not in the demo; one per custom unit
UNUSED_ICON_TAGS = [13104, 13106, 13107, 13109, 13111, 13112, 13114, 13115, 13117, 13119, 13121, 13122, 13126, 13129, 13131, 13132]

def text(s):
    return s  # literal culture-invariant FText

# Every vision's own skills use ids derived from the vision id: unique abilities at 445000 + (vid - 13100) * 100 + 10 * slot
# (Cloud 13110 -> 446000 Braver, 446010 Cross-Slash; Lightning 13125 -> 447500, 447510) and the Resonance (FinishBlow) at
# 440000 + (vid - 13099) * 10 (13110 -> 440110 Climhazzard, 13125 -> 440260 Zantetsuken). A cloned ability outside that range
# (v10's 470110) ran its mechanics but showed no motion or hit effects, so custom skills must follow the scheme.
def unique_skill_base(vid): return 445000 + (vid - 13100) * 100
def lb_id(vid): return 440000 + (vid - 13099) * 10

_utoc = None
def utoc_files():
    global _utoc
    if _utoc is None:
        _utoc = {l.split("	")[1].strip().replace("../../../FFRS/Content/", "") for l in open(os.path.join(ROOT, "extracted", "utoc_filelist.tsv"), encoding="utf-8") if "	" in l}
    return _utoc

# The demo's three "owner" Resonances (Warrior of Light, Terra, Cloud) stage the fight without Tronn's and Leah's domain,
# which is why they look better on a ported unit -- but they open with a CriWare CG movie of the owner, carry the owner's
# caption dialogue, and finish with the owner's own effects on the targets. `apply_cinematic` keeps the staging and cuts the
# rest: the movie layer never becomes visible (`movie_ops` also empties the movie itself), the dialogue is silenced, the
# owner's target effects go (or the player's chosen one takes the first slot), only the first trigger of the unit's motion
# survives, and every key from that motion onward is pulled to the front so the Resonance is short instead of a 24 s wait.
# Times are the templates' own key times, measured from the game's Cut / Master tracks (docs/09 section 4).
CINEMATIC = {
    # `tail`: Ascension idles for 4.4 s between the unit's recovery and its last camera key; pulled in as well (applied first,
    # so the main trim's tick reference is still the template's own timeline).
    440110: {"lb1": 14.83, "start": 1.5, "single_lb1": True, "tail": {"after": 23.6, "delta": -3.9},
             "target_fx": ["/Game/Effect/03_SKL/skl440110/NS_EF_SKL440110_Slash_002_Center",
                           "/Game/Effect/03_SKL/skl440110/NS_EF_SKL440110_Slash_001_Root",
                           "/Game/Effect/03_SKL/skl440110/NS_EF_SKL440110_Finish_001"]},
}

def apply_cinematic(s, vis):
    """`lb_custom` -> the same with the owner's cinematic taken out of the copy. `target_effect`: None = nothing on the
    targets (the hits still land), "keep" = the owner's own effects, or a Niagara package path to put there instead."""
    rec = CINEMATIC.get(vis)
    if not rec or s.get("no_cinematic") is False: return s
    s = dict(s); s["clone_sequence"] = True
    ed = {k: list(v) for k, v in (s.get("sequence_edits") or {}).items()}
    ed.setdefault("master", []).extend([
        {"match": {"EventType": "UISetVisibility"}, "set": {"EventType": "None"}},              # shows / hides the movie layer
        {"match": {"EventType": "OtherTalkPlay"}, "set": {"EventType": "None"}},                # the owner's caption dialogue
        {"match": {"EventType": "OtherSetVisibleCaptionWindow"}, "set": {"EventType": "None"}},
    ])
    if rec.get("single_lb1"):     # the template triggers the motion twice; the second cuts a long motion off
        ed.setdefault("cut", []).append({"match": {"EventType": "UnitPlayAnimByName", "Unit_PlayAnimByName_AnimationName": "LB1"},
                                         "skip_earliest": 1, "set": {"EventType": "None"}})
    fx = list(rec.get("target_fx") or [])
    chosen = s.get("target_effect")
    swaps = [list(x) for x in (s.get("effect_swaps") or [])]
    if chosen and chosen != "keep":
        keep = fx.pop(0)                                   # the first slot plays where the owner's main hit played
        swaps += [[keep, chosen], [keep.rsplit("/", 1)[-1], chosen.rsplit("/", 1)[-1]]]
    if chosen != "keep":
        for n in fx:
            ed.setdefault("effect", []).append({"match": {"Effect_NiagaraData.niagaraAsset": n.rsplit("/", 1)[-1]},
                                                "set": {"EventType": "None"}})
    s["sequence_edits"] = ed; s["effect_swaps"] = swaps
    s["trim"] = ([rec["tail"]] if rec.get("tail") else []) + [{"after": rec["lb1"], "delta": rec["start"] - rec["lb1"]}]
    return s

_cloned_seqs = {}
TICKS = 24000                     # sequence tick resolution (24000 / s); display rate 30 fps = 800 ticks per frame

def clone_sequence(asset_row, src_seq, dst_skill, dst_seq, mute, clones, post_objects, effect_swaps=(), edits=None, post_bytecode=None,
                   stretch=None, post_frames=None, effects=None, post_retime=None, sound_swaps=None, trim=None):
    """copy a battle sequence (Master + Track/* packages, extracted on demand) from sequence id src_seq to dst_seq under
    Sequencer/Battle/<kind>/<dst_skill>/<dst_seq>/; sound sections whose cue starts with a "mute" prefix lose their sound;
    effect_swaps = [[old name, new name], ...] rewrite the Niagara references (package path + object name);
    edits = {"master"|"cut"|"effect"|"sound": [{"match": {...}, "set": {...}}]} edit the director-blueprint event constants
    (see `ffr-dt seqdump` for the field names); stretch = {"motion": "LB1", "seconds": float} pushes every key after that motion's
    start (and the section / playback ranges) back by `seconds` so a longer unit motion is not cut off by the next motion key.
    Returns the DT_SkillAsset fields pointing at the copy."""
    if (src_seq, dst_seq) in _cloned_seqs: return _cloned_seqs[(src_seq, dst_seq)]
    master = asset_row["LevelSequence"]                       # /Game/Sequencer/Battle/Skill/414090/414091/SEQ_Battle_414091_Master
    folder = master.split("/Game/")[1].rsplit("/", 1)[0]      # Sequencer/Battle/Skill/414090/414091
    new_folder = "/".join(folder.split("/")[:-2] + [str(dst_skill), str(dst_seq)])
    legacy_dir = os.path.join(LEGACY, "FFRS", "Content", folder)
    if not os.path.exists(os.path.join(legacy_dir, master.rsplit("/", 1)[1] + ".uasset")):
        print(f"  extracting {folder} ...")
        subprocess.run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder), check=True, capture_output=True)
    ren = [[f"/Game/{folder}", f"/Game/{new_folder}"], [f"SEQ_Battle_{src_seq}", f"SEQ_Battle_{dst_seq}"]]
    def rn(p):
        for a, b in ren + [[folder, new_folder]]: p = p.replace(a, b)
        return p
    for dp, _, fs in os.walk(legacy_dir):
        for f in fs:
            if not f.endswith(".uasset"): continue
            rel_src = os.path.relpath(os.path.join(dp, f[:-7]), LEGACY).replace("\\", "/")
            rel_dst = rn(rel_src)
            clones.append({"from": rel_src, "to": rel_dst, "rename": ren + [list(x) for x in effect_swaps]})
            if mute and "_Sound" in f:
                for ex in atom_sections(os.path.join(dp, f), mute):
                    post_objects.append({"asset": rel_dst, "export": ex, "set": {"Sound": None}})
                    print(f"  muting {f[:-7]}:{ex}")
            if sound_swaps and "_Sound" in f:      # [[cue name, "/Game/Sound/.../NewCue"], ...] -> the section plays the other cue
                for ex, cue in atom_cues(os.path.join(dp, f)):
                    new_path = next((b for a, b in sound_swaps if a == cue), None)
                    if new_path:
                        post_objects.append({"asset": rel_dst, "export": ex, "set": {"Sound": new_path}})
                        print(f"  sound {f[:-7]}:{ex} {cue} -> {new_path.rsplit('/', 1)[-1]}")
            kind = "master" if f.endswith("_Master.uasset") else "cut" if "_Cut" in f else "effect" if "_Effect" in f else "sound" if "_Sound" in f else "?"
            if kind == "master":
                mops = movie_ops(os.path.join(dp, f))                 # the owner's CG movie never plays in an inherited Resonance
                for export, st in mops: post_objects.append({"asset": rel_dst, "export": export, "set": st})
                if mops:
                    post_objects.append({"asset": rel_dst, "export": os.path.basename(rel_dst), "set": {"Signature": "new"}})
                    print(f"  muting movie {f[:-7]}: {', '.join(x for x, _ in mops)}")
            for op in (edits or {}).get(kind, []):
                if op.get("skip_earliest"):
                    src_pkg = os.path.join(dp, f)
                    matched = [(t, fname) for t, et, fname in event_keys(src_pkg) if event_matches(dict(next((v for k, v in (seq_dumps(src_pkg)[1] or {}).items() if k.split(":", 1)[1] == fname), {})), op.get("match"))]
                    for t, fname in matched[int(op["skip_earliest"]):]:
                        post_bytecode.append({"asset": rel_dst, "export": rn(fname), "set": op.get("set", {})})
                    print(f"  editing {f[:-7]}: {op.get('match')} -> {list(op.get('set', {}))} on {max(0, len(matched) - int(op['skip_earliest']))} of {len(matched)} events (earliest {op['skip_earliest']} kept)")
                    continue
                post_bytecode.append({"asset": rel_dst, "export": "*", **{k: v for k, v in op.items() if k != "enable_track"}})
                print(f"  editing {f[:-7]}: {op.get('match')} -> {list(op.get('set', {}))}")
                ev = (op.get("match") or {}).get("EventType")
                if ev == "OtherChangeSubSpaceColor" or op.get("enable_track"):   # only the domain colour: other disabled tracks stay as the designers left them
                    for track in disabled_event_tracks(os.path.join(dp, f), ev):
                        post_objects.append({"asset": rel_dst, "export": track, "set": {"bIsEvalDisabled": False, "Signature": "new"}})
                        post_objects.append({"asset": rel_dst, "export": os.path.basename(rel_dst), "set": {"Signature": "new"}})
                        print(f"  enabling {f[:-7]}:{track} (the {ev} events were on a disabled track)")
    if effects and post_retime is not None:
        cut = next((os.path.join(dp, f) for dp, _, fs in os.walk(legacy_dir) for f in fs if "_Cut" in f and f.endswith(".uasset")), None)
        eff = next((os.path.join(dp, f) for dp, _, fs in os.walk(legacy_dir) for f in fs if "_Effect" in f and f.endswith(".uasset")), None)
        keys = motion_keys(cut) if cut else []
        lb_keys = [t for t, m in keys if m == "LB1"]; lb_start = max(lb_keys) if lb_keys else 0
        _, dump = seq_dumps(eff) if eff else (None, None)
        rel_eff = rn(os.path.relpath(eff[:-7], LEGACY).replace("\\", "/")) if eff else None
        taken = set()
        eff_keys = event_keys(eff) if eff else []          # (ticks, type, function) in time order
        for fx in effects:
            spawn = fx.get("spawn") or {"any": True}
            if spawn.get("any"):
                cands = [fname for _, _, fname in eff_keys]
            else:
                cands = [k.split(":", 1)[1] for k, v in (dump or {}).items() if event_matches(v, spawn["match"])]
            cands = [c for c in cands if c not in taken]
            idx = int(spawn.get("index", 0))
            fname = cands[idx] if idx < len(cands) else None
            if not fname or not rel_eff:
                print(f"  ! effect {fx['name']}: no free event in {os.path.basename(eff or '?')} matches {spawn.get('match', 'any')} (index {idx})"); continue
            taken.add(fname)
            pkg = f"/Game/Chara/effect/{fx['name']}/{fx['name']}"
            off = fx.get("offset") or [0, 0, 0]
            post_bytecode.append({"asset": rel_eff, "export": rn(fname),       # exactly this event, not every event that matches
                                  "set": {"EventType": "SsActorSpawnSpriteStudioActor",
                                          "SsActor_SsData": {"spriteStudioID": fx.get("id", fx["name"]), "ssPlayerAsset": {"path": pkg, "class": "Ss6Project"},
                                                             "AnimPackName": fx["name"], "AnimationName": fx.get("animation", "effect"), "PartName": fx.get("part", "Null_root"),
                                                             "addLocation": {"x": float(off[0]), "y": float(off[1]), "z": float(off[2])},
                                                             "bDisableFollowing": not fx.get("follow", True), "bSpawnRelativeTarget": bool(fx.get("at_target", False))}}})
            when = fx.get("time", "LB1")
            t = None
            if when != "event":                       # "event" keeps the repurposed event's own key time (the donor's cast / hit timing)
                t = lb_start + int(round(float(fx.get("delay", 0)) * TICKS / 800.0)) * 800 if when == "LB1" else int(round(float(when) * TICKS / 800.0)) * 800
                post_retime.append({"asset": rel_eff, "function": rn(fname), "time": t})   # the clone renamed SEQ_Battle_<src> in every export name
            print(f"  effect {fx['name']}: {rn(fname)} -> SsActorSpawnSpriteStudioActor at {'the event time' if t is None else f'{t / TICKS:.2f} s'}")
            if fx.get("at_target"):
                # the game's own way to put a sprite actor on the targets: a move-to-target event one frame after the spawn
                mv = next((c for c in cands if c not in taken), None)
                if not mv: print(f"  ! effect {fx['name']}: no spare event for the move-to-target step"); continue
                taken.add(mv)
                post_bytecode.append({"asset": rel_eff, "export": rn(mv),
                                      "set": {"EventType": "SsActorMoveToTargetToSsID", "SsActor_MoveToTarget_ID": fx.get("id", fx["name"]),
                                              "SsActor_MoveToTarget_targetPointID": -1, "SsActor_MoveToTarget_frame": 0, "SsActor_MoveToTarget_partName": fx.get("part", "Null_root"),
                                              "SsActor_MoveToTarget_plusOffset": {"x": float(off[0]), "y": float(off[1]), "z": float(off[2])},
                                              "SsActor_MoveToTarget_RelativeActionUnit": False, "SsActor_MoveToTarget_Height": float(fx.get("height", 0)), "SsActor_MoveToTarget_Length": float(fx.get("length", 0))}})
                tm = (t if t is not None else next((tk for tk, _, fn in eff_keys if fn == fname), 0)) + 800
                post_retime.append({"asset": rel_eff, "function": rn(mv), "time": tm})
                print(f"  effect {fx['name']}: {rn(mv)} -> SsActorMoveToTargetToSsID at {tm / TICKS:.2f} s")
    if stretch and stretch.get("seconds", 0) > 0 and post_frames is not None:
        cut = next((os.path.join(dp, f) for dp, _, fs in os.walk(legacy_dir) for f in fs if "_Cut" in f and f.endswith(".uasset")), None)
        keys = motion_keys(cut) if cut else []
        lb_keys = [t for t, m in keys if m == stretch.get("motion", "LB1")]
        start = max(lb_keys) if lb_keys else None        # the last trigger of the motion (templates re-trigger LB1 once)
        if start is None:
            print(f"  ! stretch: no {stretch.get('motion', 'LB1')} motion key in {os.path.basename(cut or '?')}")
        else:
            delta = int(round(stretch["seconds"] * TICKS / 800.0)) * 800
            for dp, _, fs in os.walk(legacy_dir):
                for f in fs:
                    if not f.endswith(".uasset"): continue
                    rel_dst = rn(os.path.relpath(os.path.join(dp, f[:-7]), LEGACY).replace("\\", "/"))
                    post_frames.append({"asset": rel_dst, "after": start + 1, "delta": delta})
                    post_objects.append({"asset": rel_dst, "export": os.path.basename(rel_dst), "set": {"Signature": "new"}})
            print(f"  stretching SEQ_Battle_{dst_seq}: keys after {start / TICKS:.2f} s ({stretch.get('motion', 'LB1')}) move by {delta / TICKS:.2f} s")
    for one in ([trim] if isinstance(trim, dict) else (trim or [])) if post_frames is not None else []:
        # the cinematic recipe: everything from the unit's motion onward moves to the front (a negative delta), so the
        # sequence's playback range ends there too and the silenced movie window is never reached. After the stretch, so the
        # stretch's tick reference is still the template's own timeline.
        after = int(round(one["after"] * TICKS / 800.0)) * 800
        delta = int(round(one["delta"] * TICKS / 800.0)) * 800
        for dp, _, fs in os.walk(legacy_dir):
            for f in fs:
                if not f.endswith(".uasset"): continue
                rel_dst = rn(os.path.relpath(os.path.join(dp, f[:-7]), LEGACY).replace("\\", "/"))
                post_frames.append({"asset": rel_dst, "after": after, "delta": delta, "cut": True})
                post_objects.append({"asset": rel_dst, "export": os.path.basename(rel_dst), "set": {"Signature": "new"}})
        print(f"  trimming SEQ_Battle_{dst_seq}: keys from {after / TICKS:.2f} s move {delta / TICKS:.2f} s (the owner's cinematic window)")

    res = {"LevelSequence": rn(master), "soundSequence": rn(asset_row["soundSequence"])}
    _cloned_seqs[(src_seq, dst_seq)] = res
    return res

def event_matches(ev, match):
    """seqdump event row vs {"EventType": ..., "Effect_NiagaraData.niagaraAsset": ...}; strings match on equality or suffix"""
    for k, want in (match or {}).items():
        cur = ev
        for part in k.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None: return False
        a, b = str(cur), str(want)
        if a != b and not a.endswith(b) and not a.endswith("/" + b) and not a.endswith(":" + b): return False
    return True

def ensure_effect_spec(fx):
    """fx needs only "source" (bmb file name): renders + converts it once into build/effects/<bmb stem>/ss6 and returns that folder"""
    spec_dir = fx.get("spec")
    src = fx.get("source") or fx.get("compose")
    if spec_dir and os.path.exists(os.path.join(ROOT, spec_dir, "spec.json")) and not src: return spec_dir
    if not src: sys.exit(f"effect {fx['name']}: no spec folder and no source bmb / compose list")
    fxdir = os.path.join(ROOT, "tools", "ffbe_effects"); sys.path.insert(0, fxdir); import layer_spec
    spec_dir = spec_dir or f"build/effects/{layer_spec.spec_stem(fx)}/ss6"
    try:
        doc, _d = layer_spec.load_doc_for(fx, log=lambda m: print(f"  {m}"))   # renders the bmb(s) once per option set, composes composites
    except Exception as ex:
        sys.exit(f"effect {fx['name']}: {ex}")
    kw = layer_spec.convert_kwargs(fx)
    run(ffrenv.py(os.path.join(fxdir, "to_ss6.py"), doc, os.path.join(ROOT, spec_dir), "--name", fx["name"], "--add-gain", str(kw["add_gain"]),
         "--scale-mult", str(kw["scale_mult"]), "--max-units", str(kw["max_units"]), "--min-frames", str(kw["min_frames"])))
    return spec_dir

def build_effect_project(name, spec_dir, donor_vid):
    """converted FFBE effect (spec.json + tex.bgra from tools/ffbe_effects/to_ss6.py) -> cooked Ss6Project + texture under Chara/effect/<name>/"""
    spec_p = os.path.join(ROOT, spec_dir, "spec.json")
    spec = json.load(open(spec_p, encoding="utf-8")); W, H = int(spec["pixelSize"][0]), int(spec["pixelSize"][1])
    chara = os.path.join(LEGACY, "FFRS", "Content", "Chara"); out = os.path.join(OUT, "FFRS", "Content", "Chara", "effect", name)
    d = donor_vid
    run(FFRDT + ["make-ss6", os.path.join(chara, "summon", f"summon{d}", f"summon{d}.uasset"), spec_p, os.path.join(out, f"{name}.uasset"),
         f"/Game/Chara/summon/summon{d}/summon{d}", f"/Game/Chara/effect/{name}/{name}", f"summon{d}={name}", "--usmap", USMAP])
    run(FFRDT + ["make-texture", os.path.join(chara, "summon", f"summon{TEX_DONOR}", f"summon{TEX_DONOR}_tex.uasset"), os.path.join(ROOT, spec_dir, "tex.bgra"), str(W), str(H),
         os.path.join(out, f"{name}_tex.uasset"), f"/Game/Chara/summon/summon{TEX_DONOR}/summon{TEX_DONOR}_tex", f"/Game/Chara/effect/{name}/{name}_tex", f"summon{TEX_DONOR}={name}", "--usmap", USMAP])

def seq_dumps(uasset):
    """(tojson, seqdump) of a sequence package, cached under build/"""
    out = os.path.join(BUILD, "seq_" + os.path.basename(uasset)[:-7] + ".json")
    if not os.path.exists(out):
        r = subprocess.run(FFRDT + ["tojson", uasset, out, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0: return None, None
    dump_p = os.path.join(BUILD, "seqdump_" + os.path.basename(uasset)[:-7] + ".json")
    if not os.path.exists(dump_p):
        r = subprocess.run(FFRDT + ["seqdump", uasset, dump_p, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0: return None, None
    return json.load(open(out, encoding="utf-8")), json.load(open(dump_p, encoding="utf-8"))

def event_keys(uasset):
    """[(ticks, EventType, function export name)] of every event key in a sequence package (enabled tracks only), in time order"""
    tj, dump = seq_dumps(uasset)
    if not tj: return []
    funcs = {int(k.split(":")[0]): (k.split(":", 1)[1], v) for k, v in dump.items()}
    ex = tj["Exports"]; imps = tj["Imports"]
    def cls(e): i = e.get("ClassIndex"); return imps[-i - 1]["ObjectName"] if isinstance(i, int) and i < 0 else "?"
    def prop(e, n): return next((p for p in e.get("Data", []) if isinstance(p, dict) and p.get("Name") == n), None)
    def num(o):
        for _ in range(8):
            if isinstance(o, (int, float)) and not isinstance(o, bool): return int(o)
            if isinstance(o, dict): o = o.get("Value")
            elif isinstance(o, list) and o: o = o[0]
            else: return None
    out = []
    for e in ex:
        if cls(e) != "MovieSceneEventTrack": continue
        dis = prop(e, "bIsEvalDisabled")
        if dis and dis.get("Value"): continue
        secs = prop(e, "Sections")
        for sref in (secs["Value"] if secs else []):
            si = sref["Value"] if isinstance(sref, dict) else sref
            ch = prop(ex[si - 1], "EventChannel")
            if not ch: continue
            kv = next((v for v in ch["Value"] if v.get("Name") == "KeyValues"), None); kt = next((v for v in ch["Value"] if v.get("Name") == "KeyTimes"), None)
            for i, key in enumerate(kv["Value"] if kv else []):
                ptrs = next((v for v in key["Value"] if v.get("Name") == "Ptrs"), None)
                fn = next((v for v in ptrs["Value"] if v.get("Name") == "Function"), None) if ptrs else None
                f = funcs.get(fn["Value"]) if fn else None
                if f: out.append((num(kt["Value"][i]) if kt else 0, f[1].get("EventType"), f[0]))
    return sorted(out)

def motion_keys(uasset):
    """[(ticks, motion name)] of the UnitPlayAnimByName keys in a Cut package, in time order"""
    tj, dump = seq_dumps(uasset)
    if not tj: return []
    funcs = {int(k.split(":")[0]): v for k, v in dump.items()}
    ex = tj["Exports"]; imps = tj["Imports"]
    def cls(e): i = e.get("ClassIndex"); return imps[-i - 1]["ObjectName"] if isinstance(i, int) and i < 0 else "?"
    def prop(e, n): return next((p for p in e.get("Data", []) if p.get("Name") == n), None)
    def num(o):
        for _ in range(8):
            if isinstance(o, (int, float)) and not isinstance(o, bool): return int(o)
            if isinstance(o, dict): o = o.get("Value")
            elif isinstance(o, list) and o: o = o[0]
            else: return None
    out = []
    for e in ex:
        if cls(e) != "MovieSceneEventTrack": continue
        dis = prop(e, "bIsEvalDisabled")
        if dis and dis.get("Value"): continue            # keys on a disabled track never play
        secs = prop(e, "Sections")
        for sref in (secs["Value"] if secs else []):
            si = sref["Value"] if isinstance(sref, dict) else sref
            ch = prop(ex[si - 1], "EventChannel")
            if not ch: continue
            kv = next((v for v in ch["Value"] if v.get("Name") == "KeyValues"), None); kt = next((v for v in ch["Value"] if v.get("Name") == "KeyTimes"), None)
            for i, key in enumerate(kv["Value"] if kv else []):
                ptrs = next((v for v in key["Value"] if v.get("Name") == "Ptrs"), None)
                fn = next((v for v in ptrs["Value"] if v.get("Name") == "Function"), None) if ptrs else None
                f = funcs.get(fn["Value"]) if fn else None
                if f and f.get("EventType") == "UnitPlayAnimByName":
                    out.append((num(kt["Value"][i]) if kt else 0, f.get("Unit_PlayAnimByName_AnimationName")))
    return sorted(out)

def lb_motion_seconds(u):
    """length of the unit's FFBE limit-burst motion (the FFR LB1 animation) in seconds, from its cgs delays (1/60 s each)"""
    ff = u.get("ffbe") or {}
    d = os.path.join(ROOT, ff.get("dir", "")); fid = ff.get("id")
    f = next((c for c in (os.path.join(d, f"unit_limitatk_cgs_{fid}.csv"), os.path.join(d, f"unit_limit_atk_cgs_{fid}.csv")) if os.path.exists(c)), None)
    if not f: return None
    total = 0
    with open(f, encoding="utf-8", errors="ignore") as motion:
        for line in motion:
            parts = line.strip().split(",")
            if len(parts) > 3 and parts[3].strip().lstrip("-").isdigit():
                total += max(1, int(parts[3]))  # same minimum frame delay as build_sprites.py
    return total / 60.0 if total else None


def prepare_ffbe_resonance(u, s, sid, tbl, clones, sequences):
    """A single authored LB timeline serves both target variants."""
    source = os.path.join(LEGACY, ffbe_resonance.SHELL + ".uasset")
    if not os.path.exists(source):
        run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", "Sequencer/Battle/Skill/440110/440111"))
    mechanics = {**row_by("Skill/DT_SkillData", "ID", s["from"])[1], **s.get("set", {})}
    seconds = lb_motion_seconds(u)
    if s.get("mechanics", "ffbe") == "ffbe":
        lb_source, resolved = ffbe_lb.resolve_import(u, s)
    else:
        lb_source = ffbe_lb.resolve(u, s)
        resolved = ffbe_lb.profile(lb_source)
    if s.get("mechanics", "ffbe") == "ffbe":
        if not resolved["supported"]:
            raise ValueError(f"{u['key']}: " + " ".join(resolved["issues"]))
        settings = dict(resolved["set"])
        if resolved.get("mode") == "support":
            import ffbe_lb_support
            settings = ffbe_lb_support.materialize(resolved, sid, s["jp"], tbl, row_by)
        for warning in resolved.get("warnings", []) + resolved.get("fallbackReasons", []):
            print(f"  ! {u['key']}: {warning}")
        if s.get("descAuto", True):
            settings["Description"] = text(resolved["description"])
        # Studio persists preview settings, including an empty support effect
        # list. Replace them before cloning: clearing a struct array first
        # discards the template ffr-dt needs to create its final elements.
        skill_row = next(r for r in tbl("Skill/DT_SkillData")["add"] if r["row"] == s["jp"])
        skill_row["set"].update(settings)
        mechanics.update(settings)
    elif lb_source and lb_source.get("hitFrames"):
        hit_set = {"hitCount": len(lb_source["hitFrames"]),
                   "hitDamageRatioList": [p / 100 for p in lb_source["hitPercents"]] +
                                         [0.0] * (30 - len(lb_source["hitFrames"]))}
        tbl("Skill/DT_SkillData")["set"].append({"row": s["jp"], "set": hit_set})
        mechanics.update(hit_set)
    else:
        print(f"  ! {u['key']}: no supported FFBE LB damage timeline; using the selected skill's hit count")
    bank, sounds = ffbe_audio.prepare(u, s, lb_source, tbl)
    if bank and not os.path.exists(os.path.join(LEGACY, ffbe_audio.SHELL + ".uasset")):
        run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", ffbe_audio.SHELL.replace("FFRS/Content/", "")))
    plan = ffbe_resonance.schedule(seconds, mechanics.get("hitCount", 1), sid,
                                   lb_source, sounds, {"enabled": False} if resolved.get("mode") == "fallback" else s.get("movement"))
    dest = f"FFRS/Content/Sequencer/Battle/Skill/{sid}/{sid + 1}/SEQ_Battle_{sid + 1}_Master"
    clones.append({"from": ffbe_resonance.SHELL, "to": dest,
                   "rename": [["SEQ_Battle_440111_Cut_000", f"SEQ_Battle_{sid + 1}_Master"]]})
    sequences.append({"asset": dest, "plan": plan, "source": lb_source, "profile": resolved, "audio": bank})
    for rel in ("Asset/Skill/DT_SkillAsset", "Asset/Skill/CDT_SkillAsset_Demo"):
        donor = row_by(rel, "ID", 440111)[0]
        for off in (1, 2):
            tbl(rel)["add"].append({"row": f"{s['jp']}_{off}", "cloneFrom": donor,
                                   "set": {"ID": sid + off, "LevelSequence": dest.replace("FFRS/Content/", "/Game/"),
                                           "soundSequence": "None", "bChangeNearClipPlane": False}})
    color_donor = row_by("PostProcess/DT_ColorGradingParameter", "ID", 62)[0]
    tbl("PostProcess/DT_ColorGradingParameter")["add"].append(
        ffbe_resonance.grading_row(sid, ffbe_resonance.resolved_field_color(s, lb_source), color_donor))
    reaction_donor = row_by("Battle/Sequencer/DT_BtlHitEffectData", "ID", 449999)[0]
    tbl("Battle/Sequencer/DT_BtlHitEffectData")["add"].append(
        {"row": s["jp"], "cloneFrom": reaction_donor, "set":
         {"ID": sid} if mechanics.get("DamageType") in ("Physic", "Magic") else ffbe_resonance.reaction_settings(sid)})
    print(f"  {u['key']}: own FFBE LB ({seconds:.2f} s), field {ffbe_resonance.resolved_field_color(s, lb_source)}")
    if lb_source:
        print(f"    FFBE LB {lb_source['lbId']}: {mechanics.get('hitCount', 1)} hits, move type {lb_source['moveType']}, {len(sounds)} sound cues")

def auto_stretch(u, s, asset_row, src_seq):
    """how far the template's keys after LB1 must move so the unit's own LB motion finishes before the next motion key"""
    st = s.get("stretch", "auto")
    if st is False or st is None: return None
    if isinstance(st, (int, float)): return {"motion": "LB1", "seconds": float(st)}
    lb = lb_motion_seconds(u)
    if not lb: return None
    master = asset_row["LevelSequence"]; folder = master.split("/Game/")[1].rsplit("/", 1)[0]
    legacy_dir = os.path.join(LEGACY, "FFRS", "Content", folder)
    if not os.path.exists(os.path.join(legacy_dir, master.rsplit("/", 1)[1] + ".uasset")):
        subprocess.run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder), check=True, capture_output=True)
    cut = next((os.path.join(dp, f) for dp, _, fs in os.walk(legacy_dir) for f in fs if "_Cut" in f and f.endswith(".uasset")), None)
    keys = motion_keys(cut) if cut else []
    lb_keys = sorted(t for t, m in keys if m == "LB1")
    start = lb_keys[0] if lb_keys else None              # the FIRST LB1 trigger; re-triggers of LB1 (+0.13 s, or Ascension's +4.3 s) do not end the window
    if start is None: return None
    nxt = next((t for t, m in sorted(keys) if t > start and m != "LB1"), None)
    if nxt is None: return None
    gap = (nxt - start) / TICKS
    need = lb - gap + 0.2                       # a little air after the motion ends
    if need <= 0.05: return None
    print(f"  {u['key']}: LB motion {lb:.2f} s, template gives {gap:.2f} s before the next motion -> stretch {need:.2f} s")
    return {"motion": "LB1", "seconds": need}

def movie_ops(uasset):
    """[(export name, set dict)] that silence the CriWare movie of an owner's Resonance Master package (Crystal Braver, Riot
    Blade - Lotus, Ascension play a full-screen CG movie from a MovieSceneManaTrack on a spawned BP_BtlSequencerMovieActor):
    the movie sections lose their source, the actor's spawn keys are all turned off, and the tracks / sections / sequence get
    fresh signatures so the compiled evaluation is rebuilt. Only existing properties are edited (the game serialises no
    defaults, so bIsEvalDisabled cannot be set). Empty for a package without a movie track."""
    tj, _ = seq_dumps(uasset)
    if not tj: return []
    imps = tj.get("Imports") or []
    def cname(e):
        c = e.get("ClassIndex")
        return imps[-c - 1].get("ObjectName") if isinstance(c, int) and c < 0 and -c - 1 < len(imps) else str(c)
    exps = tj.get("Exports") or []
    classes = {e.get("ObjectName"): cname(e) for e in exps}
    if "MovieSceneManaTrack" not in classes.values(): return []
    ops = []
    for e in exps:
        n, c = e.get("ObjectName"), classes.get(e.get("ObjectName"))
        if c == "MovieSceneManaSection": ops.append((n, {"ManaSource": None, "Signature": "new"}))
        elif c == "MovieSceneSpawnSection":
            st = {"Signature": "new"}
            curve = next((d for d in (e.get("Data") or []) if d.get("Name") == "BoolCurve"), None)
            vals = next((sub for sub in (curve or {}).get("Value", []) if sub.get("Name") == "Values"), None)
            for i in range(len((vals or {}).get("Value") or [])): st[f"BoolCurve.Values[{i}]"] = False
            ops.append((n, st))
        elif c in ("MovieSceneManaTrack", "MovieSceneSpawnTrack"): ops.append((n, {"Signature": "new"}))
    return ops

def disabled_event_tracks(uasset, event_type):
    """names of the MovieSceneEventTrack exports flagged bIsEvalDisabled whose keys trigger the given event type"""
    out = os.path.join(BUILD, "seq_" + os.path.basename(uasset)[:-7] + ".json")
    if not os.path.exists(out):
        r = subprocess.run(FFRDT + ["tojson", uasset, out, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0: return []
    dump_p = os.path.join(BUILD, "seqdump_" + os.path.basename(uasset)[:-7] + ".json")
    if not os.path.exists(dump_p):
        r = subprocess.run(FFRDT + ["seqdump", uasset, dump_p, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0: return []
    tj = json.load(open(out, encoding="utf-8")); dump = json.load(open(dump_p, encoding="utf-8"))
    types = {int(k.split(":")[0]): v.get("EventType") for k, v in dump.items()}
    ex = tj["Exports"]; imps = tj["Imports"]
    def cls(e): i = e.get("ClassIndex"); return imps[-i - 1]["ObjectName"] if isinstance(i, int) and i < 0 else "?"
    def prop(e, n): return next((p for p in e.get("Data", []) if p.get("Name") == n), None)
    found = []
    for e in ex:
        if cls(e) != "MovieSceneEventTrack": continue
        dis = prop(e, "bIsEvalDisabled")
        if not (dis and dis.get("Value")): continue
        secs = prop(e, "Sections")
        for sref in (secs["Value"] if secs else []):
            si = sref["Value"] if isinstance(sref, dict) else sref
            ch = prop(ex[si - 1], "EventChannel")
            if not ch: continue
            kv = next((v for v in ch["Value"] if v.get("Name") == "KeyValues"), None)
            for key in (kv["Value"] if kv else []):
                ptrs = next((v for v in key["Value"] if v.get("Name") == "Ptrs"), None)
                fn = next((v for v in ptrs["Value"] if v.get("Name") == "Function"), None) if ptrs else None
                if fn and types.get(fn["Value"]) == event_type and e["ObjectName"] not in found: found.append(e["ObjectName"])
    return found

def atom_sections(uasset, prefixes):
    """names of the MovieSceneAtomSection exports whose Sound cue starts with one of the prefixes"""
    out = os.path.join(BUILD, "seq_" + os.path.basename(uasset)[:-7] + ".json")
    r = subprocess.run(FFRDT + ["tojson", uasset, out, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0: sys.exit(f"tojson failed for {uasset}: {r.stderr[-300:]}")
    d = json.load(open(out, encoding="utf-8")); imps = d.get("Imports", [])
    def imp(i): return imps[-i - 1].get("ObjectName") if isinstance(i, int) and i < 0 else None
    names = []
    for e in d.get("Exports", []):
        if imp(e.get("ClassIndex")) != "MovieSceneAtomSection": continue
        snd = next((imp(pd.get("Value")) for pd in e.get("Data", []) if isinstance(pd, dict) and pd.get("Name") == "Sound"), None)
        if snd and any(str(snd).startswith(pf) for pf in prefixes): names.append(e["ObjectName"])
    return names

def atom_cues(uasset):
    """[(MovieSceneAtomSection export name, cue object name)] of a Sound package"""
    out = os.path.join(BUILD, "seq_" + os.path.basename(uasset)[:-7] + ".json")
    if not os.path.exists(out):
        r = subprocess.run(FFRDT + ["tojson", uasset, out, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0: sys.exit(f"tojson failed for {uasset}: {r.stderr[-300:]}")
    d = json.load(open(out, encoding="utf-8")); imps = d.get("Imports", [])
    def imp(i): return imps[-i - 1].get("ObjectName") if isinstance(i, int) and i < 0 else None
    res = []
    for e in d.get("Exports", []):
        if imp(e.get("ClassIndex")) != "MovieSceneAtomSection": continue
        snd = next((imp(pd.get("Value")) for pd in e.get("Data", []) if isinstance(pd, dict) and pd.get("Name") == "Sound"), None)
        if snd: res.append((e["ObjectName"], str(snd)))
    return res

def has_sequence(skill_id):
    """DT_SkillAsset row at id (shared sequence), id+1 (single target) or id+2 (group)"""
    ids = {v["ID"] for v in rows("Asset/Skill/DT_SkillAsset").values()}
    return any(skill_id + off in ids for off in (0, 1, 2))

def detail(grants):
    out = []
    for g in grants:
        p2 = g[2] if len(g) > 2 else -1
        out.append({"parameterType": f"eVisionMasteryParameterType::{g[0]}", "params": [g[1], p2]})
    while len(out) < 8:
        out.append({"parameterType": "eVisionMasteryParameterType::None", "params": [-1, -1]})
    return out

TEX_DONOR = 13110   # Cloud: single-mip BGRA8/BC5 textures, used as templates for every generated texture

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print((r.stdout or "").strip());
    if r.returncode != 0: print(r.stderr); sys.exit(f"failed: {' '.join(str(c) for c in cmd[:3])}")

def generate_sprites(u):
    """FFBE cgg/cgs -> atlas + SS6 spec -> cooked Ss6Project + textures under OUT/FFRS/Content/Chara/{summon,menu}/summon<vid>/"""
    vid, d = u["id"], u["donor"]; ff = u["ffbe"]
    work = os.path.join(ROOT, "build", "sprites", u["key"])
    base = [] if not ff.get("baseDir") or not os.path.isdir(os.path.join(ROOT, ff["baseDir"])) else ["--base", os.path.join(ROOT, ff["baseDir"]), str(ff.get("baseForm"))]
    run(ffrenv.py(os.path.join(ROOT, "tools", "ffbe2ss6", "build_sprites.py"), os.path.join(ROOT, ff["dir"]), ff["id"], str(vid), work) + base)
    chara = os.path.join(LEGACY, "FFRS", "Content", "Chara")
    out_b = os.path.join(OUT, "FFRS", "Content", "Chara", "summon", f"summon{vid}"); out_m = os.path.join(OUT, "FFRS", "Content", "Chara", "menu", f"summon{vid}")
    def ss6(kind, spec, out):
        run(FFRDT + ["make-ss6", os.path.join(chara, kind, f"summon{d}", f"summon{d}.uasset"), spec, os.path.join(out, f"summon{vid}.uasset"),
             f"/Game/Chara/{kind}/summon{d}/summon{d}", f"/Game/Chara/{kind}/summon{vid}/summon{vid}", f"summon{d}=summon{vid}", "--usmap", USMAP])
    def tex(kind, suffix, payload, w, h, out):
        run(FFRDT + ["make-texture", os.path.join(chara, kind, f"summon{TEX_DONOR}", f"summon{TEX_DONOR}{suffix}.uasset"), payload, str(w), str(h), os.path.join(out, f"summon{vid}{suffix}.uasset"),
             f"/Game/Chara/{kind}/summon{TEX_DONOR}/summon{TEX_DONOR}{suffix}", f"/Game/Chara/{kind}/summon{vid}/summon{vid}{suffix}", f"summon{TEX_DONOR}=summon{vid}", "--usmap", USMAP])
    for kind, out in (("battle", out_b), ("menu", out_m)):
        spec = json.load(open(os.path.join(work, kind, "spec.json"), encoding="utf-8")); W, H = int(spec["pixelSize"][0]), int(spec["pixelSize"][1])
        ss6("summon" if kind == "battle" else "menu", os.path.join(work, kind, "spec.json"), out)
        tex("summon" if kind == "battle" else "menu", "_tex", os.path.join(work, kind, "tex.bgra"), W, H, out)
        if kind == "battle":
            tex("summon", "_normal", os.path.join(work, kind, "normal.bc5"), W, H, out)
            tex("summon", "_mreo", os.path.join(work, kind, "mreo.bgra"), W, H, out)
    # icons: FFBE unit_icon painted into the game's icon frames (Cloud's icons as texture donors)
    icon_out = os.path.join(work, "icons")
    ic = u.get("icon") or {}
    layout = os.path.join(ROOT, "mods", "EstherTsukiko", "icon_layout.json")
    run(ffrenv.py(os.path.join(ROOT, "tools", "ffbe2ss6", "build_icons.py"), os.path.join(ROOT, ff["dir"]), ff["id"], icon_out,
                  "--style", ic.get("style", "gem"), "--rarity", str(ic.get("rarity", "7"))) + (["--layout", layout] if os.path.exists(layout) else []))
    icon_root = os.path.join(LEGACY, "FFRS", "Content", "UI", "Textures", "Icon")
    for sub, name, payload, size in (("Vision_Face", "ICON_UnitFace", "face.bgra", 128), ("Unit_Face_Timeline", "ICON_UnitFace", "timeline.bgra", 128), ("menu", "ICON_Ability", "ability.bgra", 64)):
        dst = os.path.join(OUT, "FFRS", "Content", "UI", "Textures", "Icon", sub)
        run(FFRDT + ["make-texture", os.path.join(icon_root, sub, f"{name}_summon{TEX_DONOR}.uasset"), os.path.join(icon_out, payload), str(size), str(size), os.path.join(dst, f"{name}_summon{vid}.uasset"),
             f"/Game/UI/Textures/Icon/{sub}/{name}_summon{TEX_DONOR}", f"/Game/UI/Textures/Icon/{sub}/{name}_summon{vid}", f"summon{TEX_DONOR}=summon{vid}", "--usmap", USMAP])

def stage(text):
    """progress marker for the dev UI (##stage lines are turned into friendly status text)"""
    print(f"##stage {text}", flush=True)

def main():
    install = "--no-install" not in sys.argv
    os.makedirs(BUILD, exist_ok=True)
    stage("Preparing the game tables")
    tables = {}
    def tbl(rel):
        return tables.setdefault(rel, {"asset": DT + rel, "add": [], "set": []})
    clones = []
    post_objects = []   # edits applied to cloned packages after the first patch pass
    post_bytecode = []  # director-blueprint event edits (colours, effects) on cloned sequences, same pass
    post_frames = []    # key-time / range shifts (stretched Resonances), same pass, applied before the object edits
    post_retime = []    # single event keys moved to a tick (FFBE effect spawns at LB1), applied after the stretch
    authored_sequences = []  # dedicated FFBE Resonances, including their cooked event schedules
    effect_jobs = []; built_effects = set()   # FFBE effects converted to Ss6Projects (built with the sprites)
    shop_slots = []
    for u in UNITS:
        d = u["donor"]; vid = u["id"]
        donor_unit = row_by("Unit/DT_UnitParameter", "ID", d)
        donor_vis = row_by("Item/Vision/DT_VisionItemData", "ID", d)
        donor_cmd = row_by("Skill/DT_CommandSkillData", "unitIdToUseSkill", d)
        donor_master = row_by("Skill/DT_MasterSkillData", "VisionId", d)
        donor_asset = row_by("Asset/Battle/Unit/DT_BtlUnitAsset", "ID", d)
        donor_design = row_by("Battle/Unit/DT_BtlUnitDesignParameter", "ID", d)
        donor_upg = row_by("UI/Vision/DT_VisionUpgrade_VisionUpgradeData", "VisionId", d)
        # 1. unit parameter (+ own level table: units sharing a donor's LevelParamId got mixed up in battle, so clone the donor table under a new id)
        lvl_id = 10100 + UNITS.index(u)
        donor_lvl = row_by("Unit/LevelParameter/DT_UnitLevelParameterList", "ID", donor_unit[1]["LevelParamId"])
        donor_tbl = donor_lvl[1]["DataTable"]; new_tbl = f"DT_UnitLevelParameter{u['key'].capitalize()}"
        sub = next(s for s in ("Vision", "Playable", "summon") if os.path.exists(os.path.join(LEGACY, "FFRS", "Content", "Datatable", "Unit", "LevelParameter", s, donor_tbl + ".uasset")))
        clones.append({"from": f"FFRS/Content/Datatable/Unit/LevelParameter/{sub}/{donor_tbl}", "to": f"FFRS/Content/Datatable/Unit/LevelParameter/Vision/{new_tbl}", "rename": [[donor_tbl, new_tbl]]})
        tbl("Unit/LevelParameter/DT_UnitLevelParameterList")["add"].append({"row": f"ビジョン_{u['jp']}", "cloneFrom": donor_lvl[0], "set": {
            "ID": lvl_id, "DataTable": f"/Game/Datatable/Unit/LevelParameter/Vision/{new_tbl}"}})
        st = dict(u["stats"]); st["HitPoint"] = 0; st["MagicPoint"] = st["MaxMagicPoint"]
        tbl("Unit/DT_UnitParameter")["add"].append({"row": u["jp"], "cloneFrom": donor_unit[0], "set": {
            "ID": vid, "SortId": vid, "SaveId": vid, "FaceIconId": vid, "LevelParamId": lvl_id, "Name": text(u["en"]), "Description": text(u["desc"]),
            "ElementResistanceList": u["elemRes"], **st}})
        # 2. vision item
        tbl("Item/Vision/DT_VisionItemData")["add"].append({"row": u["jp"], "cloneFrom": donor_vis[0], "set": {
            "ID": vid, "SortId": u["sort"], "finishBlowSkill": lb_id(vid) if u.get("lb_custom") else u["lb"], "CommandId": u["command"]["id"],
            "attackType": f"eSkillDamageType::{u['attackType']}", "roles": u["roles"],
            "Name": text(u["en"]), "nameSg": text(u["en"]), "namePl": text(u["en"]), "nameDetSg": text(u["en"]), "nameDetPl": text(u["en"]),
            "Description": text(u["desc"]), "buyingPrice": u["price"], "sellingPrice": 0, "isAvailableSale": False}})
        # 3. command set (+ its icon: a gameplay tag borrowed from the registry's unused vision ids, mapped to our ICON_Ability texture)
        icon_tag = f"UI.Skill.Command.Icon.{UNUSED_ICON_TAGS[UNITS.index(u)]}"
        tbl("Skill/DT_CommandSkillData")["add"].append({"row": f"{u['jp']}の技", "cloneFrom": donor_cmd[0], "set": {
            "ID": u["command"]["id"], "SortId": u["command"]["id"], "unitIdToUseSkill": vid, "SkillIcon.TagName": icon_tag,
            "Name": text(u["command"]["en"]), "Description": text(u["command"]["desc"])}})
        icon_pkg = f"/Game/UI/Textures/Icon/menu/ICON_Ability_summon{vid}"
        # the icon tables already hold placeholder rows for those tags (unreleased visions: Kain, Faris, Locke, Celes, Tifa...)
        # with no texture, and the lookup hits them first -> overwrite those rows instead of adding new ones
        for rel in ("UI/Skill/DT_CommandSkillIcon", "UI/Skill/CDT_SkillIcon"):
            placeholder = row_by(rel, "Tag", {"TagName": icon_tag})
            tbl(rel)["set"].append({"row": placeholder[0], "set": {
                "Brush.ResourceObject": icon_pkg, "Brush.ImageSize": {"X": 64.0, "Y": 64.0},
                "Brush.bIsDynamicallyLoaded": True, "Brush.ResourceName": f"{icon_pkg}.ICON_Ability_summon{vid}"}})
        # skill seal points (one row per vision in the original data; cloned from the donor)
        donor_seal = row_by("Skill/Other/DT_SkillSealPointData", "VisionId", d)
        tbl("Skill/Other/DT_SkillSealPointData")["add"].append({"row": u["jp"], "cloneFrom": donor_seal[0], "set": {"VisionId": vid}})
        # 4. master skill
        tbl("Skill/DT_MasterSkillData")["add"].append({"row": u["jp"], "cloneFrom": donor_master[0], "set": {
            "ID": u["master"]["id"], "SortId": u["master"]["id"], "VisionId": vid, "SkillIcon.TagName": icon_tag,
            "Name": text(u["master"]["en"]), "Description": text(u["master"]["desc"])}})
        # 5. cloned skills (+ their sequencer assets if any)
        skill_rows = rows("Skill/DT_SkillData")
        by_id = {v["ID"]: k for k, v in skill_rows.items()}
        custom = list(u["skills"].items())
        if u.get("lb_custom"):
            custom.append((lb_id(vid), dict(u["lb_custom"], resonance=True)))
        base = unique_skill_base(vid)
        for sid, s in custom:
            if not s.get("resonance"):
                assert base <= sid < base + 100, f"{u['key']}: skill id {sid} must be in the derived range {base}..{base + 90} (see unique_skill_base)"
            if s.get("tint") is not None:   # screen tint preset (DT_ColorGradingParameter id) for the copied sequence
                s = dict(s); s["clone_sequence"] = True
                ed = {k: list(v) for k, v in (s.get("sequence_edits") or {}).items()}
                for track in ("master", "effect"):
                    ed.setdefault(track, []).append({"match": {"EventType": "PostSetColorGradingGlobalParameter"}, "set": {"Post_SetColorGradingGlobalParameter_Id": int(s["tint"])}})
                s["sequence_edits"] = ed
            if s.get("motion"):
                s = dict(s); s["clone_sequence"] = True
                ed = {k: list(v) for k, v in (s.get("sequence_edits") or {}).items()}
                ed.setdefault("cut", [])
                for m in MOTION_NAMES:
                    if m != s["motion"]:
                        ed["cut"].append({"match": {"EventType": "UnitPlayAnimByName", "Unit_PlayAnimByName_AnimationName": m},
                                          "set": {"Unit_PlayAnimByName_AnimationName": s["motion"]}})
                s["sequence_edits"] = ed
            src = by_id[s["from"]]
            tbl("Skill/DT_SkillData")["add"].append({"row": s["jp"], "cloneFrom": src, "set": {
                "ID": sid, "SortId": sid, "Name": text(s["en"]), "Description": text(s["desc"]), **s.get("set", {})}})
            if ffbe_resonance.uses_ffbe(u, s):
                prepare_ffbe_resonance(u, s, sid, tbl, clones, authored_sequences)
                continue
            if s.get("resonance"):   # the Resonance caption dialogue lives in a per-id table loaded by path
                cap = s.get("caption_from", s["from"])
                ev = f"Datatable/Event/Text/BattleSequencerEvent/DT_BtlEv_{cap}"
                if os.path.exists(os.path.join(LEGACY, "FFRS", "Content", ev + ".uasset")):
                    clones.append({"from": "FFRS/Content/" + ev, "to": f"FFRS/Content/Datatable/Event/Text/BattleSequencerEvent/DT_BtlEv_{sid}",
                                   "rename": [[str(cap), str(sid)]]})
            # battle visuals: DT_SkillAsset maps a *sequence id* to a LevelSequence. The sequence id is the skill id + 1
            # (single-target variant) or + 2 (group variant); a few shared sequences (magic-sword lines) sit at the skill id
            # itself. A skill without any of these rows plays nothing (the demo ships sequences for only part of the skill
            # table). DT_BtlHitEffectData (hit / critical / weakness effects) is keyed by the skill id. Copy the "visuals"
            # donor's rows shifted to the new id.
            vis = s.get("visuals", s["from"])
            if s.get("resonance"): s = apply_cinematic(s, vis)
            found = []
            for off in (0, 1, 2):
                for rel in ("Asset/Skill/DT_SkillAsset", "Asset/Skill/CDT_SkillAsset_Demo"):
                    k = next((k for k, v in rows(rel).items() if v["ID"] == vis + off), None)
                    if not k: continue
                    row_set = {"ID": sid + off}
                    if s.get("clone_sequence"):   # own copy of the sequence packages (editable: muted voice, later hue / motion)
                        stretch = auto_stretch(u, s, rows(rel)[k], vis + off) if s.get("resonance") else None
                        row_set.update(clone_sequence(rows(rel)[k], vis + off, sid, sid + off, s.get("mute", []), clones, post_objects,
                                                      s.get("effect_swaps", []), s.get("sequence_edits", {}), post_bytecode, stretch, post_frames,
                                                      s.get("ffbe_effects"), post_retime, s.get("sound_swaps"), s.get("trim")))
                        for fx in s.get("ffbe_effects") or []:
                            if fx["name"] not in built_effects:
                                effect_jobs.append((fx["name"], ensure_effect_spec(fx), u["donor"])); built_effects.add(fx["name"])
                    tbl(rel)["add"].append({"row": f"{s['jp']}_{off}", "cloneFrom": k, "set": row_set}); found.append(off)
            if not found:
                print(f"  ! {u['key']}: custom skill {sid} borrows visuals from {vis}, which has no battle sequence in this build")
            hit = next((k for k, v in rows("Battle/Sequencer/DT_BtlHitEffectData").items() if v["ID"] == vis), None)
            if hit:
                tbl("Battle/Sequencer/DT_BtlHitEffectData")["add"].append({"row": s["jp"], "cloneFrom": hit, "set": {"ID": sid}})
        missing = [g[1] for tier in u["awakening"] for g in tier if g[0] == "ActiveSkill" and g[1] in by_id and not has_sequence(g[1])
                   and skill_rows[by_id[g[1]]]["skillAttrType"] != "FinishBlow"]
        if missing:
            print(f"  ! {u['key']}: granted skills without a battle sequence in this build (no animation): {missing}")
        # 6. awakening + synchro mastery
        aw = sorted([(k, v) for k, v in rows("Item/Vision/DT_VisionAwakeningMasteryData").items() if v["ID"] == d], key=lambda x: x[1]["Level"])
        for i, grants in enumerate(u["awakening"]):
            tbl("Item/Vision/DT_VisionAwakeningMasteryData")["add"].append({"row": f"{u['jp']}覚醒度{i+1}の恩恵", "cloneFrom": aw[min(i, len(aw)-1)][0], "set": {
                "ID": vid, "Level": i, "masteryPoint": i, "detailData": detail(grants)}})
        sy = sorted([(k, v) for k, v in rows("Item/Vision/DT_VisionSynchroMasteryData").items() if v["ID"] == d], key=lambda x: x[1]["Level"])
        for i, grants in enumerate(u["synchro"]):
            src_k, src_v = sy[min(i, len(sy)-1)]
            dd = detail(grants)[:len(src_v["detailData"])] if grants else [{"parameterType": "eVisionMasteryParameterType::None", "params": [-1, -1]}] * len(src_v["detailData"])
            tbl("Item/Vision/DT_VisionSynchroMasteryData")["add"].append({"row": f"{u['jp']}SLv{i}", "cloneFrom": src_k, "set": {
                "ID": vid, "Level": i, "masteryPoint": src_v["masteryPoint"], "detailData": dd}})
        # 7. battle assets / design / upgrade UI (donor sprites)
        asset_set = {"ID": vid}
        if u.get("ffbe"):   # own converted sprites (generated below into Chara/summon/summon<vid>)
            base = f"/Game/Chara/summon/summon{vid}/summon{vid}"
            asset_set.update({"animationAssetList[0].Ss6Project": base, "animationAssetList[0].textureBaseColor": base + "_tex",
                              "animationAssetList[0].textureNormal": base + "_normal", "animationAssetList[0].textureMetallicRoughness": base + "_mreo"})
        tbl("Asset/Battle/Unit/DT_BtlUnitAsset")["add"].append({"row": u["jp"], "cloneFrom": donor_asset[0], "set": asset_set})
        tbl("Battle/Unit/DT_BtlUnitDesignParameter")["add"].append({"row": u["jp"], "cloneFrom": donor_design[0], "set": {"ID": vid}})
        tbl("UI/Vision/DT_VisionUpgrade_VisionUpgradeData")["add"].append({"row": u["jp"], "cloneFrom": donor_upg[0], "set": {"VisionId": vid}})
        # 8. menu sprite package + icons, renamed copies of the donor's
        ren = [[f"summon{d}", f"summon{vid}"]]
        if not u.get("ffbe"):   # menu sprite: donor copy unless we generate our own
            clones += [
                {"from": f"FFRS/Content/Chara/menu/summon{d}/summon{d}", "to": f"FFRS/Content/Chara/menu/summon{vid}/summon{vid}", "rename": ren},
                {"from": f"FFRS/Content/Chara/menu/summon{d}/summon{d}_tex", "to": f"FFRS/Content/Chara/menu/summon{vid}/summon{vid}_tex", "rename": ren},
            ]
        if not u.get("ffbe"):   # icons: donor copies unless generated from the FFBE face icon
            clones += [
                {"from": f"FFRS/Content/UI/Textures/Icon/Vision_Face/ICON_UnitFace_summon{d}", "to": f"FFRS/Content/UI/Textures/Icon/Vision_Face/ICON_UnitFace_summon{vid}", "rename": ren},
                {"from": f"FFRS/Content/UI/Textures/Icon/Unit_Face_Timeline/ICON_UnitFace_summon{d}", "to": f"FFRS/Content/UI/Textures/Icon/Unit_Face_Timeline/ICON_UnitFace_summon{vid}", "rename": ren},
                {"from": f"FFRS/Content/UI/Textures/Icon/menu/ICON_Ability_summon{d}", "to": f"FFRS/Content/UI/Textures/Icon/menu/ICON_Ability_summon{vid}", "rename": ren},
            ]
        shop_slots.append(vid)
    # 9. shop: put the visions into the first empty slots of the Mitra item shop
    shop = rows("Shop/DT_ShopList")[SHOP_ROW]
    items = [dict(it) for it in shop["ItemList"]]
    empty = [i for i, it in enumerate(items) if it["ItemId"] == -1]
    template = dict(items[0])
    for vid in shop_slots:
        entry = dict(template, ItemId=vid, MaxOrderNum=1, PriceRatio=1.0)
        if empty: items[empty.pop(0)] = entry
        else: items.append(entry)
    tbl("Shop/DT_ShopList")["set"].append({"row": SHOP_ROW, "set": {"ItemList": items}})

    # 10. ID -> asset maps baked into "regular id" data assets (the UI resolves menu sprites / face icons through these, not by path)
    objects = []
    idmaps = [
        ("FFRS/Content/Datatable/UI/Unit/Asset/DA_MenuUnitSsProject", "/Game/Chara/menu/summon{id}/summon{id}.summon{id}"),
        ("FFRS/Content/Datatable/UI/Unit/Asset/DA_UnitIcon_Timeline", "/Game/UI/Textures/Icon/Vision_Face/ICON_UnitFace_summon{id}.ICON_UnitFace_summon{id}"),
        ("FFRS/Content/Datatable/UI/Unit/Asset/DA_UnitIconTexture", "/Game/UI/Textures/Icon/Unit_Face_Timeline/ICON_UnitFace_summon{id}.ICON_UnitFace_summon{id}"),
    ]
    for rel, fmt in idmaps:
        objects.append({"asset": rel, "mapAdd": {"assetMap": {str(u["id"]): fmt.format(id=u["id"]) for u in UNITS}}})
    # sprite scale/offset overrides for the menu sprite: copy the donor's entry
    layout = json.load(open(os.path.join(ROOT, "build", "visions_mod", "check", "da", "DA_UIUnitSsLayout.json"), encoding="utf-8"))["Properties"]["LayoutOverrideDataMap"]
    layout = {str(e["Key"]): e["Value"] for e in layout}
    over = {}
    for u in UNITS:
        if u.get("ffbe"):   # converted FFBE sprites share one scale (Tsukiko at 2.52 looked right in the equipment screen)
            over[str(u["id"])] = {"bOverrideOffset": False, "bOverrideScale": True, "Scale": u.get("menuScale", 2.52), "bOverrideFlippedHorizontally": False, "bFlippedHorizontally": False}
            continue
        dv = layout.get(str(u["donor"]))
        if dv: over[str(u["id"])] = {k: v for k, v in dv.items() if k in ("bOverrideOffset", "bOverrideScale", "Scale", "bOverrideFlippedHorizontally", "bFlippedHorizontally")}
    if over:
        objects.append({"asset": "FFRS/Content/UI/Unit/UIUnitSs/Data/DA_UIUnitSsLayout", "mapAdd": {"LayoutOverrideDataMap": over}})

    patch = {"legacyRoot": LEGACY.replace("\\", "/"), "outRoot": OUT.replace("\\", "/"), "tables": list(tables.values()), "objects": objects, "clones": clones}
    pp = os.path.join(BUILD, "patch.json")
    json.dump(patch, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("patch:", pp, f"({len(patch['tables'])} tables, {sum(len(t['add']) for t in tables.values())} added rows, {len(clones)} package clones)")
    if os.path.isdir(OUT):
        import shutil; shutil.rmtree(OUT)
    stage("Writing game tables and copying battle sequences")
    r = subprocess.run(FFRDT + ["patch", pp, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout); print(r.stderr)
    if r.returncode != 0: sys.exit("ffr-dt patch failed")
    for job in authored_sequences:
        stage("Writing the FFBE limit-burst timeline")
        ffbe_resonance.build(job, OUT, BUILD, FFRDT, USMAP, run)
    for bank in {b["name"]: b for j in authored_sequences for b in ffbe_audio.banks(j.get("audio"))}.values():
        ffbe_audio.build(bank, OUT, BUILD, FFRDT, USMAP, run, LEGACY)
    if post_objects or post_bytecode or post_frames or post_retime:   # second pass: edit the packages cloned above in place
        stage("Applying Resonance and animation edits")
        pp2 = os.path.join(BUILD, "patch2.json")
        out_fwd = OUT.replace("\\", "/")
        json.dump({"legacyRoot": out_fwd, "outRoot": out_fwd, "tables": [], "frames": post_frames, "retime": post_retime, "objects": post_objects, "bytecode": post_bytecode, "clones": []},
                  open(pp2, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        r = subprocess.run(FFRDT + ["patch", pp2, "--usmap", USMAP], capture_output=True, text=True, encoding="utf-8")
        print(r.stdout); print(r.stderr)
        if r.returncode != 0: sys.exit("ffr-dt patch (pass 2) failed")
    todo = [u for u in UNITS if u.get("ffbe")]
    for i, u in enumerate(todo):
        stage(f"Converting sprites and icons: {u['en']} ({i + 1} of {len(todo)})")
        generate_sprites(u)
    for name, spec_dir, donor in effect_jobs:
        stage(f"Building FFBE effect: {name}")
        build_effect_project(name, spec_dir, donor)
    stage("Packing the mod" + (" and installing it" if install else ""))
    cmd = ffrenv.py(os.path.join(ROOT, "tools", "build_mod.py"), OUT, ffrenv.MOD_NAME) + (["--install"] if install else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8"); print(r.stdout); print(r.stderr)
    if r.returncode != 0: sys.exit("build_mod failed")

if __name__ == "__main__":
    main()
