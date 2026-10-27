import 'dart:convert';
import 'dart:io';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String,dynamic> oldUnit(Map<String,dynamic> p) {
  final u=CharacterConfig.copy(p['profile'] as Map<String,dynamic>);
  u.addAll(CharacterConfig.copy(p['mrRestoration']['before'] as Map<String,dynamic>));
  u.remove('sephiraMrRevision');
  u[SephiraVisions.field]={'version':1,'preset':p['id'],'enabled':true};
  return u;
}
List<List<String>> signature(Map u,String f)=>[for(final t in u[f] as List)
  [for(final g in t as List) json.encode(g)]..sort()];

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('all original MR equipables are available through MR and retain their rank',() async {
    final presets=await SephiraVisions.bundled;
    final plan=json.decode(File('scripts/fixtures/sephira_mr_restoration_plan.json').readAsStringSync()) as Map;
    for(final row in plan['placements'] as List) {
      final u=presets.singleWhere((p)=>p['id']==row[0])['profile'];
      expect(u['synchro'][row[1]][0],['ActiveSkill',row[2],-1]);
    }
  });
  test('remapped saved rosters migrate once while preserving stats, private recipes and acquisition',() async {
    final presets=await SephiraVisions.bundled;
    for(final current in presets.where((p)=>p['mrRestoration'] is Map)) {
      // Exercise the earlier MR-restoration migration separately from the
      // later reviewed Eiko/Mog/Mystea kit revision.
      final preset=CharacterConfig.copy(current);
      if (preset['esperKitBefore'] is Map<String,dynamic>) {
        preset['profile']=CharacterConfig.copy(preset['esperKitBefore'] as Map<String,dynamic>);
        preset.remove('kitUpdate');
      }
      if (preset['pharmacologyKitBefore'] is Map<String,dynamic>) {
        preset['profile']=CharacterConfig.copy(preset['pharmacologyKitBefore'] as Map<String,dynamic>);
        preset.remove('kitUpdate');
      }
      // Reproduce an allocation made by an older Studio. New imports must not
      // renumber tagged presets; loading an already-remapped legacy save must
      // still migrate its kit without changing that historical identity.
      final legacy=oldUnit(preset)..remove(SephiraVisions.field);
      final u=CharacterConfig.restore(legacy,presets.map((p)=>p['profile']).toList());
      u[SephiraVisions.field]={'version':1,'preset':preset['id'],'enabled':true};
      u['stats']['Attack']=77;u['studioAcquisition']={'version':1,'location':'mitra_shop','random':false,'hideSpoilers':false};
      (u['skills'] as Map).values.first['set']['Cost']=17;
      final before=CharacterConfig.copy(u);
      expect(SephiraVisions.hasRecipeUpdate(u,presets),isTrue);
      final next=SephiraVisions.repairEquipableMr(u,presets,strict:true);
      final target=CharacterConfig.restore(preset['profile'] as Map<String,dynamic>,[],replacing:u);
      for(final f in ['awakening','synchro']) {
        expect(signature(next,f),signature(target,f),reason:'${preset['id']} $f');
      }
      for(final f in before.keys.where((k)=>!['awakening','synchro'].contains(k))) {
        expect(next[f],before[f],reason:'${preset['id']} $f');
      }
      expect(u,before);
      expect(SephiraVisions.hasRecipeUpdate(next,[preset]),isFalse);
      if (current['kitUpdate'] is Map) {
        expect(SephiraVisions.hasRecipeUpdate(next,presets),isTrue,
            reason:'The later reviewed kit remains a separate available update.');
      }
      expect(identical(SephiraVisions.repairEquipableMr(next,presets),next),isTrue);
      next['synchro'][1][0]=['PassiveSkill',1009,-1];
      expect(identical(SephiraVisions.repairEquipableMr(next,presets),next),isTrue);
      CharacterConfig.decode(CharacterConfig.encode(next));
    }
  });
  test('edited MR and overfilled awakening tiers remain intact with clear conflicts',() async {
    final presets=await SephiraVisions.bundled;
    final p=presets.singleWhere((p)=>p['id']=='christine');final u=oldUnit(p);
    u['synchro'][5][0]=['PassiveSkill',1009,-1];
    expect(identical(SephiraVisions.repairEquipableMr(u,presets),u),isTrue);
    expect(()=>SephiraVisions.repairEquipableMr(u,presets,strict:true),throwsA(isA<StateError>().having((e)=>e.message,'message',contains('MR5 was edited'))));
    final full=oldUnit(presets.singleWhere((p)=>p['id']=='barusa'));
    var id=220010;
    for(final t in full['awakening'] as List) {
      while((t as List).length<8) { t.add(['ActiveSkill',id,-1]);id+=10; }
    }
    final before=CharacterConfig.copy(full);
    expect(identical(SephiraVisions.repairEquipableMr(full,presets),full),isTrue);
    expect(()=>SephiraVisions.repairEquipableMr(full,presets,strict:true),throwsA(isA<StateError>().having((e)=>e.message,'message',contains('awakening slot'))));
    expect(full,before);
  });
  test('an older awakening revision receives its old bonuses before the MR restoration',() async {
    final presets=await SephiraVisions.bundled;final p=presets.singleWhere((p)=>p['id']=='christine');
    final old=oldUnit(p);old['sephiraRecipe']=6;
    old['awakening']=[for(final tier in old['awakening'] as List) [for(final g in tier as List) if(g[0]!='PassiveSkill') g]];
    old['synchro'][2][0][2]=77;
    final next=SephiraVisions.updateProgression(old,p);
    expect(next['sephiraRecipe'],7);expect(next['sephiraMrRevision'],1);
    expect(next['synchro'][5][0],['ActiveSkill',400630,-1]);
    expect(next['synchro'][2][0][2],77);
  });
}
