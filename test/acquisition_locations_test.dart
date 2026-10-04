import 'dart:io';
import 'dart:math';

import 'package:ffr_vision_studio/services/acquisition.dart';
import 'package:ffr_vision_studio/services/acquisition_locations.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:flutter_test/flutter_test.dart';

import 'character_config_test.dart' show profile;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    await AcquisitionCatalog.bundled;
  });

  test('all native inventory and combined records are selectable without duplicate IDs', () {
    final catalog = AcquisitionCatalog.cached!;
    expect(catalog.vendors, hasLength(125));
    expect(catalog.vendors.map((v) => v.id).toSet(), hasLength(125));
    expect(catalog.vendor('shop_1')!.label, contains('Mitra'));
    expect(catalog.vendor('shop_10001')!.label, contains('Grandshelt'));
    expect(catalog.entrances.map((e) => e.id), [
      'rock_cave',
      'shrine',
      'dwarven_cave',
      'desert_sinkhole',
    ]);
  });

  test('the shared pool starts with our cave; thirty caves persist without choosing locations for the user', () async {
    final dir = Directory.systemTemp.createTempSync('cave-pool-');
    addTearDown(() => dir.deleteSync(recursive: true));
    final file = File('${dir.path}/caves.json');
    final pool = AcquisitionLocations(file: file);
    addTearDown(pool.dispose);
    expect(pool.caves.single.id, 'crystal_cave');
    expect(file.existsSync(), isFalse);
    for (var i = 2; i <= 30; i++) {
      await pool.add(
        CaveLocation(
          id: 'cave_test_$i',
          name: 'My cave $i',
          entrance: 'shrine',
          worldX: i * 100,
          worldY: i * 50,
        ),
      );
    }
    final restored = AcquisitionLocations(file: file);
    addTearDown(restored.dispose);
    expect(restored.loadError, isNull);
    expect(restored.caves, hasLength(30));
    expect(restored.caves.last.worldX, 3000);
    expect(restored.caves.last.entrance, 'shrine');
    expect(
      restored
          .sites(AcquisitionCatalog.cached!)
          .where((s) => s.kind == 'cave')
          .map((s) => s.id),
      restored.caves.map((s) => s.id),
    );
  });

  test('custom cave snapshots survive single/bulk character configs and importing into another pool', () async {
    final pool = AcquisitionLocations();
    final other = AcquisitionLocations();
    addTearDown(pool.dispose);
    addTearDown(other.dispose);
    const cave = CaveLocation(
      id: 'cave_chosen',
      name: 'My selected cave',
      entrance: 'dwarven_cave',
      worldX: -100,
      worldY: 200,
    );
    await pool.add(cave);
    final settings = pool
        .choose(
          const Acquisition(location: 'mitra_shop', random: false),
          cave.site,
        )
        .toJson();
    final unit = {...profile(), Acquisition.field: settings};
    final config = CharacterConfig.decode(CharacterConfig.encode(unit));
    final bulk = CharacterConfig.decodeAll(CharacterConfig.encodeAll([unit]));
    expect(config[Acquisition.field], settings);
    expect(bulk.single[Acquisition.field], settings);
    final restored = Acquisition.fromJson(config[Acquisition.field] as Map);
    await other.add(CaveLocation.fromJson(restored.cave!));
    expect(other.site(restored, AcquisitionCatalog.cached!)!.worldX, -100);
    expect(
      restored.copyWith(hideSpoilers: false).toJson()['cave'],
      settings['cave'],
    );
    final rerolled = other.reroll(
      restored,
      true,
      AcquisitionCatalog.cached!,
      rng: Random(4),
    );
    expect(rerolled.location, isNot(restored.location));
    expect(Acquisition.valid(rerolled.toJson()), isTrue);
  });

  test('legacy shrine choices migrate to our cave, not a native cave in the new pool', () {
    final pool = AcquisitionLocations();
    addTearDown(pool.dispose);
    final migrated = pool.migrate(
      const Acquisition(
        location: 'earth_shrine',
        random: false,
        hideSpoilers: false,
      ),
      AcquisitionCatalog.cached!,
    );
    expect(migrated.location, 'crystal_cave');
    expect(migrated.random, isFalse);
    expect(migrated.hideSpoilers, isFalse);
    expect(migrated.cave!['entrance'], 'rock_cave');
    expect(pool.caves, hasLength(1));
  });

  test('invalid positions, conflicting IDs and failed writes preserve the existing pool', () async {
    final dir = Directory.systemTemp.createTempSync('cave-invalid-');
    addTearDown(() => dir.deleteSync(recursive: true));
    final file = File('${dir.path}/caves.json');
    final pool = AcquisitionLocations(file: file);
    addTearDown(pool.dispose);
    const cave = CaveLocation(
      id: 'cave_test',
      name: 'First',
      entrance: 'rock_cave',
      worldX: 0,
      worldY: 0,
    );
    await pool.add(cave);
    final before = file.readAsStringSync();
    await pool.add(cave);
    await expectLater(
      pool.add(
        const CaveLocation(
          id: 'cave_test',
          name: 'Overwrite',
          entrance: 'shrine',
          worldX: 1,
          worldY: 0,
        ),
      ),
      throwsStateError,
    );
    for (final x in [double.nan, double.infinity, -24501.0, 25301.0]) {
      await expectLater(
        pool.add(
          CaveLocation(
            id: 'cave_invalid',
            name: 'Bad',
            entrance: 'shrine',
            worldX: x,
            worldY: 0,
          ),
        ),
        throwsFormatException,
      );
    }
    expect(file.readAsStringSync(), before);
    expect(pool.caves, hasLength(2));
    final broken = AcquisitionLocations(
      file: File('${dir.path}/missing/caves.json'),
    );
    addTearDown(broken.dispose);
    await expectLater(broken.add(cave), throwsA(isA<FileSystemException>()));
    expect(broken.caves, hasLength(1));
    file.writeAsStringSync('{broken');
    final corrupt = AcquisitionLocations(file: file);
    addTearDown(corrupt.dispose);
    expect(corrupt.loadError, isNotNull);
    await expectLater(corrupt.add(cave), throwsStateError);
    expect(file.readAsStringSync(), '{broken');
  });
}
