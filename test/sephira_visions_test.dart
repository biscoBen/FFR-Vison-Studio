import 'dart:io';

import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';

import 'character_config_test.dart' show ConfigApi, profile, clone;

Map<String, dynamic> preset(String name, String form) {
  var unit = profile()..remove('bundledPreset');
  unit['key'] = 'sephira_$name';
  unit['en'] = name;
  unit['jp'] = name;
  unit['ffbe'] = {'id': form, 'base': '10', 'source': 'JP', 'dir': 'units/ffbe/sephira_$name/sprites/$form'};
  if (name == 'christine') unit = CharacterConfig.restore(unit, [profile()]);
  return {'id': name, 'name': name, 'theme': 'Test', 'profile': unit};
}

class CatalogConfigApi extends ConfigApi {
  CatalogConfigApi(super.roster, this.hostUnits);
  final List<Map<String, dynamic>> hostUnits;

  @override
  Future<Map<String, dynamic>> prepareAssets(String ffbeId, String form) {
    final allowed = hostUnits.any((unit) => unit['id'] == ffbeId &&
        (unit['packs'] as List).contains(form));
    if (!allowed) throw StateError('This look is not available for the selected unit.');
    return super.prepareAssets(ffbeId, form);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory dir;
  late ConfigApi api;
  late AppState app;
  setUp(() {
    dir = Directory.systemTemp.createTempSync('sephira-presets-');
    api = ConfigApi([profile()]);
    app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(dir.path))
      ..api = api
      ..units = clone(api.roster) as List
      ..sephiraPresets = [preset('a2', '102'), preset('christine', '103')];
    api.paths = app.paths;
  });
  tearDown(() { app.dispose(); dir.deleteSync(recursive: true); });

  test('enable allocates collision-free identities and keeps unrelated units', () async {
    final original = clone(app.units.single);
    await app.setSephiraEnabled(true);
    expect(app.units.first, original);
    expect(app.sephiraUnits, hasLength(2));
    expect(app.includedUnitCount, 3);
    CharacterConfig.validateAll(app.units);
    expect(api.preparations, ['10:102', '10:103']);
    expect(api.saves, 1);
  });

  test('toggle retains edits and removed entries stay removed until restored', () async {
    await app.setSephiraEnabled(true);
    final edited = CharacterConfig.copy(app.sephiraUnits.first);
    edited['stats']['Attack'] = 47;
    app.update(edited);
    await app.setSephiraEnabled(false);
    expect(app.includedUnitCount, 1);
    expect(app.sephiraUnits.first['stats']['Attack'], 47);
    expect(SephiraVisions.included(app.sephiraUnits.first), isFalse);
    await app.removeUnit(app.sephiraUnits.last['key'] as String);
    await app.setSephiraEnabled(true);
    expect(app.sephiraUnits, hasLength(1));
    expect(app.sephiraUnits.first['stats']['Attack'], 47);
    await app.restoreSephira();
    expect(app.sephiraUnits, hasLength(2));
    expect(app.sephiraUnits.first['stats']['Attack'], 47);
    final restarted = AppState(hostBase: 'http://unused', appPaths: app.paths);
    expect(restarted.sephiraEnabled, isTrue);
    expect(restarted.sephiraInitialized, isTrue);
    restarted.dispose();
  });

  test('reset preserves identity and acquisition, backs up overwritten edits', () async {
    await app.setSephiraEnabled(true);
    final old = CharacterConfig.copy(app.sephiraUnits.first);
    final edited = CharacterConfig.copy(old);
    edited['stats']['Attack'] = 47;
    edited['studioAcquisition'] = {'version': 1, 'random': false, 'hideSpoilers': false, 'location': 'mitra_shop'};
    app.update(edited);
    await app.restoreSephira(presetId: 'a2', reset: true);
    final reset = app.sephiraUnits.first;
    expect(reset['stats'], old['stats']);
    expect(reset['id'], old['id']);
    expect(reset['master']['id'], old['master']['id']);
    expect(reset['studioAcquisition'], edited['studioAcquisition']);
    final backup = Directory(app.paths.configBackups).listSync().whereType<File>().single;
    final saved = CharacterConfig.decodeAll(backup.readAsStringSync());
    expect(saved.firstWhere((u) => u['key'] == old['key'])['stats']['Attack'], 47);
  });

  test('preparation or save failure does not partially add or enable presets', () async {
    final original = clone(app.units);
    api.failPreparation = true;
    await expectLater(app.setSephiraEnabled(true), throwsException);
    expect(api.roster, original);
    expect(app.units, original);
    expect(app.sephiraEnabled, isFalse);
    expect(app.sephiraWorking, isFalse);
    api.failPreparation = false;
    api.fail = true;
    await expectLater(app.setSephiraEnabled(true), throwsStateError);
    expect(api.roster, original);
    expect(app.units, original);
  });

  test('unfinished versions are blocked before any download or roster change', () async {
    app.sephiraPresets.first['profile'] = null;
    await expectLater(app.setSephiraEnabled(true), throwsStateError);
    expect(api.preparations, isEmpty);
    expect(api.saves, 0);
  });

  test('edits made during the toggle save survive with the requested membership', () async {
    await app.setSephiraEnabled(true);
    var changed = false;
    api.beforeSave = () async {
      if (changed) return;
      changed = true;
      final edited = CharacterConfig.copy(app.sephiraUnits.first);
      edited['stats']['Attack'] = 62;
      app.update(edited);
    };
    await app.setSephiraEnabled(false);
    expect(app.sephiraUnits.first['stats']['Attack'], 62);
    expect(SephiraVisions.included(app.sephiraUnits.first), isFalse);
    expect(api.roster, app.units);
    expect(app.dirty, isFalse);
  });

  test('after all entries are removed, toggling keeps them removed', () async {
    await app.setSephiraEnabled(true);
    final keys = app.sephiraUnits.map((u) => u['key'] as String).toList();
    for (final key in keys) { await app.removeUnit(key); }
    await app.setSephiraEnabled(false);
    await app.setSephiraEnabled(true);
    expect(app.sephiraUnits, isEmpty);
    expect(api.roster, hasLength(1));
    await app.restoreSephira();
    expect(app.sephiraUnits, hasLength(2));
  });

  test('portable configs keep membership and reject native/party tagging', () {
    final u = profile()..[SephiraVisions.field] = {'version': 1, 'preset': 'a2', 'enabled': false};
    final restored = CharacterConfig.decode(CharacterConfig.encode(u));
    expect(SephiraVisions.included(restored), isFalse);
    u['party'] = {'id': 1001, 'version': 1};
    expect(() => CharacterConfig.validate(u), throwsFormatException);
  });

  test('the complete selected catalog is portable and collision-safe', () async {
    final presets = await SephiraVisions.bundled;
    expect(presets, hasLength(31));
    expect(presets.where((p) => p['profile'] == null), isEmpty);
    final configs = presets.map((p) => CharacterConfig.copy(p['profile'] as Map<String, dynamic>)).toList();
    CharacterConfig.validateAll(configs);
    final targets = List<Map<String, dynamic>?>.filled(configs.length, null);
    // Every preferred identity already belongs to another user entry.
    final loaded = CharacterConfig.restoreAll(configs, configs, targets);
    CharacterConfig.validateAll([...configs, ...loaded]);
    final minfilia = loaded.singleWhere((u) => u['en'] == 'Minfilia');
    final dual = (minfilia['skills'] as Map).values.single;
    expect(dual['set']['mimicableUnitId'], minfilia['id']);
    expect(minfilia['id'], isNot(configs[6]['id']));
  });

  test('all selected presets prepare with separate Alice shift and base owners', () async {
    final presets = await SephiraVisions.bundled;
    final hostUnits = <Map<String, dynamic>>[];
    for (final preset in presets) {
      final ffbe = preset['profile']['ffbe'] as Map;
      if (ffbe['source'] == 'CUSTOM') continue;
      final forms = <String>[ffbe['id'] as String];
      if (ffbe['baseForm'] is String && preset['id'] != 'alice') {
        forms.add(ffbe['baseForm'] as String);
      }
      hostUnits.add({'id': ffbe['base'], 'packs': forms});
    }
    // These are two distinct rows in the hosted catalog, not one unit with
    // two looks. Both are needed to restore the selected Brave Shift config.
    hostUnits.add({'id': '336000105', 'packs': ['336000117']});
    final strict = CatalogConfigApi(clone(api.roster) as List, hostUnits)
      ..paths = app.paths;
    app.api = strict;
    app.hostIndex = {'units': hostUnits};
    app.sephiraPresets = presets;
    final original = CharacterConfig.copy(app.units.single);
    await app.setSephiraEnabled(true);
    expect(app.sephiraUnits, hasLength(31));
    expect(strict.saves, 1);
    expect(strict.preparations, containsAll([
      '336000127:336000127', '336000105:336000117',
      '215002407:215002417', '215002407:215002407',
      '304000707:304000717', '304000707:304000707',
    ]));
    expect(app.units.singleWhere((u) => u['key'] == original['key'])['stats'], original['stats']);
    final alice = app.sephiraUnits.singleWhere((u) => u['sephiraVision']['preset'] == 'alice');
    expect(alice['ffbe']['id'], '336000127');
    expect(alice['ffbe']['baseForm'], '336000117');
    CharacterConfig.validateAll(strict.roster);
  });

  test('failed preparation names the preset and preserves the roster', () async {
    api.failPreparation = true;
    final original = clone(app.units);
    await expectLater(app.setSephiraEnabled(true), throwsA(
      isA<ApiException>().having((e) => e.message, 'message',
          contains('Could not prepare a2:'))));
    expect(app.units, original);
    expect(api.roster, original);
    expect(app.sephiraEnabled, isFalse);
  });

  test('existing Crystal Fina is adopted once without resetting her edits', () async {
    final original = clone(app.units.single) as Map<String, dynamic>;
    original['stats']['Mind'] = 57;
    original['studioAcquisition'] = {'version': 1, 'random': false, 'hideSpoilers': false, 'location': 'mitra_shop'};
    api.roster = [original]; app.units = clone(api.roster) as List;
    final template = profile();
    app.sephiraPresets = [{'id': 'crystal_fina', 'name': 'Crystal Fina', 'theme': 'Healing', 'profile': template}];
    await app.setSephiraEnabled(true);
    expect(app.units, hasLength(1));
    expect(app.sephiraUnits.single['key'], original['key']);
    expect(app.sephiraUnits.single['stats']['Mind'], 57);
    expect(app.sephiraUnits.single['studioAcquisition'], original['studioAcquisition']);
    expect(api.preparations, isEmpty);
    await app.setSephiraEnabled(false);
    expect(app.includedUnitCount, 0);
    expect(app.units.single['stats']['Mind'], 57);
  });

  test('preset allocation reserves native skills as well as user roster IDs', () async {
    final reserved = {
      CharacterConfig.resonanceId(13503),
      CharacterConfig.resonanceId(13500),
      CharacterConfig.skillBase(13501),
    };
    app.catalog = {'skills': [for (final id in reserved) {'id': id}]};
    await app.setSephiraEnabled(true);
    for (final u in app.sephiraUnits) {
      final owned = {CharacterConfig.resonanceId(u['id'] as int),
        ...(u['skills'] as Map).keys.map((k) => int.parse(k.toString()))};
      expect(owned.intersection(reserved), isEmpty);
    }
  });
}
