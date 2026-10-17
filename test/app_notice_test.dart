import 'dart:io';

import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late Directory directory;
  setUp(() => directory = Directory.systemTemp.createTempSync('studio-notice-'));
  tearDown(() => directory.deleteSync(recursive: true));

  testWidgets('disposing cancels a pending notice expiry', (tester) async {
    final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
    app.showNotice('Build could not start');
    app.dispose();
    await tester.pump(const Duration(seconds: 7));
    expect(tester.takeException(), isNull);
  });

  testWidgets('repeating a notice restarts its full visible duration', (tester) async {
    final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
    addTearDown(app.dispose);
    app.showNotice('Saved');
    await tester.pump(const Duration(seconds: 3));
    app.showNotice('Saved');
    await tester.pump(const Duration(seconds: 3));
    expect(app.notice, 'Saved');
    await tester.pump(const Duration(seconds: 3));
    expect(app.notice, isNull);
  });
}
