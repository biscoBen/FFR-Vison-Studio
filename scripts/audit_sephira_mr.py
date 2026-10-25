"""Track the excluded originals' equipable MR abilities, independently of kits.

Run after editing the catalog: python scripts/audit_sephira_mr.py
No game files or game installation are required; use the audited native grants.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def audit(catalog, source):
    index={track:{} for track in ('synchro','awakening')}
    for preset in catalog['presets']:
        unit=preset['profile']
        for track in index:
            for rank,tier in enumerate(unit[track]):
                for kind,identity,*_ in tier:
                    if kind not in ('ActiveSkill','PassiveSkill'):continue
                    recipe=unit.get('skills',{}).get(str(identity)) if kind=='ActiveSkill' else None
                    native=recipe['from'] if recipe else identity
                    index[track].setdefault((kind,native),[]).append({
                        'preset':preset['id'],'vision':preset['name'],
                        'rank':rank if track=='synchro' else rank+1,
                        'grantId':identity,'privateCopy':recipe is not None})
    rewards=[]
    for entry in source['entries']:
        origins=[g for g in entry['nativeGrants'] if g['track']=='synchro']
        if not origins:continue
        key=entry['kind'],entry['id'];mr=index['synchro'].get(key,[]);awakening=index['awakening'].get(key,[])
        status=('covered_mr' if any(not g['privateCopy'] for g in mr) else 'mr_copy_needs_review' if mr else
                'awakening_only' if awakening else 'missing_from_learned_kits')
        rewards.append({'kind':entry['kind'],'id':entry['id'],'name':entry['name'],
            'originalMr':[{'vision':g['vision'],'rank':g['rank']} for g in origins],
            'mr':mr,'awakening':awakening,'status':status})
    order={v['name']:n for n,v in enumerate(source['excludedVisions'])}
    rewards.sort(key=lambda r:(order[r['originalMr'][0]['vision']],r['originalMr'][0]['rank'],r['id']))
    summary={'originalVisions':len(source['excludedVisions']),'originalRewards':len(rewards)}
    for status in ('covered_mr','mr_copy_needs_review','awakening_only','missing_from_learned_kits'):
        summary[status]=sum(r['status']==status for r in rewards)
    return {'schema':1,'catalogSha256':fingerprint(catalog),'nativeAuditSha256':fingerprint(source),
        'source':'assets/sephira_visions/native_coverage.json','summary':summary,'rewards':rewards,
        'spiritWrappers':[{'vision':v['name'],'ids':v['masterRewards']} for v in source['excludedVisions']]}


def describe(report):
    s=report['summary'];missing=[r for r in report['rewards'] if r['status']!='covered_mr']
    active_gaps=sum(r['kind']=='ActiveSkill' for r in missing)
    passive_covered=sum(r['kind']=='PassiveSkill' and r['status']=='covered_mr' for r in report['rewards'])
    lines=['# Sephira MR equipable coverage','',
        f"The {s['originalVisions']} excluded originals grant {s['originalRewards']} distinct individual MR abilities. "
        f"**{s['covered_mr']} are currently covered as Sephira MR rewards; {s['awakening_only']} exist only in awakening.** "
        f"Private MR copies needing a mechanics review: {s['mr_copy_needs_review']}. Abilities absent from learned kits entirely: {s['missing_from_learned_kits']}.", '',
        'Coverage here requires an MR grant. An awakening grant or an unused skill definition does not count. Private active copies are listed for review rather than assumed to have identical mechanics. This compares the bundled presets, not additional edits in a personal Studio roster.', '',
        f'There are {active_gaps} active-skill gaps; {passive_covered} original passive MR rewards are offered through MR. The earlier 131-passive check covered original awakening bonuses as well as MR rewards; it did not establish full MR coverage.', '',
        'Each new Spirit follows its own vision\'s MR list. It does not grant an awakening-only ability. Original Spirit wrappers and permanent stat grants are separate from the individual equipable abilities audited below; new Spirits have their own reward bundles.', '',
        '## Missing as MR rewards','',
        '| Original vision | MR | Reward | Current awakening location |','|---|---:|---|---|']
    for r in missing:
        origin=r['originalMr'][0]
        where='; '.join(f"{g['vision']} tier {g['rank']}" for g in r['awakening']) or 'None'
        lines.append(f"| {origin['vision']} | {origin['rank']} | {r['name']} ({r['id']}) | {where} |")
    lines+=['','## Full comparison','',
        '| Original vision | MR | Reward | Sephira MR locations | Status |','|---|---:|---|---|---|']
    for r in report['rewards']:
        origin=r['originalMr'][0]
        where='; '.join(f"{g['vision']} MR{g['rank']}" for g in r['mr']) or '—'
        lines.append(f"| {origin['vision']} | {origin['rank']} | {r['name']} ({r['id']}) | {where} | {r['status'].replace('_',' ')} |")
    lines+=['','## Updating the comparison','',
        'Run `python scripts/audit_sephira_mr.py` after changing the catalog. The accompanying JSON records source IDs, original MR ranks, current MR/awakening placements and input fingerprints. A repository check rejects stale reports. This report does not change a kit or reward.', '',
        f"Catalog fingerprint: `{report['catalogSha256']}`.",
        f"Native coverage fingerprint: `{report['nativeAuditSha256']}`.",'']
    return '\n'.join(lines)


def main():
    catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
    source=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
    report=audit(catalog,source)
    (ROOT/'docs/SEPHIRA_MR_COVERAGE.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (ROOT/'docs/SEPHIRA_MR_COVERAGE.md').write_text(describe(report),encoding='utf-8')
    print(json.dumps(report['summary']))


if __name__=='__main__':main()
