import 'dart:io';
import 'package:ffr_vision_studio/services/game_locator.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;

void main() {
  test('Steam scan finds unknown full-game folder names by marker and keeps demo available', () {
    final root = Directory.systemTemp.createTempSync('resonance-libraries-');
    addTearDown(() => root.deleteSync(recursive: true));
    for (final name in ['FINAL FANTASY RESONANCE DEMO', 'New full game name']) {
      final marker = File(p.join(root.path, name, 'FFRS', 'Content', 'Paks', 'FFRS-Windows.utoc'));
      marker.parent.createSync(recursive: true);
      marker.writeAsStringSync('synthetic native marker');
    }
    Directory(p.join(root.path, 'Other game')).createSync();
    final found = GameLocator.candidates(root.path);
    expect(found.map(p.basename), ['New full game name', 'FINAL FANTASY RESONANCE DEMO']);
    expect(GameLocator.isGameRoot(found.first), isTrue);
    expect(GameLocator.candidates(p.join(root.path, 'missing')), isEmpty);
  });
}
