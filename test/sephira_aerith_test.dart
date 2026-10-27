import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String,dynamic> before() {
  final unit=jsonDecode(File('scripts/fixtures/elephim_before_aerith.json').readAsStringSync()) as Map<String,dynamic>;
  unit[SephiraVisions.field]={'version':1,'preset':'elephim','enabled':false};
  return unit;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Aerith replaces only Elephim presentation and resonance while retaining edited kit and save IDs', () async {
    final presets=await SephiraVisions.bundled;
    final unit=before();unit['stats']['Mind']=777;unit['price']=1;
    unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':false,'hideSpoilers':false};
    (unit['skills'] as Map).values.first['set']['Cost']=17;
    final snapshot=CharacterConfig.copy(unit);
    final updated=SephiraVisions.repairAppearance(unit,presets);
    expect(unit,snapshot);
    const changed={'en','desc','ffbe','lb','lb_custom','command','master','sephiraAppearanceRevision'};
    for(final key in unit.keys.toSet().difference(changed)) {
      expect(updated[key],unit[key],reason:key);
    }
    expect(updated['id'],13523);
    expect(updated['command']['id'],unit['command']['id']);
    expect(updated['master']['id'],1352300);
    expect(updated['master']['en'],'Spirit of Aerith');
    expect(updated['ffbe']['id'],'207000405');
    expect(updated['lb_custom']['from'],412510);
    expect(updated['lb_custom']['en'],'Great Gospel');
    expect(CharacterConfig.decode(CharacterConfig.encode(updated)),updated);
    expect(identical(SephiraVisions.repairAppearance(updated,presets),updated),isTrue);
    updated['ffbe']['id']='207000407';updated['lb_custom']['audio']='none';
    expect(identical(SephiraVisions.repairAppearance(updated,presets),updated),isTrue);
  });

  test('fresh PCs use Aerith at the same permanent Elephim save slot', () async {
    final presets=await SephiraVisions.bundled;
    final preset=presets.singleWhere((p)=>p['id']=='elephim');
    final unit=SephiraVisions.fixedProfile(preset);
    expect(preset['name'],'Aerith');
    expect(preset['form']['label'],'5');
    expect(unit['id'],13523);expect(unit['master']['id'],1352300);
    expect(unit['ffbe']['id'],'207000405');
    unit[SephiraVisions.field]={'version':1,'preset':'elephim','enabled':true};
    expect(identical(SephiraVisions.repairAppearance(unit,presets),unit),isTrue);
  });

  test('unrelated and deliberate custom models retain their current appearance', () async {
    final presets=await SephiraVisions.bundled;
    final unit=before();unit['ffbe']['id']='custom-model';
    expect(identical(SephiraVisions.repairAppearance(unit,presets),unit),isTrue);
    unit.remove(SephiraVisions.field);
    expect(identical(SephiraVisions.repairAppearance(unit,presets),unit),isTrue);
  });
}
