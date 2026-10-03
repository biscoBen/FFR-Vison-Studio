import 'dart:io';

import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/services/crystal_fina.dart';
import 'package:ffr_vision_studio/services/overworld_appearance.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:ffr_vision_studio/screens/home_screen.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/screens/party_portrait.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
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

  test('portable configs keep battle and overworld choices independent', () {
    final saved = party(replacement: true)..['overworld'] = Map<String, dynamic>.from(OverworldAppearance.profile);
    expect(CharacterConfig.decode(CharacterConfig.encode(saved)), saved);
    final all = [profile(), saved];
    expect(CharacterConfig.restoreAll(CharacterConfig.decodeAll(CharacterConfig.encodeAll(all)), [], [null, null])[1], saved);
    for (final value in [null, {'version': 1, 'model': 'a2'}, {'version': 2, 'model': OverworldAppearance.model},
      {...OverworldAppearance.profile, 'path': '../sheet.png'}]) {
      expect(() => CharacterConfig.validate({...saved, 'overworld': value}), throwsFormatException);
    }
    final fieldOnly = CharacterConfig.copy(saved)..remove('ffbe');
    CharacterConfig.validate(fieldOnly);
    expect(CharacterConfig.decode(CharacterConfig.encode(fieldOnly)), fieldOnly);
  });

  test('changing and reverting overworld preserves battle and unrelated pending edits', () async {
    final directory = Directory.systemTemp.createTempSync('party-field-');
    final api = PartyApi([profile(), party(replacement: true)]);
    final paths = AppPaths.at(directory.path);
    final app = AppState(hostBase: 'http://unused', appPaths: paths)..api = api..units = clone(api.roster);
    addTearDown(() { app.dispose(); directory.deleteSync(recursive: true); });
    final edited = CharacterConfig.copy(app.units.first as JsonMap)..['stats']['Attack'] = 123;
    app.update(edited);
    await app.editPartyCharacter(1001, overworld: OverworldAppearance.profile);
    expect(api.roster.first['stats']['Attack'], 123);
    expect(api.roster.last['ffbe'], party(replacement: true)['ffbe']);
    expect(api.roster.last['overworld'], OverworldAppearance.profile);
    final relative = 'units/custom/rain_test';
    final artwork = Directory('${paths.engineDir}/$relative')..createSync(recursive: true);
    for (final name in ['unit_anime_304000107.png', 'unit_cgg_304000107.csv']) {
      File('${artwork.path}/$name').writeAsStringSync('cached artwork');
    }
    await app.editPartyCharacter(1001, appearance: {'ffbe': {'id': '304000107', 'dir': relative, 'source': 'CUSTOM'}});
    expect(api.roster.last['overworld'], OverworldAppearance.profile);
    await app.editPartyCharacter(1001, clearOverworld: true);
    expect(api.roster.last.containsKey('overworld'), isFalse);
    expect(api.roster.last['ffbe']['id'], '304000107');
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
      expect(find.byType(PartyPortrait), findsOneWidget);
      expect(tester.widget<Image>(find.descendant(of: find.byType(PartyPortrait), matching: find.byType(Image))).image,
        const AssetImage('assets/party_portraits/100000107.png'));
      app.select('party_1001');
      await tester.pumpWidget(shell(const UnitScreen()));
      await tester.pump();
      expect(find.text('Change battle model'), findsOneWidget);
      expect(find.text('Edit overworld appearance'), findsOneWidget);
      expect(find.text('Revert to original'), findsOneWidget);
      expect(find.text('MR'), findsNothing);
      expect(find.byType(PartyPortrait), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('successive party model changes refresh the portrait without reverting', (tester) async {
    tester.view.physicalSize = const Size(1320, 860);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final directory = Directory.systemTemp.createTempSync('party-portrait-');
    final paths = AppPaths.at(directory.path);
    final api = PartyApi([]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths)
      ..api = api
      ..partyCharacters = [party()];
    addTearDown(() { app.dispose(); directory.deleteSync(recursive: true); });
    await tester.pumpWidget(ChangeNotifierProvider.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: HomeScreen()))));
    await tester.pumpAndSettle();
    expect(find.byType(PartyPortrait), findsOneWidget);

    Future<NetworkImage> replace(String form) async {
      final relative = 'units/custom/portrait_$form';
      final artwork = Directory('${paths.engineDir}/$relative')..createSync(recursive: true);
      for (final name in ['unit_anime_$form.png', 'unit_cgg_$form.csv']) {
        File('${artwork.path}/$name').writeAsStringSync('cached artwork');
      }
      await tester.runAsync(() => app.editPartyCharacter(1001, appearance: {
        'ffbe': {'id': form, 'dir': relative, 'source': 'CUSTOM'},
      }));
      await tester.pumpAndSettle();
      final portrait = tester.widget<Image>(find.descendant(
        of: find.byType(PixelImage), matching: find.byType(Image))).image as NetworkImage;
      expect(Uri.parse(portrait.url).path, '/api/spec/party_1001/icon/face');
      expect(api.roster.single['id'], 1001);
      expect(api.roster.single['ffbe']['id'], form);
      return portrait;
    }

    final first = await replace('401001207');
    final cardImage = tester.element(find.byType(PixelImage));
    final second = await replace('304000107');
    expect(tester.element(find.byType(PixelImage)), same(cardImage));
    expect(second, isNot(first)); // A different provider cannot reuse the old cached portrait.
    expect(api.saves, 2);
    expect(find.byType(PartyPortrait), findsNothing);
    expect(await replace('401001207'), first); // Returning to a form can reuse its own cached image.
    await tester.runAsync(() => app.removeUnit('party_1001'));
    await tester.pumpAndSettle();
    expect(find.byType(PartyPortrait), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
