import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/design/anim_viewer.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/crystal_fina.dart';

void main() {
  test('native Fina preview uses a new image cache identity', () {
    final api = Api('http://localhost:8765');
    expect(api.animUrl(CrystalFina.spriteId, 'atk'), contains('?presentation=native-fina-9'));
    expect(api.ffbePreview(CrystalFina.spriteId, 'limitatk'), contains('?presentation=native-fina-9'));
    expect(api.animUrl('401001207', 'atk'), 'http://localhost:8765/api/ffbe/anim/401001207/atk.webp');
    expect(api.animUrl(CrystalFina.spriteId, 'atk', nativePreview: false), endsWith('?original=1'));
  });

  testWidgets('the native preview identifies resonance and keeps animation navigation', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SizedBox(width: 420, child: AnimViewer(
      anims: const ['idle', 'atk', 'limitatk'], url: (a) => 'unused/$a', loading: true,
      initial: 'limitatk', caption: CrystalFina.previewCaption, labels: const {'limitatk': 'Resonance'},
    )))));
    expect(find.text(CrystalFina.previewCaption), findsOneWidget);
    expect(find.text('Resonance  3/3'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.chevron_right));
    await tester.pump();
    expect(find.text('Idle  1/3'), findsOneWidget);
  });
}
