import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String,dynamic> before(String name) => Map<String,dynamic>.from(
  (json.decode(File('scripts/fixtures/sephira_user_kits_before.json').readAsStringSync()) as Map)[name] as Map);

List<List<String>> layout(Map unit) => [for (final tier in unit['awakening'] as List)
  [for (final g in tier as List)
    if (g[0]=='ActiveSkill' && unit['skills'][g[1].toString()] is Map)
      'custom:${unit['skills'][g[1].toString()]['from']}'
    else '${g[0]}:${g[1]}']];

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('reviewed Fina and Aria kits match their exact shared tier capacities', () async {
    final presets=await SephiraVisions.bundled;
    final fina=presets.singleWhere((p)=>p['id']=='crystal_fina')['profile'] as Map;
    final aria=presets.singleWhere((p)=>p['id']=='aria')['profile'] as Map;
    expect((fina['awakening'] as List).map((t)=>(t as List).length),[7,8,7,3]);
    expect((aria['awakening'] as List).map((t)=>(t as List).length),[8,8,7,2]);
    expect(layout(fina).first,['ActiveSkill:210010','ActiveSkill:210250','custom:570690','ActiveSkill:230040','ActiveSkill:210140','PassiveSkill:1381','PassiveSkill:1107']);
    expect(layout(aria).first,['ActiveSkill:420100','ActiveSkill:220480','custom:245000','custom:502020','custom:225090','custom:503970','ActiveSkill:210120','PassiveSkill:1375']);
    expect(layout(fina).last,['custom:210190','ActiveSkill:210160','PassiveSkill:1456']);
    expect(layout(aria).last,['ActiveSkill:210160','PassiveSkill:1352']);
    expect(aria['synchro'][9][0],['PassiveSkill',1524,-1]);
    expect(aria['master']['id'],before('aria')['master']['id']);
    expect(fina['synchro'],before('crystal_fina')['synchro']);
  });

  test('existing remapped kits keep identities, combat edits and unrelated settings', () async {
    final presets=await SephiraVisions.bundled;
    for (final id in ['crystal_fina','aria']) {
      final source=before(id);
      final unit=CharacterConfig.restore(source,presets.map((p)=>p['profile']).toList());
      unit[SephiraVisions.field]={'version':1,'preset':id,'enabled':false};
      unit['en']='My $id';unit['stats']['Mind']=777;unit['price']=1;
      unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':false,'hideSpoilers':false};
      final recipe=(unit['skills'] as Map).values.whereType<Map>().firstWhere((r)=>r['from']==(id=='aria'?245000:503630));
      recipe['set']['Cost']=17;recipe['desc']='My description';
      final snapshot=CharacterConfig.copy(unit);
      final next=SephiraVisions.repairKit(unit,presets,strict:true);
      expect(layout(next),layout(presets.singleWhere((p)=>p['id']==id)['profile'] as Map));
      for (final field in ['id','key','en','stats','ffbe','skills','lb_custom','studioAcquisition',SephiraVisions.field]) {
        expect(next[field],snapshot[field],reason:'$id $field');
      }
      expect(next['master']['id'],snapshot['master']['id']);
      for (var rank=0;rank<10;rank++) {
        expect((next['synchro'][rank] as List).where((g)=>g[0]!='PassiveSkill').toList(),
          (snapshot['synchro'][rank] as List).where((g)=>g[0]!='PassiveSkill').toList());
      }
      expect(unit,snapshot);
      expect(identical(SephiraVisions.repairKit(next,presets),next),isTrue);
      next['awakening'][3].removeLast();
      expect(identical(SephiraVisions.repairKit(next,presets),next),isTrue,reason:'Later deliberate edits remain yours.');
      CharacterConfig.decode(CharacterConfig.encode(next));
    }
  });

  test('draft internal Reraise becomes its castable spell and extra abilities survive', () async {
    final presets=await SephiraVisions.bundled;
    final unit=CharacterConfig.copy(presets.singleWhere((p)=>p['id']=='crystal_fina')['profile'] as Map<String,dynamic>);
    unit.remove('sephiraKitRevision');unit[SephiraVisions.field]={'version':1,'preset':'crystal_fina','enabled':true};
    unit['awakening'][3][1][1]=210240;
    unit['awakening'][3].add(['ActiveSkill',220010,-1]);
    final next=SephiraVisions.repairKit(unit,presets,strict:true);
    expect(layout(next).last,['custom:210190','ActiveSkill:210160','PassiveSkill:1456','ActiveSkill:220010']);
  });

  test('full edited tiers remain unchanged and explicit update explains the capacity conflict', () async {
    final presets=await SephiraVisions.bundled;
    final unit=before('crystal_fina');
    unit[SephiraVisions.field]={'version':1,'preset':'crystal_fina','enabled':true};
    unit['awakening'][1].add(['ActiveSkill',220010,-1]);
    final snapshot=CharacterConfig.copy(unit);
    expect(identical(SephiraVisions.repairKit(unit,presets),unit),isTrue);
    expect(()=>SephiraVisions.repairKit(unit,presets,strict:true),throwsA(isA<StateError>().having((e)=>e.message,'message',contains('tier 2'))));
    expect(unit,snapshot);
    expect(SephiraVisions.hasRecipeUpdate(unit,presets),isTrue);
  });

  test('independent Fina gains the same kit without enrollment or MR/stat reset', () async {
    final presets=await SephiraVisions.bundled;
    final unit=before('independent_fina');final snapshot=CharacterConfig.copy(unit);
    final next=SephiraVisions.repairKit(unit,presets,strict:true);
    expect(layout(next),layout(presets.singleWhere((p)=>p['id']=='crystal_fina')['profile'] as Map));
    expect(next['synchro'],snapshot['synchro']);
    expect(next['stats'],snapshot['stats']);
    expect(next['master']['id'],snapshot['master']['id']);
    expect(next.containsKey(SephiraVisions.field),isFalse);
    expect(unit,snapshot);
    CharacterConfig.decode(CharacterConfig.encode(next));
  });
}
