import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;

import 'crystal_fina.dart';
import 'paths.dart';

typedef FeatureAssetReader = Future<Uint8List> Function(String path);
typedef FeatureProcessRunner = Future<ProcessResult> Function(
  String executable,
  List<String> arguments,
  String workingDirectory,
);

class BundledFeatures {
  BundledFeatures({
    FeatureAssetReader? readAsset,
    FeatureProcessRunner? runProcess,
  }) : _readAsset =
           readAsset ??
           ((path) async {
             final data = await rootBundle.load(path);
             return data.buffer.asUint8List(
               data.offsetInBytes,
               data.lengthInBytes,
             );
           }),
       _runProcess =
           runProcess ??
           ((exe, args, dir) => Process.run(
             exe,
             args,
             workingDirectory: dir,
             runInShell: false,
           ));
  final FeatureAssetReader _readAsset;
  final FeatureProcessRunner _runProcess;
  Future<Map<String, Uint8List>>? _payload;

  Future<Map<String, Uint8List>> _load() => _payload ??= _verifiedPayload();

  Future<Map<String, Uint8List>> _verifiedPayload() async {
    final manifest = json.decode(
      utf8.decode(await _readAsset('${CrystalFina.assetRoot}/manifest.json')),
    ) as Map;
    if (manifest['schema'] != 1 ||
        manifest['feature'] != CrystalFina.presetId) {
      throw StateError('Crystal Fina bundle manifest is unsupported.');
    }
    final files = <String, Uint8List>{};
    for (final entry in (manifest['files'] as Map).entries) {
      final relative = entry.key as String;
      _safeRelative(relative);
      final data = await _readAsset('${CrystalFina.assetRoot}/$relative');
      if (sha256.convert(data).toString() != entry.value) {
        throw StateError('Crystal Fina bundle checksum mismatch: $relative');
      }
      files[relative] = data;
    }
    for (final required in [
      'profile.json',
      'engine/install_crystalfina.py',
      'engine/payload/manifest.json',
      'engine/payload/_ffr_crystalfina.py',
      'units/custom/crystal_fina_2/detail.json',
    ]) {
      if (!files.containsKey(required)) {
        throw StateError('Crystal Fina bundle is incomplete: $required');
      }
    }
    return files;
  }

  void _safeRelative(String path) {
    if (path.isEmpty ||
        path.contains('\\') ||
        path.contains(':') ||
        p.posix.isAbsolute(path) ||
        path
            .split('/')
            .any((part) => part.isEmpty || part == '.' || part == '..')) {
      throw StateError('Unsafe Crystal Fina bundle path.');
    }
  }

  File _file(String root, String relative) {
    _safeRelative(relative);
    final path = p.joinAll([root, ...relative.split('/')]);
    var node = path;
    while (p.isWithin(p.absolute(root), p.absolute(node)) ||
        p.equals(p.absolute(root), p.absolute(node))) {
      if (FileSystemEntity.isLinkSync(node)) {
        throw StateError('Crystal Fina runtime path is a link: $node');
      }
      if (p.equals(p.absolute(node), p.absolute(root))) {
        break;
      }
      node = p.dirname(node);
    }
    return File(path);
  }

  Future<void> _write(File file, Uint8List data) async {
    if (file.existsSync() &&
        sha256.convert(await file.readAsBytes()) == sha256.convert(data)) {
      return;
    }
    await file.parent.create(recursive: true);
    final temporary = File('${file.path}.staging');
    try {
      await temporary.writeAsBytes(data, flush: true);
      // The engine is stopped for managed extension changes. Source assets are
      // only replaced if they are still the exact version previously supplied.
      if (file.existsSync()) {
        await file.delete();
      }
      await temporary.rename(file.path);
    } finally {
      if (temporary.existsSync()) {
        await temporary.delete();
      }
    }
  }

  Future<Map<String, dynamic>> profile() async =>
      json.decode(utf8.decode((await _load())['profile.json']!))
          as Map<String, dynamic>;

  Future<Map<String, dynamic>> detail() async {
    final files = await _load();
    final result = json.decode(
      utf8.decode(files['units/custom/crystal_fina_2/detail.json']!),
    ) as Map<String, dynamic>;
    final preset = await profile();
    result['name'] = preset['en'];
    result['jpname'] = preset['jp'];
    result['ffrStats'] = preset['stats'];
    return result;
  }

  Future<void> ensureUnitAssets(AppPaths paths) async {
    final files = await _load();
    final stateFile = _file(paths.root, 'bundled/crystal-fina-assets.json');
    final previous = stateFile.existsSync()
        ? json.decode(await stateFile.readAsString()) as Map
        : <String, dynamic>{};
    final installed = Map<String, dynamic>.from(previous);
    for (final entry in files.entries.where(
      (e) => e.key.startsWith('units/'),
    )) {
      final file = _file(paths.engineDir, entry.key);
      final hash = sha256.convert(entry.value).toString();
      if (file.existsSync()) {
        final current = sha256.convert(await file.readAsBytes()).toString();
        if (current != hash && current != previous[entry.key]) {
          continue;
        } // Preserve imported/user-edited artwork.
      }
      await _write(file, entry.value);
      installed[entry.key] = hash;
    }
    await _write(
      stateFile,
      Uint8List.fromList(utf8.encode(json.encode(installed))),
    );
  }

  Future<void> prepareEngine(
    AppPaths paths, {
    required bool engineRunning,
  }) async {
    if (engineRunning) {
      throw StateError(
        'Close the running engine before installing Crystal Fina support.',
      );
    }
    try {
      final nativeStaged = await _stageExistingVisions(paths);
      // Remove our outer hooks so Crystal Fina can validate its owned builder.
      await _runExistingVisions(paths, nativeStaged, 'Restore');
      final files = await _load();
      final fingerprint = sha256
          .convert(
            utf8.encode(
              files.entries
                  .map((e) => '${e.key}:${sha256.convert(e.value)}')
                  .join('\n'),
            ),
          )
          .toString();
      // The frozen Windows engine can encounter MAX_PATH when the material's
      // nested Unreal path follows a full hash. Keep directory names compact;
      // every payload file still uses its complete SHA-256 for verification.
      final staged = p.join(
        paths.root,
        'bundled',
        'cf-${fingerprint.substring(0, 16)}',
      );
      for (final entry in files.entries.where(
        (e) => e.key.startsWith('engine/'),
      )) {
        await _write(_file(staged, entry.key), entry.value);
      }
      await ensureUnitAssets(paths);
      final result = await _runProcess(paths.engineExe, [
        '--run',
        p.join(staged, 'engine', 'install_crystalfina.py'),
        '--engine',
        paths.engineDir,
        '--action',
        'Apply',
      ], paths.engineDir);
      if (result.exitCode != 0) {
        throw StateError(result.stderr.toString().trim());
      }
      final status = json.decode(result.stdout.toString()) as Map;
      if (status['status'] != 'active' || status['patchVersion'] != '1.1.1') {
        throw StateError(
          'The engine did not confirm the Crystal Fina extension.',
        );
      }
      await _runExistingVisions(paths, nativeStaged, 'Apply');
    } catch (error) {
      throw StateError('Studio engine setup failed: $error');
    }
  }

  Future<String> _stageExistingVisions(AppPaths paths) async {
    const root = 'assets/existing_visions';
    final manifest = json.decode(
      utf8.decode(await _readAsset('$root/manifest.json')),
    ) as Map;
    if (manifest['schema'] != 1) {
      throw StateError('Unsupported existing vision extension.');
    }
    if ((manifest['files'] as Map).keys.toSet().difference({
          'install_existing_visions.py',
          'payload/manifest.json',
          'payload/_ffr_existingvisions.py',
          'payload/_ffr_party.py',
          'payload/_ffr_testing.py',
          'payload/_ffr_crystal_cave.py',
          'payload/_ffr_ability_modes.py',
          'payload/ability_hiding_review.json',
          'payload/_ffr_animation_repair.py',
          'payload/_ffr_build_sprites.py',
          'payload/_ffr_library.py',
          'payload/ffbe_animation_index.json',
          'payload/ffbe_barrage_index.json',
        }).isNotEmpty ||
        (manifest['files'] as Map).length != 13) {
      throw StateError('Existing vision extension is incomplete.');
    }
    final files = <String, Uint8List>{};
    for (final entry in (manifest['files'] as Map).entries) {
      final relative = entry.key as String;
      _safeRelative(relative);
      final data = await _readAsset('$root/$relative');
      if (sha256.convert(data).toString() != entry.value) {
        throw StateError(
          'Existing vision extension checksum mismatch: $relative',
        );
      }
      files[relative] = data;
    }
    final fingerprint = sha256
        .convert(utf8.encode(json.encode(manifest)))
        .toString();
    final staged = p.join(
      paths.root,
      'bundled',
      'ev-${fingerprint.substring(0, 16)}',
    );
    for (final entry in files.entries) {
      await _write(_file(staged, entry.key), entry.value);
    }
    return staged;
  }

  Future<void> _runExistingVisions(
    AppPaths paths,
    String staged,
    String action,
  ) async {
    final result = await _runProcess(paths.engineExe, [
      '--run',
      p.join(staged, 'install_existing_visions.py'),
      '--engine',
      paths.engineDir,
      '--action',
      action,
    ], paths.engineDir);
    if (result.exitCode != 0) {
      throw StateError(result.stderr.toString().trim());
    }
    final status = json.decode(result.stdout.toString()) as Map;
    if (status['patchVersion'] != '1.2.1' ||
        status['status'] != (action == 'Apply' ? 'active' : 'restored')) {
      throw StateError('The engine did not confirm existing vision support.');
    }
  }
}
