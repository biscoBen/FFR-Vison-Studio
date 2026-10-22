"""Resolve native demo/production tables without changing prepared source rows."""
import copy
import json
from pathlib import Path
import re

PREFIX = 'FFRS/Content/Datatable/'
COMPOSITES = {
    'Asset/Skill/DT_SkillAsset': 'Asset/Skill/CDT_SkillAsset_Demo',
    'Asset/Battle/Stage/DT_BtlStageAsset': 'Asset/Battle/Stage/CDT_BtlStageAsset_Demo',
    'Event/TalkEvent/MainEvent/DT_TalkEventData_Chapter01': 'Event/TalkEvent/CDT_TalkEventData_Demo',
    'Event/TalkEvent/LegendEvent/DT_TalkEventData_LegendEvent': 'Event/TalkEvent/CDT_TalkEventData_Demo',
    'Map/MapData/DT_MapData_00Com': 'Map/CDT_MapData_Demo',
}


class NativeTables:
    def __init__(self, root, source=None):
        self.root = Path(root)
        self.source = source or self.file_rows
        self._stamp = None
        self._inventory = None

    def file_rows(self, rel):
        return json.loads((self.root / 'extracted/rows' / (rel + '.json')).read_text(encoding='utf-8-sig'))['rows']

    def available(self, rel):
        # The official listing wins over leftover files from another build.
        listing = self.root / 'extracted/utoc_filelist.tsv'
        stamp = (listing.stat().st_mtime_ns, listing.stat().st_size) if listing.is_file() else None
        if stamp != self._stamp or self._inventory is None:
            self._stamp = stamp
            self._inventory = set()
            if stamp is not None:
                self._inventory = set(re.findall(r'FFRS/Content/Datatable/[^\t\r\n]+?\.uasset',
                    listing.read_text(encoding='utf-8-sig')))
        if stamp is not None: return PREFIX + rel + '.uasset' in self._inventory
        return any((self.root / folder / (prefix + rel + suffix)).is_file()
                   for folder, prefix, suffix in (('extracted/rows', '', '.json'),
                       ('extracted/legacy', PREFIX, '.uasset')))

    def resolve(self, rel):
        if rel.endswith('_Demo'):
            prod = rel[:-5] + '_Prod'
            if self.available(prod) and not self.available(rel): return prod
        return rel

    def parents(self, rel):
        if rel.endswith(('_Demo', '_Prod')): return [self.resolve(rel)]
        prod = rel + '_Prod'
        if not self.available(prod): return [rel]
        return ([rel] if self.available(rel) else []) + [prod]

    def __call__(self, rel):
        parents = self.parents(rel)
        if len(parents) == 1: return self.source(parents[0])
        result = {}
        composite = None
        for parent in parents:
            for key, value in self.source(parent).items():
                if key in result and result[key] != value:
                    # Match the native cooked composite, not an assumed parent order.
                    target = self.resolve(COMPOSITES.get(rel, ''))
                    if not target or not self.available(target):
                        raise ValueError('Conflicting native table rows require a composite: ' + rel + '/' + key)
                    if composite is None: composite = self.source(target)
                    authoritative = composite.get(key)
                    if authoritative not in (result[key], value):
                        raise ValueError('Native parent/composite rows disagree: ' + rel + '/' + key)
                    result[key] = authoritative
                else: result[key] = value
        return result

    def normalize(self, tables):
        """Move recipes to real parents; cooked composites get their own edits.

        A production-only donor must be cloned inside its production parent,
        never inserted into the read-only dump of the shared table.
        """
        result = {}
        for rel, plan in tables.items():
            parents = self.parents(rel)
            if len(parents) == 1:
                target = parents[0]
                out = result.setdefault(target, {**copy.deepcopy(plan), 'asset': PREFIX + target, 'add': [], 'set': []})
                for kind in ('add', 'set'): out[kind].extend(copy.deepcopy(plan.get(kind, [])))
                continue
            originals = {p: self.source(p) for p in parents}
            combined = self(rel)
            added = {}
            def owners(key):
                if key in added: return added[key]
                if key not in combined: raise ValueError('Native recipe row is unavailable: ' + rel + '/' + key)
                return [p for p, values in originals.items() if values.get(key) == combined[key]]
            def emit(parent, kind, entry):
                out = result.setdefault(parent, {'asset': PREFIX + parent, 'add': [], 'set': []})
                out[kind].append(copy.deepcopy(entry))
            for entry in plan.get('add', []):
                sources = owners(entry['cloneFrom'])
                targets = owners(entry['row']) if entry['row'] in combined else sources[:1]
                for target in targets:
                    if target not in sources:
                        raise ValueError('Native clone and destination have different parent tables: ' + rel + '/' + entry['row'])
                    emit(target, 'add', entry)
                added[entry['row']] = targets
            for entry in plan.get('set', []):
                for target in owners(entry['row']): emit(target, 'set', entry)
        tables.clear()
        tables.update(result)
        return tables


def reader(root, source=None):
    return source if isinstance(source, NativeTables) else NativeTables(root, source)


def normalize(root, tables, rows=None):
    return reader(root, rows).normalize(tables)


def install_catalog(catalog, root):
    if getattr(catalog, '_native_tables_installed', False): return
    catalog.rows = reader(root, catalog.rows)
    original = catalog.load
    def load(*args, **kwargs):
        value = copy.deepcopy(original(*args, **kwargs))
        if not catalog.rows.available('Asset/Skill/DT_SkillAsset_Prod'): return value
        assets = {r['ID']: r for r in catalog.rows('Asset/Skill/DT_SkillAsset').values()}
        for skill in value.get('skills', []):
            offsets = [off for off in (0, 1, 2) if skill['id'] + off in assets]
            skill['seq'] = offsets
            skill['seqPath'] = assets[skill['id'] + offsets[0]]['LevelSequence'] if offsets else None
        return value
    catalog.load = load
    catalog._native_tables_installed = True
