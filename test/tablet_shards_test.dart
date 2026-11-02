import 'dart:io';
import 'dart:typed_data';

import 'package:ffr_vision_studio/services/tablet_shards.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late List<TabletShard> shards;
  setUpAll(() async {
    shards = await TabletShard.bundled();
  });
  TabletShard shard(int number) =>
      shards.singleWhere((s) => s.number == number);
  Uint8List fixture(String name) =>
      File('test/fixtures/tablet_shards/$name.sav').readAsBytesSync();

  test('all 99 unique native identities retain explicit guide order', () {
    expect(
      shards.map((s) => s.number),
      orderedEquals(List.generate(99, (i) => i + 1)),
    );
    expect(shards.map((s) => (s.mapId, s.uniqueId)).toSet(), hasLength(99));
    for (final s in shards) {
      expect(s.chapter, inInclusiveRange(1, 8));
      expect(s.hint, isNotEmpty);
      expect(s.location, isNotEmpty);
    }
    for (final expected in [
      (3, 2040, 9),
      (4, 2040, 8),
      (40, 3110, 59),
      (41, 3110, 60),
      (42, 3110, 58),
      (54, 3150, 3),
      (55, 3150, 2),
      (68, 3210, 26),
      (69, 3211, 3),
      (70, 3212, 4),
      (75, 3211, 4),
      (78, 3220, 36),
      (79, 3220, 35),
      (92, 3271, 2),
      (93, 3271, 1),
    ]) {
      expect(
        (shard(expected.$1).mapId, shard(expected.$1).uniqueId),
        (expected.$2, expected.$3),
      );
    }
  });

  test('independently encrypted save handles flags, wide strings and partial areas', () {
    final save = TabletSave.decode(fixture('partial'));
    expect(save.playSeconds, 12345);
    expect(save.savedTicks, 638976312000000000);
    expect(
      shards
          .where((s) => save.status(s) == TabletShardStatus.collected)
          .map((s) => s.number),
      [3, 9, 48, 51, 69],
    );
    expect(
      save.status(shard(1)),
      TabletShardStatus.missing,
      reason: 'An empty treasure list still marks a map visited',
    );
    expect(
      save.status(shard(4)),
      TabletShardStatus.missing,
      reason: 'Felicitas guide order is not actor order',
    );
    expect(
      save.status(shard(49)),
      TabletShardStatus.missing,
      reason: 'Closed and unrelated item records do not count',
    );
    expect(save.status(shard(68)), TabletShardStatus.unvisited);
    expect(save.status(shard(70)), TabletShardStatus.unvisited);
    expect(save.status(shard(75)), TabletShardStatus.missing);
    expect(
      save
          .visible(shards)
          .where((s) => s.location == "Fina's Psyche")
          .map((s) => s.number),
      [75],
    );
    expect(
      save
          .visible(shards, showUnvisited: true)
          .where((s) => s.location == "Fina's Psyche")
          .map((s) => s.number),
      [68, 70, 75],
    );
  });

  test(
    'single actor states never grant other actors or same IDs on other maps',
    () {
      for (final s in shards) {
        final save = TabletSave({
          for (final map in shards.map((s) => s.mapId)) map: {},
          s.mapId: {s.uniqueId},
        });
        expect(
          shards.where((s) => save.status(s) == TabletShardStatus.collected),
          [s],
        );
        expect(save.visible(shards), hasLength(98));
      }
    },
  );

  test('complete and unvisited saves remain distinct under all filters', () {
    final collected = <int, Set<int>>{};
    for (final s in shards) {
      collected.putIfAbsent(s.mapId, () => {}).add(s.uniqueId);
    }
    final full = TabletSave(collected), empty = TabletSave({});
    expect(full.visible(shards), isEmpty);
    expect(full.visible(shards, onlyMissing: false), hasLength(99));
    expect(empty.visible(shards), isEmpty);
    expect(empty.visible(shards, showUnvisited: true), hasLength(99));
    expect(
      empty
          .visible(shards, showUnvisited: true, chapter: 4)
          .map((s) => s.number),
      orderedEquals(List.generate(16, (i) => 43 + i)),
    );
  });

  test('invalid, truncated and unsupported saves fail instead of showing zero collected', () {
    for (final name in ['missing-map', 'unsupported-version', 'invalid-size']) {
      expect(
        () => TabletSave.decode(fixture(name)),
        throwsA(isA<TabletSaveException>()),
        reason: name,
      );
    }
    final bytes = fixture('partial');
    for (final n in [0, 3, 32, 48, 100, bytes.length ~/ 2]) {
      expect(
        () => TabletSave.decode(Uint8List.sublistView(bytes, 0, n)),
        throwsA(isA<TabletSaveException>()),
      );
    }
    final corrupt = Uint8List.fromList(bytes)..[32] ^= 255;
    expect(
      () => TabletSave.decode(corrupt),
      throwsA(isA<TabletSaveException>()),
    );
  });

  test('discover current PC Steam accounts and legacy slots, select newest, and read without writes', () async {
    final root = Directory.systemTemp.createTempSync('tablet-shards-');
    addTearDown(() => root.deleteSync(recursive: true));
    final paths = [
      p.join(
        root.path,
        'FFRS',
        'Steam',
        '76561198000000001',
        'GameSaveData0.sav',
      ),
      p.join(
        root.path,
        'FFRS',
        'Steam',
        '76561198000000002',
        'GameSaveData1.sav',
      ),
      p.join(root.path, 'FFRS', 'Saved', 'SaveGames', 'GameSaveData2.sav'),
    ];
    for (var i = 0; i < paths.length; i++) {
      final file = File(paths[i]);
      file.parent.createSync(recursive: true);
      file.writeAsBytesSync(fixture('partial'));
      file.setLastModifiedSync(DateTime(2026, 11, 2, 12, i));
    }
    File(p.join(File(paths[0]).parent.path, 'SystemSaveData.sav'))
        .writeAsBytesSync([1, 2, 3]);
    final files = await findTabletSaves(
      environment: {'LOCALAPPDATA': root.path},
      gameRoot: root.path,
    );
    expect(files.map((f) => f.path), paths.reversed);
    final original = File(paths.first).readAsBytesSync();
    final save = await readTabletSave(paths.first);
    expect(save.status(shard(9)), TabletShardStatus.collected);
    expect(File(paths.first).readAsBytesSync(), original);
    expect(await findTabletSaves(environment: {}), isEmpty);
  });
}
