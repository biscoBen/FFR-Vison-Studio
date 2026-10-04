import 'package:ffr_vision_studio/design/studio_title_bar.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:window_manager/window_manager.dart';

void main() {
  testWidgets('caption has readable controls in both themes and sends window actions', (tester) async {
    final calls = <String>[];
    var maximized = false;
    const channel = MethodChannel('window_manager');
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      if (call.method == 'isMaximized') return maximized;
      if (call.method == 'isMinimized') return false;
      if (call.method == 'maximize') maximized = true;
      if (call.method == 'unmaximize') maximized = false;
      return null;
    });
    addTearDown(() => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null));
    for (final brightness in [Brightness.light, Brightness.dark]) {
      await tester.pumpWidget(MaterialApp(
        theme: ThemeData(brightness: brightness),
        builder: (_, child) => StudioWindowFrame(child: child!),
        home: const Scaffold(body: Text('Studio content')),
      ));
      await tester.pumpAndSettle();
      final caption = tester.widget<WindowCaption>(find.byType(WindowCaption));
      expect(caption.brightness, brightness);
      expect(caption.backgroundColor, brightness == Brightness.light
          ? const Color(0xfff3f3f3) : const Color(0xff1c1c1c));
      final buttons = find.byType(WindowCaptionButton);
      expect(buttons, findsNWidgets(3));
      expect(find.text('Studio content'), findsOneWidget);
      await tester.tap(buttons.at(0)); await tester.pumpAndSettle();
      expect(calls, contains('minimize'));
      await tester.tap(buttons.at(1)); await tester.pumpAndSettle();
      expect(calls, contains('maximize'));
      await tester.tap(buttons.at(2)); await tester.pumpAndSettle();
      expect(calls, contains('close'));
    }
  });
}
