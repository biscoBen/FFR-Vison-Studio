import 'dart:convert';

import 'package:ffr_vision_studio/services/api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('changing a testing switch preserves the other persisted settings', () async {
    var settings = <String, dynamic>{'schema': 1, 'maxMr': true, 'practiceBattle': false, 'crystalCave': false, 'crystalCaveTest': false, 'fieldLeader': true};
    final client = MockClient((request) async {
      expect(request.url.path, '/api/testing');
      if (request.method == 'PUT') {
        settings = jsonDecode(request.body) as Map<String, dynamic>;
      }
      return http.Response(jsonEncode(settings), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://studio');
      await api.saveCrystalCave(true);
      await api.saveTestingPracticeBattle(true);
      expect(settings, {'schema': 1, 'maxMr': true, 'practiceBattle': true, 'practiceEncounter': 'standard', 'crystalCave': true, 'crystalCaveTest': false, 'fieldLeader': true});
      await api.saveTestingMaxMr(false);
      expect(settings, {'schema': 1, 'maxMr': false, 'practiceBattle': true, 'practiceEncounter': 'standard', 'crystalCave': true, 'crystalCaveTest': false, 'fieldLeader': true});
      expect(await api.fieldLeader(), isTrue);
      await api.saveFieldLeader(false);
      expect(settings, {'schema': 1, 'maxMr': false, 'practiceBattle': true, 'practiceEncounter': 'standard', 'crystalCave': true, 'crystalCaveTest': false, 'fieldLeader': false});
      expect(await api.testingPracticeBattle(), isTrue);
      expect(await api.crystalCave(), isTrue);
    }, () => client);
  });

  test('legacy MR settings keep the new practice battle disabled', () async {
    final client = MockClient((_) async => http.Response('{"schema":1,"maxMr":true}', 200));
    await http.runWithClient(() async {
      expect(await Api('http://studio').testingPracticeBattle(), isFalse);
      expect(await Api('http://studio').testingPracticeEncounter(), 'standard');
      expect(await Api('http://studio').crystalCave(), isFalse);
      expect(await Api('http://studio').fieldLeader(), isFalse);
      expect(await Api('http://studio').crystalCaveTest(), isFalse);
    }, () => client);
  });

  test('practice opponents survive unrelated switches and disabling the battle', () async {
    var settings = <String, dynamic>{'schema': 1, 'maxMr': false, 'practiceBattle': true};
    final client = MockClient((request) async {
      if (request.method == 'PUT') settings = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(jsonEncode(settings), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://studio');
      await api.saveTestingPracticeEncounter('cactuar');
      await api.saveTestingMaxMr(true);
      await api.saveTestingPracticeBattle(false);
      expect(await api.testingPracticeEncounter(), 'cactuar');
      expect(settings['maxMr'], isTrue);
      expect(settings['practiceBattle'], isFalse);
      await api.saveTestingPracticeBattle(true);
      expect(await api.testingPracticeEncounter(), 'cactuar');
    }, () => client);
  });

  test('Fina test and original cave are exclusive and other settings survive', () async {
    var settings = <String, dynamic>{'schema': 1, 'maxMr': true,
      'practiceBattle': true, 'crystalCave': true, 'fieldLeader': true,
      'crystalCaveTestSolid': true, 'crystalCaveTestRotate': false};
    final client = MockClient((request) async {
      if (request.method == 'PUT') settings = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(jsonEncode(settings), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://studio');
      await api.saveCrystalCaveTest(true);
      expect(await api.crystalCaveTest(), isTrue);
      expect(settings.containsKey('crystalCaveTestSolid'), isFalse);
      expect(settings.containsKey('crystalCaveTestRotate'), isFalse);
      expect(settings['crystalCave'], isFalse);
      await api.saveTestingMaxMr(false);
      expect(settings['crystalCaveTest'], isTrue);
      expect(settings['practiceBattle'], isTrue);
      expect(settings['fieldLeader'], isTrue);
      await api.saveCrystalCave(true);
      expect(settings['crystalCaveTest'], isFalse);
      expect(settings['crystalCave'], isTrue);
    }, () => client);
  });
}
