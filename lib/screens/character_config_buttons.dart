import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../services/character_config.dart';
import '../state/app_state.dart';

/// Fixed to the bottom of the character/roster page, outside the scroll area.
class CharacterConfigButtons extends StatefulWidget {
  const CharacterConfigButtons({super.key});
  @override
  State<CharacterConfigButtons> createState() => _CharacterConfigButtonsState();
}

class _CharacterConfigButtonsState extends State<CharacterConfigButtons> {
  bool busy = false;

  Future<void> _save(AppState app, String key) async {
    setState(() => busy = true);
    try {
      final unit = await app.snapshotCharacter(key);
      final contents = CharacterConfig.encode(unit);
      await Directory(app.paths.characterConfigs).create(recursive: true);
      final name = (unit['en'] as String)
          .replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1f]'), '_')
          .replaceAll(RegExp(r'[. ]+$'), '');
      final destination = await FilePicker.platform.saveFile(
        dialogTitle: 'Save character config',
        fileName: '${name.isEmpty ? 'Character' : name}.vision.json',
        initialDirectory: app.paths.characterConfigs,
        type: FileType.custom,
        allowedExtensions: ['json'],
        lockParentWindow: true,
      );
      if (destination == null) {
        return;
      }
      final path = destination.toLowerCase().endsWith('.json')
          ? destination
          : '$destination.vision.json';
      // Encode first, then replace atomically so a failed write keeps an older save.
      final temporary = File(
        '$path.${DateTime.now().microsecondsSinceEpoch}.tmp',
      );
      try {
        await temporary.writeAsString(contents, flush: true);
        await temporary.rename(path);
      } finally {
        if (await temporary.exists()) {
          await temporary.delete();
        }
      }
      if (mounted) {
        _message(
          'Character config saved',
          '${unit['en']} was saved to:\n$path\n\nYou can remove the character and load this file later to restore its setup.',
        );
      }
    } catch (e) {
      if (mounted) {
        _message('Could not save character config', e.toString());
      }
    } finally {
      if (mounted) {
        setState(() => busy = false);
      }
    }
  }

  Future<void> _load(AppState app) async {
    final navigator = Navigator.of(context);
    setState(() => busy = true);
    var progressOpen = false;
    try {
      await Directory(app.paths.characterConfigs).create(recursive: true);
      final picked = await FilePicker.platform.pickFiles(
        dialogTitle: 'Load character config',
        initialDirectory: app.paths.characterConfigs,
        type: FileType.custom,
        allowedExtensions: ['json'],
        lockParentWindow: true,
      );
      final path = picked?.files.single.path;
      if (path == null) {
        return;
      }
      final file = File(path);
      if (await file.length() > CharacterConfig.maxBytes) {
        throw const FormatException(
          'This file is too large to be a character config.',
        );
      }
      final saved = CharacterConfig.decode(await file.readAsString());
      final target = CharacterConfig.target(saved, app.units);
      if (!mounted) {
        return;
      }
      final ok = await showDialog<bool>(
        context: context,
        builder: (c) => AlertDialog(
          backgroundColor: Guide.paper,
          shape: Border.fromBorderSide(Guide.frame),
          title: Text(
            target == null
                ? 'Restore ${saved['en']}?'
                : 'Load config for ${target['en']}?',
            style: Guide.h2(),
          ),
          content: Text(
            target == null
                ? 'Adds ${saved['en']} back to your visions with the saved abilities, passives, stats and Resonance.'
                : 'Replaces ${target['en']}\'s current setup with the saved abilities, passives, stats and Resonance. A backup of your current roster is kept automatically.',
            style: Guide.text(),
          ),
          actions: [
            GuideButton('Cancel', onPressed: () => Navigator.pop(c, false)),
            GuideButton(
              'Load character config',
              onPressed: () => Navigator.pop(c, true),
            ),
          ],
        ),
      );
      if (ok != true || !mounted) {
        return;
      }
      progressOpen = true;
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => PopScope(
          canPop: false,
          child: AlertDialog(
            backgroundColor: Guide.paper,
            content: Row(
              children: [
                const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(),
                ),
                const SizedBox(width: 16),
                Text('Loading character config…', style: Guide.text()),
              ],
            ),
          ),
        ),
      );
      await app.loadCharacterConfig(
        saved,
        expectedTargetKey: target?['key'] as String?,
      );
      if (navigator.mounted) {
        navigator.pop();
        progressOpen = false;
      }
      if (navigator.mounted) {
        _message(
          'Character config loaded',
          '${saved['en']} is ready with its saved setup. Build or install the mod to apply it to the game.',
          dialogContext: navigator.context,
        );
      }
    } catch (e) {
      if (navigator.mounted && progressOpen) {
        navigator.pop();
        progressOpen = false;
      }
      if (mounted) {
        _message('Could not load character config', e.toString());
      }
    } finally {
      if (mounted) {
        setState(() => busy = false);
      }
    }
  }

  void _message(String title, String message, {BuildContext? dialogContext}) =>
      showDialog<void>(
        context: dialogContext ?? context,
        builder: (c) => AlertDialog(
          backgroundColor: Guide.paper,
          shape: Border.fromBorderSide(Guide.frame),
          title: Text(title, style: Guide.h2()),
          content: SelectableText(message, style: Guide.text()),
          actions: [GuideButton('OK', onPressed: () => Navigator.pop(c))],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final selected = app.selected;
    return Container(
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: Guide.hairline)),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          GuideButton(
            'Save character config',
            icon: Icons.save_outlined,
            onPressed: busy || selected == null
                ? null
                : () => _save(app, selected['key'] as String),
          ),
          const SizedBox(height: 8),
          GuideButton(
            'Load character config',
            icon: Icons.folder_open,
            onPressed: busy || app.api == null || app.engineDown || app.building
                ? null
                : () => _load(app),
          ),
        ],
      ),
    );
  }
}
