import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../design/theme.dart';
import '../../design/widgets.dart';
import '../../design/description_tooltip.dart';
import '../../state/app_state.dart';
import '../../state/catalog_helpers.dart';
import '../../state/catalog_descriptions.dart';
import 'tiers.dart';

/// MR rewards use the engine's separate, zero-based synchro mastery rows.
class MrStep extends StatefulWidget {
  const MrStep({super.key, required this.unit, required this.set});
  final Map<String, dynamic> unit;
  final ValueChanged<Map<String, dynamic>> set;

  @override
  State<MrStep> createState() => _MrStepState();
}

class _MrStepState extends State<MrStep> {
  int _cap(int target) {
    final caps = (widget.unit['native'] as Map?)?['synchroCaps'] as List?;
    return caps != null && target < caps.length ? caps[target] as int : 5;
  }

  static const stats = [...statParams, (11, 'Equip cost', 8)];
  final amounts = <int, int>{for (final p in stats) p.$1: p.$3};
  int rank = 0;
  String query = '';
  String group = 'all';

  List<List<dynamic>> _rewards() {
    final rows = (widget.unit['synchro'] as List? ?? [])
        .map(
          (row) =>
              (row as List).map((g) => List<dynamic>.from(g as List)).toList(),
        )
        .toList();
    while (widget.unit['native'] == null && rows.length < 10) {
      rows.add([]);
    }
    return rows;
  }

  void _full(int target) => ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        'MR ${target + 1} already has ${_cap(target)} rewards. Remove or move one first.',
      ),
    ),
  );

  void _add(Grant grant) {
    final rows = _rewards();
    if (rows[rank].length >= _cap(rank)) {
      _full(rank);
      return;
    }
    // Stat boosts can stack; avoid granting the same skill twice at one rank.
    if (grant[0] != 'BaseParameter' &&
        rows[rank].any((g) => sameGrant(g, grant))) {
      return;
    }
    rows[rank].add(List<dynamic>.from(grant));
    widget.set({'synchro': rows});
  }

  void _move(int from, int index, int to) {
    if (from == to) {
      return;
    }
    final rows = _rewards();
    if (rows[to].length >= _cap(to)) {
      _full(to);
      return;
    }
    final grant = rows[from][index];
    if (grant[0] != 'BaseParameter' &&
        rows[to].any((g) => sameGrant(g, grant))) {
      return;
    }
    rows[from].removeAt(index);
    rows[to].add(grant);
    widget.set({'synchro': rows});
  }

  void _remove(int row, int index) {
    final rows = _rewards();
    rows[row].removeAt(index);
    widget.set({'synchro': rows});
  }

  @override
  Widget build(BuildContext context) {
    final app = context.read<AppState>();
    final cat = app.catalog ?? {};
    String abilityTitle(Map<String, dynamic> row) =>
        catalogEntryTitle(cat, 'skills', row);
    String passiveTitle(Map<String, dynamic> row) =>
        catalogEntryTitle(cat, 'passives', row);
    final skillDescriptions = catalogDescriptions(cat, 'skills');
    final passiveDescriptions = catalogDescriptions(cat, 'passives');
    final visibleSkills = {
      for (final s in catalogLibrary(cat, 'skills', [
        ...app.units,
        widget.unit,
      ]))
        s['id'],
    };
    final visiblePassives = {
      for (final p in catalogLibrary(cat, 'passives', [
        ...app.units,
        widget.unit,
      ]))
        p['id'],
    };
    final rows = _rewards();
    final skills = <num, Map<String, dynamic>>{
      for (final s in (cat['skills'] as List? ?? []))
        (s as Map)['id'] as num: {
          ...Map<String, dynamic>.from(s),
          'desc': skillDescriptions[s['id']] ?? '',
        },
      for (final e in (widget.unit['skills'] as Map? ?? {}).entries)
        int.parse(e.key.toString()): {
          'id': int.parse(e.key.toString()),
          'name': (e.value as Map)['en'],
          'desc': e.value['desc'],
          'custom': true,
        },
    };
    final passives = <num, Map<String, dynamic>>{
      for (final p in (cat['passives'] as List? ?? []))
        (p as Map)['id'] as num: {
          ...Map<String, dynamic>.from(p),
          'desc': passiveDescriptions[p['id']] ?? '',
        },
    };
    final master = widget.unit['master'] as Map?;
    final library = <Map<String, dynamic>>[
      for (final s in skills.values)
        if (s['custom'] == true || visibleSkills.contains(s['id']))
          {...s, 'kind': 'ActiveSkill', 'title': abilityTitle(s)},
      for (final p in passives.values)
        if (visiblePassives.contains(p['id']))
          {...p, 'kind': 'PassiveSkill', 'title': passiveTitle(p)},
      if (master != null)
        {
          'id': master['id'],
          'name': master['en'],
          'title': master['en'],
          'desc': master['desc'],
          'kind': 'MasterSkill',
        },
    ]..sort((a, b) => a['title'].toString().compareTo(b['title'].toString()));
    final q = query.trim().toLowerCase();
    final shown = library
        .where(
          (r) =>
              (group == 'all' || r['kind'] == group) &&
              (q.isEmpty ||
                  '${r['title']} ${r['desc'] ?? ''}'.toLowerCase().contains(q)),
        )
        .toList();
    String statName(num id) =>
        stats.where((s) => s.$1 == id).map((s) => s.$2).firstOrNull ??
        'Stat $id';
    String grantName(Grant g) => switch (g[0]) {
      'BaseParameter' => statName(g[1] as num),
      'ActiveSkill' =>
        skills[g[1]] == null ? 'Ability ${g[1]}' : abilityTitle(skills[g[1]]!),
      'PassiveSkill' =>
        passives[g[1]] == null
            ? 'Passive ${g[1]}'
            : passiveTitle(passives[g[1]]!),
      'MasterSkill' when g[1] == master?['id'] =>
        (master?['en'] ?? 'Master reward').toString(),
      _ => '${g[0]} ${g[1]}',
    };
    String grantDescription(Grant g) => switch (g[0]) {
      'ActiveSkill' => (skills[g[1]]?['desc'] ?? '').toString(),
      'PassiveSkill' => (passives[g[1]]?['desc'] ?? '').toString(),
      'MasterSkill' => (master?['desc'] ?? '').toString(),
      _ => '',
    };

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Band('MR rewards', color: Guide.blue),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Text('ADD TO', style: Guide.label()),
                    const SizedBox(width: 10),
                    DropdownButton<int>(
                      key: const ValueKey('mr-target'),
                      value: rank,
                      items: [
                        for (var i = 0; i < rows.length; i++)
                          DropdownMenuItem(
                            value: i,
                            child: Text('MR ${i + 1}'),
                          ),
                      ],
                      onChanged: (i) {
                        if (i != null) {
                          setState(() => rank = i);
                        }
                      },
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Up to ${_cap(rank)} rewards at this rank. Unlock points stay unchanged.',
                        style: Guide.small(),
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final p in stats)
                      Container(
                        decoration: BoxDecoration(
                          border: Border.all(color: Guide.hairline),
                        ),
                        padding: const EdgeInsets.only(left: 8),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(p.$2, style: Guide.strong()),
                            SizedBox(
                              width: 52,
                              child: TextFormField(
                                key: ValueKey('mr-stat-${p.$1}'),
                                initialValue: '${amounts[p.$1]}',
                                textAlign: TextAlign.center,
                                keyboardType:
                                    const TextInputType.numberWithOptions(
                                      signed: true,
                                    ),
                                decoration: const InputDecoration(
                                  contentPadding: EdgeInsets.all(6),
                                ),
                                onChanged: (text) {
                                  final n = int.tryParse(text);
                                  if (n != null) {
                                    amounts[p.$1] = n;
                                  }
                                },
                              ),
                            ),
                            IconButton(
                              tooltip: 'Add ${p.$2} to MR ${rank + 1}',
                              icon: const Icon(Icons.add, size: 18),
                              onPressed: () =>
                                  _add(['BaseParameter', p.$1, amounts[p.$1]!]),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
              Band('Abilities and passives', color: Guide.purple),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        decoration: const InputDecoration(
                          hintText: 'Search MR rewards',
                          prefixIcon: Icon(Icons.search, size: 18),
                        ),
                        onChanged: (text) => setState(() => query = text),
                      ),
                    ),
                    const SizedBox(width: 8),
                    DropdownButton<String>(
                      value: group,
                      items: const [
                        DropdownMenuItem(
                          value: 'all',
                          child: Text('All rewards'),
                        ),
                        DropdownMenuItem(
                          value: 'ActiveSkill',
                          child: Text('Abilities'),
                        ),
                        DropdownMenuItem(
                          value: 'PassiveSkill',
                          child: Text('Passives'),
                        ),
                        DropdownMenuItem(
                          value: 'MasterSkill',
                          child: Text('Master reward'),
                        ),
                      ],
                      onChanged: (v) => setState(() => group = v ?? 'all'),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: shown.length,
                  itemBuilder: (_, i) {
                    final r = shown[i];
                    final granted = rows[rank].any(
                      (g) => g[0] == r['kind'] && g[1] == r['id'],
                    );
                    return Container(
                      color: i.isOdd ? Guide.paper2 : Guide.paper,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: DescriptionTooltip(
                              title: r['title'].toString(),
                              description: (r['desc'] ?? '').toString(),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    r['title'].toString(),
                                    style: Guide.strong(),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  Text(
                                    (r['desc'] ?? '').toString(),
                                    style: Guide.small(),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          ),
                          IconButton(
                            tooltip: granted
                                ? 'Already granted at MR ${rank + 1}'
                                : 'Add to MR ${rank + 1}',
                            icon: Icon(
                              granted ? Icons.check : Icons.add,
                              size: 18,
                            ),
                            onPressed: granted
                                ? null
                                : () => _add([r['kind'], r['id']]),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
        Container(width: 1, color: Guide.hairline),
        SizedBox(
          width: 380,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Band('Learned by MR', color: Guide.ink),
              Expanded(
                child: ListView(
                  key: const ValueKey('mr-ranks'),
                  padding: const EdgeInsets.all(12),
                  children: [
                    for (var i = 0; i < rows.length; i++)
                      Container(
                        key: ValueKey('mr-rank-$i'),
                        margin: const EdgeInsets.only(bottom: 10),
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: rank == i ? Guide.blue : Guide.ink,
                            width: rank == i ? 2 : 1,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            InkWell(
                              onTap: () => setState(() => rank = i),
                              child: Container(
                                color: Guide.paper2,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 8,
                                ),
                                child: Row(
                                  children: [
                                    Text('MR ${i + 1}', style: Guide.label()),
                                    const Spacer(),
                                    Text(
                                      '${rows[i].length}/${_cap(i)}',
                                      style: Guide.num(),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            if (rows[i].isEmpty)
                              Padding(
                                padding: const EdgeInsets.all(10),
                                child: Text(
                                  'No rewards at this rank.',
                                  style: Guide.small(),
                                ),
                              ),
                            for (var j = 0; j < rows[i].length; j++)
                              Padding(
                                key: ValueKey('mr-grant-$i-$j'),
                                padding: const EdgeInsets.fromLTRB(10, 4, 0, 4),
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: DescriptionTooltip(
                                        title: grantName(rows[i][j]),
                                        description: grantDescription(
                                          rows[i][j],
                                        ),
                                        child: Text(
                                          grantName(rows[i][j]),
                                          style: Guide.strong(),
                                          maxLines: 3,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                    ),
                                    if (rows[i][j][0] == 'BaseParameter')
                                      SizedBox(
                                        width: 56,
                                        child: TextFormField(
                                          key: ValueKey(
                                            'mr-amount-$i-$j-${rows[i][j]}',
                                          ),
                                          initialValue:
                                              '${rows[i][j].length > 2 ? rows[i][j][2] : 0}',
                                          textAlign: TextAlign.center,
                                          keyboardType:
                                              const TextInputType.numberWithOptions(
                                                signed: true,
                                              ),
                                          decoration: const InputDecoration(
                                            contentPadding: EdgeInsets.all(6),
                                          ),
                                          onFieldSubmitted: (value) {
                                            final n = int.tryParse(value);
                                            if (n == null) {
                                              return;
                                            }
                                            final updated = _rewards();
                                            updated[i][j] = [
                                              'BaseParameter',
                                              rows[i][j][1],
                                              n,
                                            ];
                                            widget.set({'synchro': updated});
                                          },
                                        ),
                                      ),
                                    PopupMenuButton<int>(
                                      tooltip: 'Move reward',
                                      icon: const Icon(
                                        Icons.arrow_forward,
                                        size: 16,
                                      ),
                                      itemBuilder: (_) => [
                                        for (var to = 0; to < rows.length; to++)
                                          PopupMenuItem(
                                            value: to,
                                            enabled: to != i,
                                            child: Text('MR ${to + 1}'),
                                          ),
                                      ],
                                      onSelected: (to) => _move(i, j, to),
                                    ),
                                    IconButton(
                                      tooltip: 'Remove reward',
                                      icon: const Icon(Icons.close, size: 16),
                                      onPressed: () => _remove(i, j),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
