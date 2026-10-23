import 'dart:io';
import 'dart:convert';

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

Map<String, dynamic> revision5Preset(Map<String, dynamic> value) {
  final result = CharacterConfig.copy(value);
  (result['profile'] as Map).addAll(CharacterConfig.copy(result['revision5Progression'] as Map<String, dynamic>));
  result['profile']['sephiraRecipe'] = 5;
  return result;
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

  test('LB audio repairs old defaults once and preserves kits and later explicit mutes', () async {
    final presets = await SephiraVisions.bundled;
    for (final p in presets) {
      final old = CharacterConfig.copy(p['profile'] as Map<String, dynamic>);
      old[SephiraVisions.field] = {'version': 1, 'preset': p['id'], 'enabled': true};
      (old['lb_custom'] as Map)..remove('sephiraAudio')..['audio'] = 'none';
      final before = CharacterConfig.copy(old);
      final next = SephiraVisions.repairLbAudio(old, presets);
      expect(next['lb_custom']['audio'], 'native');
      expect(next['lb_custom']['audio_codec'], 'host');
      expect(next['lb_custom']['sephiraAudio'], 1);
      expect(old, before);
      for (final field in old.keys.where((k) => k != 'lb_custom')) {
        expect(next[field], old[field]);
      }
      expect(SephiraVisions.repairLbAudio(next, presets), same(next));
      next['lb_custom']['audio'] = 'none';
      expect(SephiraVisions.repairLbAudio(next, presets), same(next));
      old['lb_custom']['audio_bank'] = 'my-recordings.json';
      expect(SephiraVisions.repairLbAudio(old, presets), same(old));
      old.remove(SephiraVisions.field);
      if (p['id'] != 'crystal_fina') expect(SephiraVisions.repairLbAudio(old, presets), same(old));
    }
  });

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
    expect(presets, hasLength(30));
    expect(presets.where((p) => p['profile'] == null), isEmpty);
    final configs = presets.map((p) => CharacterConfig.copy(p['profile'] as Map<String, dynamic>)).toList();
    CharacterConfig.validateAll(configs);
    final targets = List<Map<String, dynamic>?>.filled(configs.length, null);
    // Every preferred identity already belongs to another user entry.
    final loaded = CharacterConfig.restoreAll(configs, configs, targets);
    CharacterConfig.validateAll([...configs, ...loaded]);
    final minfilia = loaded.singleWhere((u) => u['en'] == 'Minfilia');
    final dual = (minfilia['skills'] as Map).values.singleWhere((s) => s['from'] == 445210);
    expect(dual['set']['mimicableUnitId'], minfilia['id']);
    expect(minfilia['id'], isNot(configs[6]['id']));
    for (final u in loaded) {
      // Count the portable, remapped grants actually used by the builder;
      // learned MR skills must remain additional to the awakening quota.
      final awakening = (u['awakening'] as List).expand((tier) => tier as List)
          .where((g) => g[0] == 'ActiveSkill' || g[0] == 'PassiveSkill').length;
      final mr = (u['synchro'] as List).expand((tier) => tier as List)
          .where((g) => g[0] == 'ActiveSkill' || g[0] == 'PassiveSkill').length;
      final preset = presets.singleWhere((p) => p['profile']['en'] == u['en']);
      expect(awakening, inInclusiveRange(15, 28), reason: u['en'] as String);
      expect(awakening, preset['balance']['kitCount']);
      expect(mr, preset['balance']['mrSkillCount']);
      expect(awakening + mr, preset['balance']['totalSkillCount']);
      for (final skill in (u['skills'] as Map).values) {
        final settings = skill['set'] as Map;
        if (settings.containsKey('belongCommandList')) {
          expect(settings['belongCommandList'], [u['command']['id']]);
          expect(settings['commandIdBelongDebuggingAllSkills'], [u['command']['id'], -1]);
        }
      }
    }
  });


  test('MR migration retains every saved ability and combat edit after identity remapping', () async {
    final presets = [for (final p in await SephiraVisions.bundled) revision5Preset(p)];
    final previous = json.decode(File('scripts/fixtures/sephira_revision3_grants.json').readAsStringSync()) as Map;
    final occupied = presets.map((p) => p['profile']).toList();
    final revision4 = json.decode(File('scripts/fixtures/sephira_revision4_grants.json').readAsStringSync()) as Map;
    for (final preset in presets) {
      final old = CharacterConfig.copy(preset['profile'] as Map<String, dynamic>);
      old['awakening'] = previous[preset['id']]['awakening'];
      old['synchro'] = previous[preset['id']]['synchro'];
      old['sephiraRecipe'] = 3;
      (old['skills'] as Map).addAll(revision4[preset['id']]['skills'] as Map);
      for (final r in preset['rewardReplacements'] as List) {
        if (r['newGrant'][0] == 'ActiveSkill') (old['skills'] as Map).remove(r['newGrant'][1].toString());
      }
      for (final id in preset['masteryFillers'] as List) { (old['skills'] as Map).remove(id.toString()); }
      final saved = CharacterConfig.restore(old, occupied);
      saved[SephiraVisions.field] = {'version': 1, 'preset': preset['id'], 'enabled': false};
      saved['stats']['Attack'] = 123;
      final customSkill = (saved['skills'] as Map).values.first as Map;
      customSkill['set']['Cost'] = 27;
      final before = CharacterConfig.copy(saved);
      Set<String> grants(Map value) => {for (final field in ['awakening', 'synchro'])
        for (final tier in value[field] as List) for (final g in tier as List)
          if (g[0] == 'ActiveSkill' || g[0] == 'PassiveSkill') '${g[0]}:${g[1]}'};
      final next = SephiraVisions.updateProgression(saved, preset);
      final removed = {for (final r in preset['rewardReplacements'] as List)
        '${r['oldKind']}:${r['oldKind'] == 'ActiveSkill' && r['oldId'] != r['oldSource'] ? CharacterConfig.skillBase(saved['id'] as int) + (r['oldId'] as int) - CharacterConfig.skillBase(preset['profile']['id'] as int) : r['oldId']}'};
      expect(grants(next).containsAll(grants(before).difference(removed)), isTrue, reason: preset['id'] as String);
      expect(saved, before);
      expect(next['id'], saved['id']);
      expect(next['ffbe'], saved['ffbe']);
      expect(next['stats'], saved['stats']);
      expect(next[SephiraVisions.field], saved[SephiraVisions.field]);
      for (final entry in (saved['skills'] as Map).entries) {
        if (!(preset['rewardReplacements'] as List).any((r) => r['oldKind'] == 'ActiveSkill' && r['oldSource'] == (entry.value as Map)['from'])) {
          expect(next['skills'][entry.key], entry.value);
        }
      }
      expect(next['sephiraRecipe'], 5);
      expect((next['awakening'] as List).expand((t) => t as List).length, inInclusiveRange(20, 28));
      expect((next['synchro'] as List).map((t) => (t as List).length).toList(), [0,1,1,1,1,1,1,1,1,3]);
      final portable = CharacterConfig.decode(CharacterConfig.encode(next));
      expect(portable['studioAcquisition'], next['studioAcquisition']);
      // Applying the update again must not add another filler or alter a kit.
      expect(SephiraVisions.updateProgression(next, preset), next);
    }
  });

  test('revision 4 source correction replaces all protected grants in place and keeps custom acquisition and IDs', () async {
    final presets = [for (final p in await SephiraVisions.bundled) revision5Preset(p)];
    final previous = json.decode(File('scripts/fixtures/sephira_revision4_grants.json').readAsStringSync()) as Map;
    final occupied = presets.map((p) => p['profile']).toList();
    var replacements = 0;
    for (final preset in presets) {
      final old = CharacterConfig.copy(preset['profile'] as Map<String, dynamic>);
      old['awakening'] = previous[preset['id']]['awakening'];
      old['synchro'] = previous[preset['id']]['synchro'];
      old['sephiraRecipe'] = 4;
      (old['skills'] as Map).addAll(previous[preset['id']]['skills'] as Map);
      for (final r in preset['rewardReplacements'] as List) {
        if (r['newGrant'][0] == 'ActiveSkill') (old['skills'] as Map).remove(r['newGrant'][1].toString());
      }
      final saved = CharacterConfig.restore(old, occupied);
      saved[SephiraVisions.field] = {'version':1, 'preset':preset['id'], 'enabled':true};
      saved['studioAcquisition'] = {'version':2, 'location':'shop_3', 'random':false, 'hideSpoilers':true, 'cave':null};
      saved['stats']['Attack'] = 123;
      final firstActive = (preset['rewardReplacements'] as List).where((r) => r['newGrant'][0] == 'ActiveSkill').firstOrNull;
      int? customId;
      if (firstActive != null) {
        customId = CharacterConfig.skillBase(saved['id'] as int) + (firstActive['newGrant'][1] as int) - CharacterConfig.skillBase(old['id'] as int);
        saved['skills'][customId.toString()] = {'from':220010, 'en':'My custom spell', 'jp':'MyCustom', 'desc':'My edited spell.', 'set':{'Cost':7}};
      }
      final before = CharacterConfig.copy(saved);
      final updated = SephiraVisions.updateProgression(saved, preset);
      for (final r in preset['rewardReplacements'] as List) {
        replacements++;
        final grant = updated[r['field']][r['rank']].firstWhere((g) => g[0] == r['newGrant'][0] &&
            (g[0] == 'PassiveSkill' ? g[1] == r['source'] : updated['skills'][g[1].toString()]['from'] == r['source']));
        expect(grant, isNotNull, reason:preset['id'] as String);
      }
      expect(updated['studioAcquisition'], saved['studioAcquisition']);
      expect(updated['id'], saved['id']);
      expect(updated['stats'], saved['stats']);
      expect(updated['ffbe'], saved['ffbe']);
      expect(updated['lb_custom'], saved['lb_custom']);
      if (customId != null) expect(updated['skills'][customId.toString()], saved['skills'][customId.toString()]);
      expect(saved, before);
      expect(SephiraVisions.updateProgression(updated,preset),updated);
      CharacterConfig.decode(CharacterConfig.encode(updated));
    }
    expect(replacements,52);
  });

  test('revision 6 curates all 131 original passives and keeps active skills, edits and permanent stats', () async {
    final presets = await SephiraVisions.bundled;
    final occupied = presets.map((p) => p['profile']).toList();
    final passiveIds = <int>[];
    for (final preset in presets) {
      final previous = revision5Preset(preset);
      final saved = CharacterConfig.restore(previous['profile'] as Map<String, dynamic>, occupied);
      saved[SephiraVisions.field] = {'version':1, 'preset':preset['id'], 'enabled':false};
      saved['studioAcquisition'] = {'version':1, 'random':false, 'hideSpoilers':false, 'location':'mitra_shop'};
      (saved['skills'] as Map).values.first['set']['Cost'] = 27;
      saved['stats']['Attack'] = 123;
      final before = CharacterConfig.copy(saved);
      final revision6 = CharacterConfig.copy(preset);
      revision6['profile']['sephiraRecipe'] = 6;
      final next = SephiraVisions.updateProgression(saved, revision6);
      final active = {for (final field in ['awakening','synchro']) for (final tier in saved[field] as List)
        for (final g in tier as List) if (g[0]=='ActiveSkill') g[1]};
      expect({for (final tier in next['awakening'] as List) for (final g in tier as List) g[1]}, active);
      expect((next['awakening'] as List).expand((t) => t as List).every((g) => g[0]=='ActiveSkill'), isTrue);
      for (final rank in [1,3,5,7,9]) {
        final chosen = (next['synchro'][rank] as List).where((g) => g[0]=='PassiveSkill').single;
        expect(chosen, preset['profile']['synchro'][rank][0]);
        passiveIds.add(chosen[1] as int);
      }
      for (final field in ['id','key','ffbe','stats','skills','lb_custom','studioAcquisition',SephiraVisions.field]) {
        expect(next[field], saved[field], reason:'${preset['id']}: $field');
      }
      for (var rank = 0; rank < 10; rank++) {
        expect((next['synchro'][rank] as List).where((g) => g[0]=='BaseParameter' || g[0]=='MasterSkill').toList(),
            (saved['synchro'][rank] as List).where((g) => g[0]=='BaseParameter' || g[0]=='MasterSkill').toList());
      }
      expect(saved, before);
      expect(next['sephiraRecipe'],6);
      expect(SephiraVisions.updateProgression(next,revision6),next);
      CharacterConfig.decode(CharacterConfig.encode(next));
    }
    expect(passiveIds,hasLength(150));
    expect(passiveIds.toSet(),hasLength(150));
    final coverage = json.decode(File('assets/sephira_visions/native_coverage.json').readAsStringSync()) as Map;
    final originals = (coverage['entries'] as List).where((e) => e['kind']=='PassiveSkill').map((e) => e['id']).toSet();
    expect(originals,hasLength(131));
    expect(passiveIds.toSet().containsAll(originals),isTrue);
  });

  test('revision 7 adds awakening bonuses without resetting edited MR or active skills', () async {
    final presets = await SephiraVisions.bundled;
    var additions = 0;
    for (final preset in presets) {
      final unit = CharacterConfig.copy(preset['profile'] as Map<String,dynamic>);
      unit[SephiraVisions.field] = {'version':1,'preset':preset['id'],'enabled':false};
      unit['sephiraRecipe'] = 6;
      unit['awakening'] = [for (final tier in unit['awakening'] as List)
        [for (final g in tier as List) if (g[0]!='PassiveSkill') g]];
      unit['synchro'][2][0][2] = 77;
      unit['stats']['Attack'] = 123;
      (unit['skills'] as Map).values.first['set']['Cost'] = 27;
      final before = CharacterConfig.copy(unit);
      final next = SephiraVisions.updateProgression(unit,preset);
      for (final field in unit.keys.where((k) => k!='awakening' && k!='sephiraRecipe')) {
        expect(next[field],unit[field],reason:'${preset['id']}: $field');
      }
      expect((next['awakening'] as List).expand((t)=>t as List).where((g)=>g[0]=='ActiveSkill').toList(),
          (unit['awakening'] as List).expand((t)=>t as List).where((g)=>g[0]=='ActiveSkill').toList());
      final bonus = (next['awakening'] as List).expand((t)=>t as List).where((g)=>g[0]=='PassiveSkill').toList();
      additions += bonus.length;
      expect(bonus.length,(preset['awakeningBalance']['grants'] as List).length);
      expect((next['awakening'] as List).every((t)=>(t as List).length<=8),isTrue);
      expect(next['sephiraRecipe'],7);
      expect(unit,before);
      expect(SephiraVisions.updateProgression(next,preset),next);
      CharacterConfig.decode(CharacterConfig.encode(next));
    }
    expect(additions,160);
    final full = CharacterConfig.copy(presets.first['profile'] as Map<String,dynamic>);
    full['sephiraRecipe']=6;
    full['awakening']=[for (var tier=0;tier<4;tier++)
      [for (var i=0;i<8;i++) ['ActiveSkill',220010+tier*100+i,-1]]];
    final before = CharacterConfig.copy(full);
    expect(()=>SephiraVisions.updateProgression(full,presets.first),throwsStateError);
    expect(full,before);
  });

  test('independent Fina receives awakening bonuses once and preserves edited full kits', () async {
    final presets=await SephiraVisions.bundled;
    final unit=json.decode(File('assets/crystal_fina/profile.json').readAsStringSync()) as Map<String,dynamic>;
    unit['sephiraRecipe']=6;
    unit['awakening']=[for(final tier in unit['awakening'] as List)
      [for(final g in tier as List) if(g[0]!='PassiveSkill') g]];
    final next=SephiraVisions.repairIndependentBonuses(unit,presets);
    expect(next['sephiraRecipe'],7);
    expect((next['awakening'] as List).expand((t)=>t as List).where((g)=>g[0]=='PassiveSkill'),hasLength(5));
    expect(next['synchro'],unit['synchro']);
    expect(SephiraVisions.repairIndependentBonuses(next,presets),same(next));
    unit['awakening']=[for(var t=0;t<4;t++) [for(var i=0;i<8;i++) ['ActiveSkill',220010+t*100+i,-1]]];
    expect(SephiraVisions.repairIndependentBonuses(unit,presets),same(unit));
  });

  test('progression update backs up the old roster and commits atomically', () async {
    final presets = await SephiraVisions.bundled;
    final unit = CharacterConfig.copy(presets.first['profile'] as Map<String, dynamic>);
    unit[SephiraVisions.field] = {'version': 1, 'preset': presets.first['id'], 'enabled': true};
    unit['sephiraRecipe'] = 3;
    unit['stats']['Attack'] = 123;
    api.roster = [unit]; app.units = clone(api.roster) as List; app.sephiraPresets = presets;
    api.fail = true;
    await expectLater(app.updateSephiraProgression(), throwsStateError);
    expect(api.roster.single['sephiraRecipe'], 3);
    expect(app.units.single['sephiraRecipe'], 3);
    api.fail = false;
    await app.updateSephiraProgression();
    expect(app.units.single['sephiraRecipe'], 7);
    expect(app.units.single['stats']['Attack'], 123);
    final backups = Directory(app.paths.configBackups).listSync().whereType<File>();
    expect(backups, isNotEmpty);
    expect(CharacterConfig.decodeAll(backups.first.readAsStringSync()).single['sephiraRecipe'], 3);
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
    expect(app.sephiraUnits, hasLength(30));
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

  test('recipe update notice preserves saved edits until explicit reset', () async {
    app.sephiraPresets.first['profile'].remove('sephiraRecipe');
    await app.setSephiraEnabled(true);
    final edited = CharacterConfig.copy(app.sephiraUnits.first);
    edited['stats']['Attack'] = 47;
    app.update(edited);
    app.sephiraPresets.first['profile']['sephiraRecipe'] = 2;
    expect(app.sephiraRecipeUpdate, isTrue);
    await app.setSephiraEnabled(false);
    await app.setSephiraEnabled(true);
    expect(app.sephiraRecipeUpdate, isTrue);
    expect(app.sephiraUnits.first['stats']['Attack'], 47);
    await app.restoreSephira(presetId: 'a2', reset: true);
    expect(app.sephiraRecipeUpdate, isFalse);
    expect(app.sephiraUnits.first['sephiraRecipe'], 2);
    expect(app.sephiraUnits.first['stats']['Attack'], isNot(47));
  });

  test('reset all backs up retired Great Dragon and preserves independent copies', () async {
    await app.setSephiraEnabled(true);
    final retired = CharacterConfig.restore(profile(), app.units)
      ..[SephiraVisions.field] = {'version': 1, 'preset': 'great_dragon', 'enabled': true};
    final independent = CharacterConfig.restore(profile(), [...app.units, retired])
      ..['en'] = 'Great Dragon';
    api.roster = clone([...app.units, retired, independent]) as List;
    app.units = clone(api.roster) as List;
    expect(SephiraVisions.included(retired), isFalse);
    expect(app.sephiraUnits, hasLength(2));
    await app.restoreSephira(reset: true);
    expect(app.units.where((u) => SephiraVisions.retiredMember(u as Map)), isEmpty);
    expect(app.units.singleWhere((u) => u['key'] == independent['key']), independent);
    final backup = Directory(app.paths.configBackups).listSync().whereType<File>().single;
    expect(CharacterConfig.decodeAll(backup.readAsStringSync()).where(SephiraVisions.retiredMember), hasLength(1));
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
