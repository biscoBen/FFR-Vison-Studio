import 'dart:io';
import 'dart:math';

import 'package:ffr_vision_studio/services/acquisition.dart';
import 'package:ffr_vision_studio/services/acquisition_locations.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';

import 'character_config_test.dart' show profile, ConfigApi, clone;

class CaveRemovalApi extends ConfigApi {
  CaveRemovalApi(super.roster);
  final crystalSettings = <bool>[];
  @override
  Future<void> saveCrystalCave(bool value) async => crystalSettings.add(value);
}

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

  test('placement edits persist precise transforms for every assigned vision without changing identities', () async {
    final dir = Directory.systemTemp.createTempSync('cave-edit-');
    final api = CaveRemovalApi([]);
    final app = AppState(
      hostBase: 'http://unused',
      appPaths: AppPaths.at(dir.path),
    )..api = api;
    addTearDown(() {
      app.dispose();
      dir.deleteSync(recursive: true);
    });
    const old = CaveLocation(
      id: 'cave_edit',
      name: 'Corner',
      entrance: 'shrine',
      worldX: 17600,
      worldY: 21400,
    );
    await app.acquisitionLocations.add(old);
    final choice = app.acquisitionLocations.choose(
      const Acquisition(
        location: 'mitra_shop',
        random: false,
        hideSpoilers: false,
      ),
      old.site,
    );
    app.units = [
      {...profile(), 'key': 'one', Acquisition.field: choice.toJson()},
      {
        ...profile(),
        'key': 'two',
        Acquisition.field: choice
            .copyWith(random: true, hideSpoilers: true)
            .toJson(),
      },
      {
        ...profile(),
        'key': 'shop',
        Acquisition.field: const Acquisition(location: 'mitra_shop').toJson(),
      },
    ];
    api.roster = clone(app.units) as List;
    app.update({
      ...app.units.first as Map<String, dynamic>,
      'en': 'Pending name',
    });
    const edited = CaveLocation(
      id: 'cave_edit',
      name: 'Tucked by trees',
      entrance: 'shrine',
      worldX: 17500.25,
      worldY: 21300.75,
      worldZ: 20.5,
      yaw: -45,
      scale: .75,
    );
    await app.updateAcquisitionCave(edited);
    expect(app.units.first['en'], 'Pending name');
    for (var i = 0; i < 2; i++) {
      final saved = Acquisition.fromJson(
        api.roster[i][Acquisition.field] as Map,
      );
      expect(saved.location, old.id);
      expect(saved.cave, edited.toJson());
      expect(saved.random, i == 1);
      expect(saved.hideSpoilers, i == 1);
      expect(
        CharacterConfig.decode(
          CharacterConfig.encode(api.roster[i] as Map<String, dynamic>),
        )[Acquisition.field],
        saved.toJson(),
      );
    }
    expect(
      api.roster.last[Acquisition.field],
      const Acquisition(location: 'mitra_shop').toJson(),
    );
    final pool = AcquisitionLocations(
      file: File('${dir.path}/acquisition-caves.json'),
    );
    addTearDown(pool.dispose);
    expect(pool.cave(old.id)!.toJson(), edited.toJson());
    app.buildState = {'running': true};
    await expectLater(app.updateAcquisitionCave(old), throwsStateError);
    expect(pool.cave(old.id)!.toJson(), edited.toJson());
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

  test('removal persists, clears every assigned vision and preserves other edits and placements', () async {
    final dir = Directory.systemTemp.createTempSync('cave-remove-');
    final poolFile = File('${dir.path}/acquisition-caves.json');
    final catalog = AcquisitionCatalog.cached!;
    final api = CaveRemovalApi([]);
    final app = AppState(
      hostBase: 'http://unused',
      appPaths: AppPaths.at(dir.path),
    )..api = api;
    addTearDown(() {
      app.dispose();
      dir.deleteSync(recursive: true);
    });
    const cave = CaveLocation(
      id: 'cave_remove',
      name: 'Remove me',
      entrance: 'shrine',
      worldX: 17000,
      worldY: 21000,
    );
    await app.acquisitionLocations.add(cave);
    final choice = app.acquisitionLocations.choose(
      const Acquisition(
        location: 'mitra_shop',
        random: false,
        hideSpoilers: false,
      ),
      cave.site,
    );
    final first = {
      ...profile(),
      'key': 'first',
      Acquisition.field: choice.toJson(),
    };
    final second = {
      ...profile(),
      'key': 'second',
      Acquisition.field: choice
          .copyWith(random: true, hideSpoilers: true)
          .toJson(),
    };
    final other = {
      ...profile(),
      'key': 'other',
      Acquisition.field: app.acquisitionLocations
          .choose(choice, CaveLocation.original.site)
          .toJson(),
    };
    app.units = [first, second, other];
    api.roster = clone(app.units) as List;
    app.update({...first, 'en': 'An unsaved name edit'});
    await app.removeAcquisitionCave(cave.id);
    expect(app.dirty, isFalse);
    expect(app.units.first['en'], 'An unsaved name edit');
    for (var i = 0; i < 2; i++) {
      final saved = Acquisition.fromJson(
        api.roster[i][Acquisition.field] as Map,
      );
      expect(saved.location, catalog.mitraShop);
      expect(saved.cave, isNull);
      expect(saved.random, i == 1);
      expect(saved.hideSpoilers, i == 1);
      expect(api.roster[i]['stats'], first['stats']);
    }
    expect(api.roster.last, other);
    expect(api.crystalSettings, isEmpty);
    final restored = AcquisitionLocations(file: poolFile);
    addTearDown(restored.dispose);
    expect(restored.cave(cave.id), isNull);
    expect(restored.caves.single.id, 'crystal_cave');
    expect(restored.sites(catalog).any((s) => s.id == cave.id), isFalse);
  });

  test('removing the original cave disables its legacy switch and old choices safely migrate to the shop', () async {
    final dir = Directory.systemTemp.createTempSync('original-cave-remove-');
    final unit = {
      ...profile(),
      Acquisition.field: const Acquisition(location: 'earth_shrine').toJson(),
    };
    final api = CaveRemovalApi([unit]);
    final app =
        AppState(hostBase: 'http://unused', appPaths: AppPaths.at(dir.path))
          ..api = api
          ..units = [unit]
          ..crystalCave = true;
    addTearDown(() {
      app.dispose();
      dir.deleteSync(recursive: true);
    });
    await app.removeAcquisitionCave('crystal_cave');
    expect(api.crystalSettings, [false]);
    expect(app.crystalCave, isFalse);
    expect(app.acquisitionLocations.caves, isEmpty);
    expect(api.roster.single[Acquisition.field]['cave'], isNull);
    final catalog = AcquisitionCatalog.cached!;
    for (final old in ['earth_shrine', 'crystal_cave']) {
      expect(
        app.acquisitionLocations
            .migrate(Acquisition(location: old), catalog)
            .location,
        catalog.mitraShop,
      );
    }
    final restored = AcquisitionLocations(file: app.acquisitionLocations.file);
    addTearDown(restored.dispose);
    expect(restored.caves, isEmpty);
  });

  test('a blocked or failed removal preserves the saved pool and vision assignments', () async {
    final dir = Directory.systemTemp.createTempSync('failed-cave-remove-');
    final unit = {
      ...profile(),
      Acquisition.field: Acquisition(
        location: 'crystal_cave',
        cave: CaveLocation.original.toJson(),
      ).toJson(),
    };
    final api = CaveRemovalApi([unit]);
    final app =
        AppState(hostBase: 'http://unused', appPaths: AppPaths.at(dir.path))
          ..api = api
          ..units = [unit];
    addTearDown(() {
      app.dispose();
      dir.deleteSync(recursive: true);
    });
    final before = clone(app.units);
    app.buildState = {'running': true};
    await expectLater(
      app.removeAcquisitionCave('crystal_cave'),
      throwsStateError,
    );
    app.buildState = null;
    Directory('${app.acquisitionLocations.file!.path}.pending').createSync();
    await expectLater(
      app.removeAcquisitionCave('crystal_cave'),
      throwsA(isA<FileSystemException>()),
    );
    expect(app.acquisitionLocations.caves.single.id, 'crystal_cave');
    expect(app.units, before);
    expect(api.roster, before);
    expect(api.saves, 0);
    await app.removeAcquisitionCave('cave_missing');
    expect(api.saves, 0);
  });
}
