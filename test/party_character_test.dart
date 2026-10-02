import 'dart:io';

import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/services/crystal_fina.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:ffr_vision_studio/screens/home_screen.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'character_config_test.dart' show ConfigApi, profile, clone;

Map<String, dynamic> party({bool replacement = false}) => {
  'key': 'party_1001',
  'id': 1001,
  'jp': 'レイン',
  'en': 'Rain',
  'party': {'version': 1, 'id': 1001},
  if (replacement)
    'ffbe': {'id': '401001207', 'dir': 'units/ffbe/a2', 'source': 'CUSTOM'},
};

class PartyApi extends ConfigApi {
  PartyApi(super.roster);
  @override
  Future<Map<String, dynamic>> partyCharacter(int id) async => party();
}

void main() {
  setUpAll(() async {
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });
  test('party configs retain identity in single and mixed roster saves', () {
    final saved = party(replacement: true);
    expect(CharacterConfig.decode(CharacterConfig.encode(saved)), saved);
    final all = [profile(), saved];
    final restored = CharacterConfig.restoreAll(
      CharacterConfig.decodeAll(CharacterConfig.encodeAll(all)),
      [],
      [null, null],
    );
    expect(restored[1], saved);
    expect(
      CharacterConfig.sameCharacter(saved, {
        ...profile(),
        'ffbe': saved['ffbe'],
      }),
      false,
    );
    expect(
      CharacterConfig.target(saved, [party(), profile()])?['key'],
      'party_1001',
    );
    expect(
      () => CharacterConfig.validate({...saved, 'id': 13501}),
      throwsFormatException,
    );
    expect(
      () => CharacterConfig.validate({
        ...saved,
        'stats': {'Attack': 999},
      }),
      throwsFormatException,
    );
    expect(() => CharacterConfig.restore(saved, [party()]), throwsStateError);
    expect(CharacterConfig.restore(profile(), [saved])['id'], profile()['id']);
  });

  test('party appearance does not reserve the added Crystal Fina vision', () {
    final existing = party(replacement: true)
      ..['ffbe']['id'] = CrystalFina.spriteId;
    expect(
      CrystalFina.instantiate(profile(), [existing])['id'],
      profile()['id'],
    );
  });

  test(
    'opening and reverting a party character preserve unrelated pending edits',
    () async {
      final directory = Directory.systemTemp.createTempSync('party-state-');
      final api = PartyApi([profile()]);
      final app =
          AppState(
              hostBase: 'http://unused',
              appPaths: AppPaths.at(directory.path),
            )
            ..api = api
            ..units = clone(api.roster);
      addTearDown(() {
        app.dispose();
        directory.deleteSync(recursive: true);
      });
      final edited = CharacterConfig.copy(app.units.first as JsonMap)
        ..['stats']['Attack'] = 123;
      app.update(edited);
      await app.editPartyCharacter(1001);
      expect(app.units.first['stats']['Attack'], 123);
      expect(app.selected?['party']['id'], 1001);
      await app.removeUnit('party_1001');
      expect(app.units.length, 1);
      expect(app.units.first['stats']['Attack'], 123);
      await app.loadCharacterConfig(party(), expectedTargetKey: null);
      expect(app.selected?['id'], 1001);
    },
  );

  testWidgets(
    'home separates party characters and their editor has battle controls',
    (tester) async {
      tester.view.physicalSize = const Size(1320, 860);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final directory = Directory.systemTemp.createTempSync('party-home-');
      final app =
          AppState(
              hostBase: 'http://unused',
              appPaths: AppPaths.at(directory.path),
            )
            ..api = PartyApi([party()])
            ..units = [party()]
            ..partyCharacters = [party()];
      addTearDown(() {
        app.dispose();
        directory.deleteSync(recursive: true);
      });
      Widget shell(Widget child) => ChangeNotifierProvider.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(body: child),
        ),
      );
      await tester.pumpWidget(shell(const HomeScreen()));
      await tester.pump();
      expect(find.byKey(const Key('party-characters')), findsOneWidget);
      expect(find.text('RAIN'), findsOneWidget);
      expect(find.text('Battle appearance'), findsOneWidget);
      app.select('party_1001');
      await tester.pumpWidget(shell(const UnitScreen()));
      await tester.pump();
      expect(find.text('Change battle model'), findsOneWidget);
      expect(find.text('Revert to original'), findsOneWidget);
      expect(find.text('MR'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
}
