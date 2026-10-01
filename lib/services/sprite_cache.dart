import 'dart:convert';
import 'dart:io';

import 'package:archive/archive_io.dart';
import 'package:path/path.dart' as p;

import 'downloader.dart';
import 'paths.dart';

/// Track every file in a hosted sprite pack, rather than trusting .complete.
class SpriteCache {
  SpriteCache(this.paths, this.downloader);
  final AppPaths paths;
  final Downloader downloader;

  String directory(String form) => p.join(paths.engineSprites, form);
  File previewMarker(String form) =>
      File(p.join(directory(form), '.studio-preview-ready'));
  bool previewReady(String form) {
    try {
      return previewMarker(form).readAsStringSync() == '1';
    } catch (_) {
      return false;
    }
  }

  File _inventory(String form) =>
      File(p.join(directory(form), '.studio-sprites.json'));

  bool _safeName(String name) =>
      name.isNotEmpty &&
      !p.isAbsolute(name) &&
      !name.contains(':') &&
      !name.contains('\\') &&
      !name.split('/').contains('..');
  bool _present(String form, String name, {bool nonempty = true}) {
    final file = File(p.join(directory(form), name));
    return file.existsSync() && (!nonempty || file.lengthSync() > 0);
  }

  bool hasSheets(String form) =>
      _present(form, 'unit_anime_$form.png') &&
      _present(form, 'unit_cgg_$form.csv');

  bool isComplete(String form) {
    try {
      final record = json.decode(_inventory(form).readAsStringSync()) as Map;
      final files = (record['files'] as Map).cast<String, int>();
      return record['version'] == 1 &&
          hasSheets(form) &&
          files.containsKey('unit_anime_$form.png') &&
          files.containsKey('unit_cgg_$form.csv') &&
          files.entries.every(
            (entry) =>
                _safeName(entry.key) &&
                _present(form, entry.key, nonempty: entry.value > 0),
          );
    } catch (_) {
      return false;
    }
  }

  /// Fill absent/empty files; retain existing artwork and a reusable verified ZIP.
  Future<bool> ensure(
    String form,
    Map<String, dynamic>? info, {
    void Function(String)? onStep,
  }) async {
    if (!RegExp(r'^\d+$').hasMatch(form)) {
      throw StateError('Invalid character form $form.');
    }
    if (isComplete(form)) {
      return false;
    }
    if (info == null) {
      if (hasSheets(form)) {
        return false;
      } // Older/offline engines can still use their installed packs.
      throw StateError(
        'No sprite pack for form $form is available on the host yet.',
      );
    }
    final ready = previewMarker(form);
    if (ready.existsSync()) {
      ready.deleteSync();
    }
    onStep?.call('downloading missing sprites');
    final zip = await downloader.download(
      info['url'] as String,
      p.join(paths.downloads, '$form.zip'),
      sha256: info['sha256'] as String?,
    );
    final input = InputFileStream(zip.path);
    late Map<String, int> files;
    try {
      files = {
        for (final entry
            in ZipDecoder()
                .decodeStream(input)
                .files
                .where((entry) => entry.isFile))
          if (_safeName(entry.name.replaceAll('\\', '/')))
            entry.name.replaceAll('\\', '/'): entry.size,
      };
    } finally {
      await input.close();
    }
    if (!files.containsKey('unit_anime_$form.png') ||
        !files.containsKey('unit_cgg_$form.csv')) {
      throw StateError('The sprite pack for $form is incomplete.');
    }
    onStep?.call('unpacking missing sprites');
    await Downloader.unzip(zip, directory(form), overwriteExisting: false);
    if (!hasSheets(form) ||
        !files.entries.every(
          (entry) => _present(form, entry.key, nonempty: entry.value > 0),
        )) {
      throw StateError('The sprite pack for $form is incomplete.');
    }
    _inventory(form)
        .writeAsStringSync(json.encode({'version': 1, 'files': files}));
    File(p.join(directory(form), '.complete'))
        .writeAsStringSync(DateTime.now().toIso8601String());
    return true;
  }
}
