import 'dart:convert';

import 'package:ffr_vision_studio/services/api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('treasure radar installs independently of builds and testing settings', () async {
    var enabled = false;
    final client = MockClient((request) async {
      expect(request.url.path, '/api/minimap-treasure');
      if (request.method == 'PUT') {
        final value = jsonDecode(request.body) as Map;
        expect(value['game'], r'D:\steam\steamapps\common\FINAL FANTASY RESONANCE');
        enabled = value['enabled'] as bool;
      }
      return http.Response(jsonEncode({'available': true, 'enabled': enabled}), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://studio');
      expect((await api.minimapTreasure())['enabled'], false);
      expect((await api.setMinimapTreasure(true, r'D:\steam\steamapps\common\FINAL FANTASY RESONANCE'))['enabled'], true);
      expect((await api.setMinimapTreasure(false, r'D:\steam\steamapps\common\FINAL FANTASY RESONANCE'))['enabled'], false);
    }, () => client);
  });
}
