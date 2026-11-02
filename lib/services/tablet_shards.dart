// Save layout and shard identities adapted from heydavee/ffr-shard-finder (MIT).
// Copyright (c) 2026 heydavee. See assets/tablet_shards/LICENSE.txt.
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:pointycastle/api.dart';
import 'package:pointycastle/block/aes.dart';

class TabletShard {
  const TabletShard({
    required this.number,
    required this.chapter,
    required this.mapId,
    required this.uniqueId,
    required this.location,
    required this.hint,
  });
  final int number, chapter, mapId, uniqueId;
  final String location, hint;
  static Future<List<TabletShard>>? _bundled;
  static Future<List<TabletShard>> bundled() => _bundled ??= _load();
  static Future<List<TabletShard>> _load() async {
    final data = jsonDecode(
      await rootBundle.loadString('assets/tablet_shards/shards.json'),
    ) as Map;
    return [
      for (final s in data['shards'] as List)
        TabletShard(
          number: s['number'] as int,
          chapter: s['chapter'] as int,
          mapId: s['mapId'] as int,
          uniqueId: s['uniqueId'] as int,
          location: s['location'] as String,
          hint: s['hint'] as String,
        ),
    ];
  }
}

enum TabletShardStatus { collected, missing, unvisited }

class TabletSaveException implements Exception {
  const TabletSaveException(this.message);
  final String message;
  @override
  String toString() => message;
}

class TabletSave {
  TabletSave(this.collected, {this.playSeconds = 0, this.savedTicks = 0});
  final Map<int, Set<int>> collected;
  final double playSeconds;
  final int savedTicks;

  TabletShardStatus status(TabletShard shard) =>
      !collected.containsKey(shard.mapId)
      ? TabletShardStatus.unvisited
      : collected[shard.mapId]!.contains(shard.uniqueId)
      ? TabletShardStatus.collected
      : TabletShardStatus.missing;

  List<TabletShard> visible(
    List<TabletShard> shards, {
    bool onlyMissing = true,
    bool showUnvisited = false,
    int? chapter,
  }) => shards
      .where(
        (s) =>
            (chapter == null || chapter == s.chapter) &&
            (showUnvisited || status(s) != TabletShardStatus.unvisited) &&
            (!onlyMissing || status(s) != TabletShardStatus.collected),
      )
      .toList();

  static TabletSave decode(Uint8List bytes) {
    if (bytes.length < 48 ||
        bytes.length > maxTabletSaveBytes ||
        ascii.decode(bytes.sublist(0, 4), allowInvalid: true) != 'SVHD') {
      throw const TabletSaveException(
        'Choose a Resonance Steam GameSaveData*.sav file.',
      );
    }
    try {
      final size = (bytes.length - 32) ~/ 16 * 16;
      final plain = Uint8List(size);
      final aes = AESEngine()
        ..init(
          false,
          KeyParameter(
            Uint8List.fromList(utf8.encode('wwrqPkdwzPvgfchQ8kTYHVbn4umTf3d7')),
          ),
        );
      for (var i = 0; i < size; i += 16) {
        aes.processBlock(bytes, 32 + i, plain, i);
      }
      final r = _SaveReader(plain);
      if (ascii.decode(r.take(4), allowInvalid: true) != 'GVAS' ||
          r.i32() != 3) {
        throw const FormatException('Unsupported save header');
      }
      r.skip(8 + 6 + 4); // Package versions, engine version and changelist.
      r.string(); // Engine branch.
      r.i32(); // Custom-version format.
      r.skip(r.count() * 20);
      r.string(); // Save-game class.
      r.u8();
      final props = r.properties(0, only: {'Map', 'Player'});
      final map = props['Map'];
      if (map is! Map || map['mapGimmick'] is! Map) {
        throw const FormatException('Missing map progress');
      }
      final collected = <int, Set<int>>{};
      for (final entry in (map['mapGimmick'] as Map).entries) {
        if (entry.key is! int || entry.value is! Map) {
          throw const FormatException('Invalid map progress');
        }
        final found = <int>{};
        final box = (entry.value as Map)['treasureBox'];
        if (box != null && box is! Map) {
          throw const FormatException('Invalid treasure progress');
        }
        final records = box is Map ? box['treasureBoxList'] : null;
        if (records != null && records is! List) {
          throw const FormatException('Invalid treasure records');
        }
        for (final record in records is List ? records : const []) {
          if (record is! Map) {
            throw const FormatException('Invalid treasure record');
          }
          if (record['ID'] == -1 &&
              record['IsOpen'] == true &&
              record['UniqueID'] is int) {
            found.add(record['UniqueID'] as int);
          }
        }
        collected[entry.key as int] = found;
      }
      final player = props['Player'];
      return TabletSave(
        collected,
        playSeconds: player is Map && player['PlayTime'] is num
            ? (player['PlayTime'] as num).toDouble()
            : 0,
        savedTicks: player is Map && player['SavedDateTime'] is int
            ? player['SavedDateTime'] as int
            : 0,
      );
    } on FormatException {
      throw const TabletSaveException(
        'This save is incomplete or uses an unsupported format. Save in-game and refresh, or choose another slot.',
      );
    }
  }
}

const maxTabletSaveBytes = 64 * 1024 * 1024;

class TabletSaveFile {
  const TabletSaveFile(this.path, this.modified);
  final String path;
  final DateTime modified;
  String get name => p.basename(path);
  String get folder => p.basename(p.dirname(path));
}

/// Search this PC's actual save folders, never the cloud task's or another PC's paths.
Future<List<TabletSaveFile>> findTabletSaves({
  String? gameRoot,
  Map<String, String>? environment,
}) async {
  final env = environment ?? Platform.environment;
  final roots = <String>[];
  final local = env['LOCALAPPDATA'];
  if (local != null && local.isNotEmpty) {
    final steam = Directory(p.join(local, 'FFRS', 'Steam'));
    roots.add(steam.path);
    try {
      if (await steam.exists()) {
        await for (final entry in steam.list(followLinks: false)) {
          if (entry is Directory) {
            roots.add(entry.path);
          }
        }
      }
    } on FileSystemException {
      /* Other roots and manual selection remain available. */
    }
    roots.add(p.join(local, 'FFRS', 'Saved', 'SaveGames'));
  }
  if (gameRoot != null) {
    roots.add(p.join(gameRoot, 'FFRS', 'Saved', 'SaveGames'));
  }
  final files = <String, TabletSaveFile>{};
  for (final root in roots.toSet()) {
    try {
      final directory = Directory(root);
      if (!await directory.exists()) {
        continue;
      }
      await for (final entry in directory.list(followLinks: false)) {
        if (entry is File &&
            RegExp(
              r'^GameSaveData\d+\.sav$',
              caseSensitive: false,
            ).hasMatch(p.basename(entry.path))) {
          final stat = await entry.stat();
          files[p.normalize(p.absolute(entry.path))] = TabletSaveFile(
            entry.path,
            stat.modified,
          );
        }
      }
    } on FileSystemException {
      /* A locked folder must not hide another account's slots. */
    }
  }
  return files.values.toList()
    ..sort((a, b) => b.modified.compareTo(a.modified));
}

Future<TabletSave> readTabletSave(String path) async {
  final file = await File(path).open(mode: FileMode.read);
  late final Uint8List bytes;
  try {
    final size = await file.length();
    if (size > maxTabletSaveBytes) {
      throw const TabletSaveException(
        'This file is too large to be a supported Resonance save.',
      );
    }
    bytes = await file.read(size);
    if (bytes.length != size) {
      throw const TabletSaveException(
        'The save changed while it was being read. Try Refresh again.',
      );
    }
  } finally {
    await file.close();
  }
  return Isolate.run(() => TabletSave.decode(bytes));
}

class _SaveType {
  const _SaveType(this.name, this.args);
  final String name;
  final List<_SaveType> args;
}

/// UE5 complete property tags. Every nested read is bounded by its owning tag.
class _SaveReader {
  _SaveReader(this.bytes)
    : data = ByteData.sublistView(bytes),
      limit = bytes.length;
  final Uint8List bytes;
  final ByteData data;
  int offset = 0, limit, nodes = 0;
  Never invalid() => throw const FormatException('Invalid save property');
  void require(int n) {
    if (n < 0 || offset + n > limit) {
      invalid();
    }
  }

  void skip(int n) {
    require(n);
    offset += n;
  }

  Uint8List take(int n) {
    require(n);
    final s = Uint8List.sublistView(bytes, offset, offset + n);
    offset += n;
    return s;
  }

  int u8() {
    require(1);
    return bytes[offset++];
  }

  int i32() {
    require(4);
    final n = data.getInt32(offset, Endian.little);
    offset += 4;
    return n;
  }

  int count() {
    final n = i32();
    if (n < 0 || n > 1000000) {
      invalid();
    }
    return n;
  }

  String string() {
    final n = i32();
    if (n == 0) {
      return '';
    }
    if (n.abs() > 1000000) {
      invalid();
    }
    if (n < 0) {
      final raw = take(-n * 2), view = ByteData.sublistView(raw);
      if (view.getUint16(raw.length - 2, Endian.little) != 0) {
        invalid();
      }
      return String.fromCharCodes([
        for (var i = 0; i < raw.length - 2; i += 2)
          view.getUint16(i, Endian.little),
      ]);
    }
    final raw = take(n);
    if (raw.last != 0) {
      invalid();
    }
    return latin1.decode(raw.sublist(0, raw.length - 1));
  }

  _SaveType type(int depth) {
    if (depth > 64) {
      invalid();
    }
    final name = string(), n = count();
    if (n > 16) {
      invalid();
    }
    return _SaveType(name, [for (var i = 0; i < n; i++) type(depth + 1)]);
  }

  Map<String, dynamic> properties(int depth, {Set<String>? only}) {
    if (depth > 64) {
      invalid();
    }
    final out = <String, dynamic>{};
    for (;;) {
      if (++nodes > 1000000) {
        invalid();
      }
      final name = string();
      if (name.isEmpty || name == 'None') {
        return out;
      }
      final ty = type(0), size = i32(), flags = u8();
      if (flags & 1 != 0) {
        skip(4);
      }
      if (flags & 2 != 0) {
        skip(16);
      }
      if (flags & 4 != 0 && u8() & 2 != 0) {
        skip(17);
      }
      require(size);
      final end = offset + size, parentLimit = limit;
      limit = end;
      if (only == null || only.contains(name)) {
        try {
          out[name] = ty.name == 'BoolProperty'
              ? flags & 0x10 != 0
              : value(
                  ty,
                  depth + 1,
                  only: depth == 0
                      ? name == 'Map'
                            ? {'mapGimmick'}
                            : {'PlayTime', 'SavedDateTime'}
                      : null,
                );
        } on UnsupportedError {
          out[name] = null; // Unknown unrelated fields are skippable by their complete tag size.
        }
      }
      offset = end;
      limit = parentLimit;
    }
  }

  dynamic value(_SaveType ty, int depth, {Set<String>? only}) {
    if (depth > 64 || ++nodes > 1000000) {
      invalid();
    }
    switch (ty.name) {
      case 'BoolProperty':
        return u8() != 0;
      case 'IntProperty':
        return i32();
      case 'UInt32Property':
        require(4);
        final v = data.getUint32(offset, Endian.little);
        offset += 4;
        return v;
      case 'Int64Property':
      case 'UInt64Property':
        require(8);
        final v = ty.name == 'Int64Property'
            ? data.getInt64(offset, Endian.little)
            : data.getUint64(offset, Endian.little);
        offset += 8;
        return v;
      case 'Int16Property':
      case 'UInt16Property':
        require(2);
        final v = ty.name == 'Int16Property'
            ? data.getInt16(offset, Endian.little)
            : data.getUint16(offset, Endian.little);
        offset += 2;
        return v;
      case 'Int8Property':
        require(1);
        final v = data.getInt8(offset);
        offset++;
        return v;
      case 'FloatProperty':
      case 'DoubleProperty':
        final size = ty.name == 'FloatProperty' ? 4 : 8;
        require(size);
        final v = size == 4
            ? data.getFloat32(offset, Endian.little)
            : data.getFloat64(offset, Endian.little);
        offset += size;
        return v;
      case 'StrProperty':
      case 'NameProperty':
      case 'EnumProperty':
      case 'SoftObjectProperty':
      case 'ObjectProperty':
        return string();
      case 'ByteProperty':
        return ty.args.isEmpty ? u8() : string();
      case 'StructProperty':
        if (ty.args.isEmpty) {
          invalid();
        }
        final name = ty.args.first.name;
        if (name == 'DateTime') {
          require(8);
          final v = data.getInt64(offset, Endian.little);
          offset += 8;
          return v;
        }
        const nativeSizes = {
          'Timespan': 8,
          'Vector': 24,
          'Rotator': 24,
          'Vector2D': 16,
          'Quat': 32,
          'LinearColor': 16,
          'Color': 4,
          'IntPoint': 8,
          'IntVector': 12,
          'Guid': 16,
        };
        if (nativeSizes.containsKey(name)) {
          skip(nativeSizes[name]!);
          return null;
        }
        return properties(depth, only: only);
      case 'ArrayProperty':
      case 'SetProperty':
        if (ty.args.length != 1) {
          invalid();
        }
        if (ty.name == 'SetProperty') {
          i32();
        }
        final n = count();
        if (n > limit - offset) {
          invalid();
        }
        if (ty.args.first.name == 'ByteProperty' &&
            ty.args.first.args.isEmpty) {
          skip(n);
          return null;
        }
        return [for (var i = 0; i < n; i++) value(ty.args.first, depth + 1)];
      case 'MapProperty':
        if (ty.args.length != 2) {
          invalid();
        }
        i32();
        final n = count();
        if (n > limit - offset) {
          invalid();
        }
        final result = <dynamic, dynamic>{};
        for (var i = 0; i < n; i++) {
          final key = value(ty.args[0], depth + 1);
          result[key] = value(ty.args[1], depth + 1);
        }
        return result;
      default:
        throw UnsupportedError(ty.name);
    }
  }
}
