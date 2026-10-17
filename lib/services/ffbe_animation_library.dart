import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;

import 'paths.dart';

/// Installs only the browsable source library, outside mod inputs and game files.
class FfbeAnimationLibrary {
  static const revision = 'memorial-en-v208-1';
  static const assetRoot = 'assets/ffbe_library';

  Future<void> prepare(
    AppPaths paths, {
    Future<Uint8List> Function(String)? readAsset,
    void Function(int completed, int total)? onProgress,
  }) async {
    Future<Uint8List> read(String path) async {
      if (readAsset != null) return readAsset(path);
      final data = await rootBundle.load(path);
      return data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
    }

    final raw = await read('$assetRoot/manifest.json');
    final manifest = json.decode(utf8.decode(raw)) as Map;
    if (manifest['schema'] != 1 || manifest['revision'] != revision) {
      throw StateError('Unsupported FFBE animation library.');
    }
    final root = p.join(paths.engineDir, 'library', 'ffbe');
    File checked(String relative) {
      var node = p.join(root, relative);
      final file = File(node);
      while (p.isWithin(paths.root, node) || p.equals(paths.root, node)) {
        if (FileSystemEntity.isLinkSync(node)) {
          throw StateError('Linked FFBE library path: $node');
        }
        if (p.equals(paths.root, node)) break;
        node = p.dirname(node);
      }
      return file;
    }

    final packs = (manifest['packs'] as List).cast<Map>();
    var completed = 0;
    onProgress?.call(completed, packs.length);
    for (final pack in packs) {
      final name = pack['name'] as String;
      if (!RegExp(r'^library-\d{2}\.zip$').hasMatch(name) ||
          pack['bytes'] is! int ||
          (pack['bytes'] as int) <= 0 ||
          !RegExp(r'^[a-f0-9]{64}$').hasMatch(pack['sha256'].toString())) {
        throw StateError('Invalid FFBE library pack.');
      }
      final file = checked(p.join(revision, name));
      if (file.existsSync() &&
          await file.length() == pack['bytes'] &&
          (await sha256.bind(file.openRead()).first).toString() ==
              pack['sha256']) {
        onProgress?.call(++completed, packs.length);
        continue;
      }
      final bytes = await read('$assetRoot/$name');
      if (bytes.length != pack['bytes'] ||
          sha256.convert(bytes).toString() != pack['sha256']) {
        throw StateError('FFBE animation library checksum mismatch: $name');
      }
      await file.parent.create(recursive: true);
      final temporary = checked(p.join(revision, '$name.staging'));
      await temporary.writeAsBytes(bytes, flush: true);
      if (file.existsSync()) await file.delete();
      await temporary.rename(file.path);
      onProgress?.call(++completed, packs.length);
    }
    final file = checked('manifest.json');
    await file.parent.create(recursive: true);
    if (!file.existsSync() || await file.readAsString() != utf8.decode(raw)) {
      final temporary = checked('manifest.json.staging');
      await temporary.writeAsBytes(raw, flush: true);
      if (file.existsSync()) await file.delete();
      await temporary.rename(file.path);
      onProgress?.call(++completed, packs.length);
    }
  }
}
