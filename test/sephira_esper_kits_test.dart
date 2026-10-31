import 'dart:convert';
import 'dart:io';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('Revelry updates its previous description without changing saved kits or custom text', () async {
    final presets = await SephiraVisions.bundled;
    final preset = presets.singleWhere((p) => p['id'] == 'eiko');
    final unit = CharacterConfig.copy(preset['profile'] as Map<String, dynamic>);
    unit[SephiraVisions.field] = {'version': 1, 'preset': 'eiko', 'enabled': true};
    unit['sephiraPassiveText']['1963']['name'] = 'My label';
    unit['sephiraPassiveText']['1963']['desc'] = 'Each ordinary esper action has a 50% chance to become its special. The final special is guaranteed.';
    unit['stats']['Mind'] = 999;
    final before = CharacterConfig.copy(unit);
    final expected = CharacterConfig.copy(unit);
    expected['sephiraPassiveText']['1963']['desc'] = 'Each ordinary esper action has a 30% chance to become its special. The final special is guaranteed.';
    final actual = SephiraVisions.repairDescriptions(unit, presets);
    expect(actual, expected);
    expect(unit, before);
    expect(identical(SephiraVisions.repairDescriptions(actual, presets), actual), isTrue);
    unit['sephiraPassiveText']['1963']['desc'] = 'My custom description';
    expect(identical(SephiraVisions.repairDescriptions(unit, presets), unit), isTrue);
  });
  test('Rikku Pharmacology replaces only default MR7 and respects later edits', () async {
    final presets = await SephiraVisions.bundled;
    final p = presets.singleWhere((p) => p['id'] == 'rikku');
    final unit = CharacterConfig.copy(p['pharmacologyKitBefore'] as Map<String, dynamic>);
    unit[SephiraVisions.field] = {'version': 1, 'preset': 'rikku', 'enabled': false};
    unit['awakening'][0] = (unit['awakening'][0] as List).reversed.toList();
    unit['sephiraPassiveText'] = {'1387': {'name': 'My label', 'desc': 'My text'}};
    unit['en'] = 'My Rikku';
    unit['stats']['Attack'] = 999;
    final before = CharacterConfig.copy(unit);
    final actual = SephiraVisions.repairKit(unit, presets, strict: true);
    expect(actual['synchro'][7], [['PassiveSkill', 1044, -1]]);
    for (final field in before.keys.where((k) => k != 'synchro' && k != 'sephiraKitRevision')) {
      expect(actual[field], before[field], reason: field);
    }
    for (var rank = 0; rank < 10; rank++) {
      if (rank != 7) expect(actual['synchro'][rank], before['synchro'][rank]);
    }
    expect(actual['master']['id'], 1352700);
    expect(unit, before);
    CharacterConfig.decode(CharacterConfig.encode(actual));
    actual['synchro'][7] = [['PassiveSkill', 1280, -1]];
    expect(identical(SephiraVisions.repairKit(actual, presets), actual), isTrue);
    final conflict = CharacterConfig.copy(before);
    conflict['synchro'][7] = [['PassiveSkill', 1280, -1]];
    expect(identical(SephiraVisions.repairKit(conflict, presets), conflict), isTrue);
    expect(() => SephiraVisions.repairKit(conflict, presets, strict: true), throwsStateError);
  });
  test('Eiko support update moves Raise and adds Shellga to an existing kit', () async {
    final presets = await SephiraVisions.bundled;
    final p = presets.singleWhere((p) => p['id'] == 'eiko');
    final unit = CharacterConfig.copy(p['profile'] as Map<String, dynamic>);
    unit[SephiraVisions.field] = {'version': 1, 'preset': 'eiko', 'enabled': true};
    final raise = ['ActiveSkill', 210140, -1];
    final shellga = ['ActiveSkill', 230070, -1];
    unit['awakening'][0].removeWhere((g) => g[1] == 210140);
    unit['awakening'][1].removeWhere((g) => g[1] == 230070);
    unit['awakening'][1].insert(1, raise);
    unit['sephiraKitRevision'] = 1;
    unit['awakening'][0].add(['ActiveSkill', 210120, -1]);
    final before = CharacterConfig.copy(unit);
    final actual = SephiraVisions.repairKit(unit, presets, strict: true);
    expect(actual['awakening'][0], contains(equals(raise)));
    expect(actual['awakening'][1], isNot(contains(equals(raise))));
    expect(actual['awakening'][1], contains(equals(shellga)));
    expect(actual['awakening'][0], contains(equals(['ActiveSkill', 210120, -1])));
    for (final field in before.keys.where((k) => k != 'awakening' && k != 'sephiraKitRevision')) {
      expect(actual[field], before[field], reason: field);
    }
    expect((actual['awakening'] as List).every((t) => (t as List).length <= 8), isTrue);
    expect(identical(SephiraVisions.repairKit(actual, presets), actual), isTrue);
    expect(unit, before);
    CharacterConfig.decode(CharacterConfig.encode(actual));
  });
  test('Eiko and Mog reward moves migrate once while keeping save IDs and edits', () async {
    final presets=await SephiraVisions.bundled;
    for (final id in ['eiko','mog','mystea']) {
      final p=presets.singleWhere((p)=>p['id']==id);
      final unit=CharacterConfig.copy(p['esperKitBefore'] as Map<String,dynamic>);
      unit[SephiraVisions.field]={'version':1,'preset':id,'enabled':false};
      unit['en']='My $id';unit['stats']['Mind']=999;
      unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':false,'hideSpoilers':false};
      final old=CharacterConfig.copy(unit);
      final actual=SephiraVisions.repairKit(unit,presets,strict:true);
      expect(actual['awakening'],p['profile']['awakening']);
      expect(actual['synchro'],p['profile']['synchro']);
      for (final field in ['id','key','en','stats','ffbe','lb_custom','studioAcquisition',SephiraVisions.field]) {
        expect(actual[field],old[field],reason:'$id $field');
      }
      for (final key in (old['skills'] as Map).keys) {expect(actual['skills'][key],old['skills'][key]);}
      expect(actual['master']['id'],old['master']['id']);
      expect(actual['master']['desc'],p['profile']['master']['desc']);
      expect(identical(SephiraVisions.repairKit(actual,presets),actual),isTrue);
      expect(unit,old);
      CharacterConfig.decode(CharacterConfig.encode(actual));
    }
  });
  test('edited MR conflicts remain openable and the explicit update explains them', () async {
    final presets=await SephiraVisions.bundled;
    final unit=CharacterConfig.copy(presets.singleWhere((p)=>p['id']=='eiko')['esperKitBefore'] as Map<String,dynamic>);
    unit[SephiraVisions.field]={'version':1,'preset':'eiko','enabled':true};
    unit['synchro'][7][0][1]=1256;
    final old=CharacterConfig.copy(unit);
    expect(identical(SephiraVisions.repairKit(unit,presets),unit),isTrue);
    expect(()=>SephiraVisions.repairKit(unit,presets,strict:true),throwsA(isA<StateError>().having((e)=>e.message,'message',contains('MR7'))));
    expect(unit,old);
  });
  test('fixed profiles and installed runtime data agree on all four new reward IDs', () async {
    final presets=await SephiraVisions.bundled;
    final source=json.decode(File('assets/existing_visions/payload/esper_mastery.json').readAsStringSync()) as Map;
    final p=presets.singleWhere((p)=>p['id']=='eiko');
    final u=SephiraVisions.fixedProfile(p);
    expect(u['id'],13515);
    expect([for (final rank in [1,3,5,7,9]) u['synchro'][rank][0][1]],[1107,1960,1961,1962,1963]);
    for (final id in [1960,1961,1962,1963]) {
      expect(u['sephiraPassiveText']['$id']['name'],source['passives']['$id']['name']);
      expect(source['passives']['$id']['marker'],id*100);
    }
    expect(u['synchro'][9].last,['MasterSkill',1351500,-1]);
  });
}
