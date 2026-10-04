import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/overworld_appearance.dart';
import 'package:ffr_vision_studio/services/overworld_catalog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Dart and engine share the audited catalog and every portable choice roundtrips', () {
    expect(
      overworldCatalog,
      json.decode(
        File('assets/existing_visions/payload/overworld_catalog.json')
            .readAsStringSync(),
      ),
    );
    for (final model in OverworldAppearance.models.keys) {
      final profile = OverworldAppearance.profileFor(model);
      expect(OverworldAppearance.valid(profile), isTrue);
      final party = {
        'key': 'party_1002',
        'id': 1002,
        'jp': 'ラスウェル',
        'en': 'Lasswell',
        'party': {'version': 1, 'id': 1002},
        'overworld': profile,
      };
      expect(
        CharacterConfig.decode(CharacterConfig.encode(party))['overworld'],
        profile,
      );
      expect(
        OverworldAppearance.valid({...profile, 'path': '../other.png'}),
        isFalse,
      );
    }
  });

  test('all normal images and directional sheets are bundled with verified checksums', () async {
    for (final model in OverworldAppearance.models.keys) {
      expect(await OverworldAppearance.assetBytes(model, 'icon'), isNotEmpty);
      expect(await OverworldAppearance.assetBytes(model, 'sheet'), isNotEmpty);
    }
    expect(OverworldAppearance.data('lasswell')['directions'], 4);
    expect(OverworldAppearance.data('vagrant_knight_rain')['directions'], 8);
  });
}
