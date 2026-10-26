import 'dart:convert';
import 'dart:io';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
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
