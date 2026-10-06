import 'package:flutter/material.dart';

import '../../design/theme.dart';

/// Read original snapshots, including an edited vision's immutable baseline.
/// Never infer a kit from ability names or representative PDF source labels.
List<Map<String, dynamic>> nativeKitOptions(List<dynamic> visions, Map unit) {
  final byId = <int, Map<String, dynamic>>{};
  for (final source in [unit, ...visions]) {
    if (source is! Map) continue;
    final native = source['native'] as Map?;
    final baseline = native?['baseline'] as Map?;
    final id = native?['id'] ?? source['id'];
    if (baseline == null || id is! int || baseline['en'] is! String) continue;
    byId[id] = {...Map<String, dynamic>.from(baseline), 'id': id};
  }
  return byId.values.toList()
    ..sort((a, b) => a['en'].toString().compareTo(b['en'].toString()));
}

bool nativeKitContains(Map? kit, String kind, num id) {
  if (kit == null) return true;
  final type = kind == 'skills' ? 'ActiveSkill' : 'PassiveSkill';
  return ['awakening', 'synchro'].any(
    (field) => (kit[field] as List? ?? []).any(
      (tier) => (tier as List).any(
        (grant) =>
            grant is List &&
            grant.length >= 2 &&
            grant[0] == type &&
            grant[1] == id,
      ),
    ),
  );
}

Map<String, dynamic>? selectedNativeKit(
  List<Map<String, dynamic>> options,
  int id,
) => options.where((u) => u['id'] == id).firstOrNull;

Map<String, dynamic>? nativeKitContext(
  Map<String, dynamic>? kit,
  Map<String, dynamic> unit,
) => kit == null
    ? unit
    : {
        'native': {'baseline': kit},
      };

class NativeKitFilter extends StatelessWidget {
  const NativeKitFilter({
    super.key,
    required this.options,
    required this.selected,
    required this.onChanged,
  });
  final List<Map<String, dynamic>> options;
  final int selected;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    if (options.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 6),
      child: Row(
        children: [
          Text('NATIVE KIT', style: Guide.label()),
          const SizedBox(width: 10),
          Expanded(
            child: DropdownButton<int>(
              key: const ValueKey('native-kit-filter'),
              value: options.any((u) => u['id'] == selected) ? selected : 0,
              isExpanded: true,
              style: Guide.text(),
              dropdownColor: Guide.paper,
              items: [
                const DropdownMenuItem(value: 0, child: Text('All visions')),
                for (final u in options)
                  DropdownMenuItem(
                    value: u['id'] as int,
                    child: Text(u['en'].toString()),
                  ),
              ],
              onChanged: (id) => onChanged(id ?? 0),
            ),
          ),
        ],
      ),
    );
  }
}
