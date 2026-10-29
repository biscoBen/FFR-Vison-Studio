"""Concise player-facing skill text; provenance stays in the catalog audit."""
import re

ELEMENTS = {'None':'non-elemental', 'Thunder':'Lightning', 'Ice':'Ice', 'Fire':'Fire',
            'Water':'Water', 'Earth':'Earth', 'Wind':'Wind', 'Light':'Light', 'Dark':'Dark'}
METADATA = re.compile(r' (?:Self|Single|Group|All|SingleAndGroup|Random) (?:friendlies|enemies); MP \d+; hits \d+; accuracy \d+; stagger \d+\.$')
DAMAGE = re.compile(r'^(?:Non-elemental|Fire|Ice|Thunder|Water|Wind|Earth|Light|Dark) (?:physical|magic) damage; power [\d.]+\.')


def short_skill(recipe, source):
    text = recipe.get('desc', '')
    if not METADATA.search(text): return text
    row = {**source, **recipe.get('set', {})}
    text = METADATA.sub('', text)
    target = row['TargetType']
    whom = 'all enemies' if target in ('Group','All') else 'random enemies' if target=='Random' else 'an enemy'
    if DAMAGE.match(text):
        element = '' if row['element']=='None' else ELEMENTS[row['element']] + ' '
        nature = 'physical' if row['DamageType']=='Physic' else 'magic'
        count = row.get('hitCount',1)
        attack = f'Deal {element}{nature} damage to {whom}'
        if count > 1: attack += f' {count} times'
        text = DAMAGE.sub(attack + '.', text)
    elif text.startswith('Restore '):
        match = re.match(r'Restore ([\d.]+)% max (HP|MP)\.',text)
        if match:
            amount, resource = match.groups()
            owner = 'own' if target=='Self' else 'all allies’' if target in ('Group','All') else 'an ally’s'
            replacement = f'Restore {amount}% of {owner} max {resource}.'
            text = replacement + text[match.end():]
        else:
            who = 'own' if target=='Self' else 'all allies’' if target in ('Group','All') else 'an ally’s'
            text = re.sub(r'^Restore healing power [\d.]+\.', f'Restore {who} HP.',text)
            text = re.sub(r'^Restore ([\d.]+) (HP|MP)\.',rf'Restore \1 of {who} \2.',text)
    text = re.sub(r'^Drain MP; power [\d.]+\.', f'Drain MP from {whom}.',text)
    text = re.sub(r'Apply (\w+) \(100%\)\.',r'Inflict \1.',text)
    text = re.sub(r'Apply (\w+) \((\d+)%\)\.',r'Inflict \1 with a \2% chance.',text)
    text = text.replace('Paralyzation','Paralysis').replace('Raise ','Increase ').replace('Also ','')
    text = re.sub(r'Apply (HP|MP) drain \((\d+)% of damage\)\.',
                  lambda m: ('Absorb damage dealt as ' + m[1] + '.' if m[2]=='100' else
                             'Absorb ' + m[2] + '% of damage dealt as ' + m[1] + '.'), text)
    text = re.sub(r'^(Drain MP from [^.]+\.) Absorb damage dealt as MP\.',r'\1',text)
    def status_list(match):
        pairs = re.findall(r'(\w+) \((\d+)%\)', match[1])
        if not pairs: return match[0]
        labels = {'DeffenceDown':'defense', 'MindDown':'spirit', 'AttackDown':'attack',
                  'IntelligenceDown':'magic', 'AgilityDown':'speed', 'Charme':'Charm'}
        names = [labels.get(name,name) for name,_ in pairs]
        joined = names[0] if len(names)==1 else ', '.join(names[:-1]) + ' and ' + names[-1]
        possible = any(int(chance)<100 for _,chance in pairs)
        if all(name.endswith('Down') for name,_ in pairs):
            return ('May lower ' if possible else 'Lower ') + joined + '.'
        return ('May inflict ' if possible else 'Inflict ') + joined + '.'
    text = re.sub(r'Apply ([^.]+)\.', status_list, text)
    for status, label in {'IntelligenceDown':'magic','AttackDown':'attack','DeffenceDown':'defense',
                          'MindDown':'spirit','AgilityDown':'speed'}.items():
        text=text.replace('Inflict '+status+'.','Lower '+label+'.')
    text=text.replace('Charme','Charm')
    text=re.sub(r'Restore ([\d.]+) of own (HP|MP)\.',r'Restore \1 \2 to self.',text)
    text=re.sub(r'Restore ([\d.]+) of an ally’s (HP|MP)\.',r'Restore \1 \2 to an ally.',text)
    text=re.sub(r'Restore ([\d.]+) of all allies’ (HP|MP)\.',r'Restore \1 \2 to all allies.',text)
    return text


def resonance(recipe, source, english, preset=None):
    text = english[recipe['from']]['desc']
    text = re.sub(r'^\[[^]]+\] ', '', text)
    row = {**source, **recipe.get('set',{})}
    # Native wording already describes secondary effects, target changes and
    # native duration placeholders. Change only the private damage's element/type.
    def damage(match):
        element = ELEMENTS[row['element']]
        element = '' if row['element']=='None' and row['DamageType']=='Physic' else element + ' '
        return 'Deal ' + element + ('physical' if row['DamageType']=='Physic' else 'magic') + ' damage'
    text = re.sub(r'Deal (?:(?:non-elemental|Lightning|Thunder|Fire|Ice|Water|Wind|Earth|Light|Dark) )?(?:physical|magic) damage', damage,text)
    if preset == 'primm' and recipe['from'] == 440030:
        text = text.replace('power of Blade Torrent', 'power of Moonlightbringer')
    return text


def revise(catalog, rows, english):
    skills = {row['ID']:row for row in rows('Skill/DT_SkillData').values()}
    localized = {row['id']:row for row in english['skills']}
    for preset in catalog['presets']:
        profile = preset['profile']
        audit = preset.setdefault('descriptionUpdate', {'schema':1, 'skills':[]})
        for key, recipe in profile.get('skills',{}).items():
            before = recipe.get('desc','')
            after = short_skill(recipe, skills[recipe['from']])
            if before != after:
                audit['skills'].append({'from':recipe['from'], 'name':recipe['en'],
                                        'before':before, 'after':after})
                recipe.update(desc=after,descAuto=False)
        lb=profile['lb_custom']; after=resonance(lb,skills[lb['from']],localized,preset['id'])
        previous=resonance(lb,skills[lb['from']],localized)
        if lb['desc'] != after:
            # Keep the original technical-text migration as well as the
            # previously shipped player-facing wording. Both saved versions
            # must reach the corrected text without resetting an edited kit.
            before=audit.get('resonance',{}).get('before',lb['desc'])
            audit['resonance']={'from':lb['from'], 'before':before, 'after':after}
            lb.update(desc=after,descAuto=False)
        if previous != after:
            audit['resonance'].update(previous=[previous],requiresActive=445300)
    return catalog


def standalone(profile, catalog):
    """Apply the same authored-text repairs to the independent Fina template."""
    update=next(p['descriptionUpdate'] for p in catalog['presets'] if p['id']=='crystal_fina')
    for recipe in profile.get('skills',{}).values():
        for edit in update['skills']:
            if (recipe.get('from'),recipe.get('en'),recipe.get('desc')) == (edit['from'],edit['name'],edit['before']):
                recipe.update(desc=edit['after'],descAuto=False)
    if profile.get('lb_custom',{}).get('from')==update['resonance']['from']:
        lb=profile['lb_custom']
        if lb.get('desc')==update['resonance']['before']:
            lb.update(desc=update['resonance']['after'],descAuto=False)
    return profile
