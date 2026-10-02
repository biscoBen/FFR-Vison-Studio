import 'dart:convert';

import 'package:ffr_vision_studio/services/api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('changing either testing switch preserves the other persisted setting', () async {
    var settings = <String, dynamic>{'schema': 1, 'maxMr': true, 'practiceBattle': false};
    final client = MockClient((request) async {
      expect(request.url.path, '/api/testing');
      if (request.method == 'PUT') {
        settings = jsonDecode(request.body) as Map<String, dynamic>;
      }
      return http.Response(jsonEncode(settings), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://studio');
      await api.saveTestingPracticeBattle(true);
      expect(settings, {'schema': 1, 'maxMr': true, 'practiceBattle': true});
      await api.saveTestingMaxMr(false);
      expect(settings, {'schema': 1, 'maxMr': false, 'practiceBattle': true});
      expect(await api.testingPracticeBattle(), isTrue);
    }, () => client);
  });

  test('legacy MR settings keep the new practice battle disabled', () async {
    final client = MockClient((_) async => http.Response('{"schema":1,"maxMr":true}', 200));
    await http.runWithClient(() async {
      expect(await Api('http://studio').testingPracticeBattle(), isFalse);
    }, () => client);
  });
}
