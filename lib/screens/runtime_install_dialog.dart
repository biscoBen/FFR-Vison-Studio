import 'package:flutter/material.dart';

import '../services/api.dart';

/// Ask before building so a fresh installation cannot fail after a long build.
Future<bool> confirmRuntimeInstall(BuildContext context, Api api, {bool lastBuild = false}) async {
  final runtime = await api.runtimeStatus(lastBuild: lastBuild);
  if (runtime['required'] != true || runtime['ready'] == true) return true;
  if (!context.mounted) return false;
  final choice = await showDialog<String>(context: context, builder: (dialog) => AlertDialog(
    title: const Text('Install UE4SS?'),
    content: const SizedBox(width: 440, child: Text(
      'UE4SS enables overworld replacements and cycling, Crystal Fina’s runtime effects and movie music, '
      'and Eiko’s custom esper bonuses.\n\n'
      'Install the bundled loader with your mod, or continue with those features disabled. '
      'Your visions and their normal skills will still install. Existing mods are preserved.',
    )),
    actions: [
      TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Cancel')),
      TextButton(onPressed: () => Navigator.pop(dialog, 'skip'), child: const Text('Continue without it')),
      FilledButton(onPressed: () => Navigator.pop(dialog, 'install'), child: const Text('Install UE4SS')),
    ],
  ));
  if (choice == null) return false;
  await api.runtimeChoice(runtime['game'] as String, choice);
  return true;
}
