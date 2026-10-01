import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../design/theme.dart';
import '../../design/widgets.dart';
import '../../state/app_state.dart';

/// Keep native Resonances intact until the user selects another existing one.
class NativeResonanceStep extends StatelessWidget {
  const NativeResonanceStep({super.key, required this.unit, required this.set});
  final Map<String, dynamic> unit;
  final ValueChanged<Map<String, dynamic>> set;

  @override
  Widget build(BuildContext context) {
    final cat = context.read<AppState>().catalog ?? {};
    final choices = (cat['skills'] as List? ?? [])
        .cast<Map<String, dynamic>>()
        .where((s) => s['attr'] == 'FinishBlow')
        .toList();
    final selected = choices.where((s) => s['id'] == unit['lb']).firstOrNull;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Band('Game vision Resonance', color: Guide.gold),
        Box(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                selected?['name']?.toString() ?? 'Resonance ${unit['lb']}',
                style: Guide.h2(),
              ),
              const SizedBox(height: 8),
              Text((selected?['desc'] ?? '').toString(), style: Guide.text()),
              const SizedBox(height: 16),
              Text(
                'Changing the model preserves this Resonance and its cinematic. Choose another existing Resonance below to replace it.',
                style: Guide.small(),
              ),
              const SizedBox(height: 12),
              DropdownButton<num>(
                isExpanded: true,
                value: selected?['id'] as num?,
                hint: const Text('Choose a game Resonance'),
                items: [
                  for (final s in choices)
                    DropdownMenuItem(
                      value: s['id'] as num,
                      child: Text(
                        '${s['name']}${(s['seq'] as List?)?.isNotEmpty == true ? '' : ' (Unverified)'}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: (id) {
                  if (id != null) {
                    set({'lb': id});
                  }
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}
