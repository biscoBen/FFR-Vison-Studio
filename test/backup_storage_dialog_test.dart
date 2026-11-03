import 'package:ffr_vision_studio/screens/backup_storage_dialog.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class BackupApi extends Api {
  BackupApi() : super('http://unused');
  int cleaned = 0;
  String? token;
  bool? automatic;
  bool fail = false;
  final report = <String, dynamic>{
    'token': 'reviewed',
    'backups': 60,
    'backupBytes': 90 * 1024 * 1024 * 1024,
    'reclaimBytes': 84 * 1024 * 1024 * 1024,
    'removeCount': 56,
    'skipped': 1,
    'automatic': false,
  };
  @override
  Future<Map<String, dynamic>> backupStorage() async => report;
  @override
  Future<Map<String, dynamic>> cleanupBackups(
    String reviewedToken, {
    required bool automatic,
  }) async {
    cleaned++;
    token = reviewedToken;
    this.automatic = automatic;
    if (fail) {
      throw ApiException(
        'The backup list changed. Refresh and review cleanup again.',
      );
    }
    return {
      ...report,
      'token': 'new',
      'automatic': automatic,
      'reclaimBytes': 0,
      'removeCount': 0,
      'freedBytes': report['reclaimBytes'],
      'removed': 56,
    };
  }
}

void main() {
  Future<void> show(WidgetTester tester, BackupApi api) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showDialog<void>(
                context: context,
                builder: (_) => BackupStorageDialog(api: api),
              ),
              child: const Text('Storage'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Storage'));
    await tester.pumpAndSettle();
  }

  testWidgets(
    'opening shows recoverable space and protections without deleting; action passes reviewed token',
    (tester) async {
      final api = BackupApi();
      await show(tester, api);
      expect(find.textContaining('90.00 GB'), findsOneWidget);
      expect(find.textContaining('Keeps the latest three'), findsOneWidget);
      expect(api.cleaned, 0);
      await tester.tap(find.byKey(const Key('backup-retention')));
      await tester.tap(find.byKey(const Key('cleanup-backups')));
      await tester.pumpAndSettle();
      expect(api.token, 'reviewed');
      expect(api.automatic, false);
      expect(
        find.text('Freed 84.00 GB from 56 older backups.'),
        findsOneWidget,
      );
      expect(find.text('Save backup limit'), findsOneWidget);
    },
  );

  testWidgets(
    'stale or failed cleanup clears the actionable preview until refresh',
    (tester) async {
      final api = BackupApi()..fail = true;
      await show(tester, api);
      await tester.tap(find.byKey(const Key('cleanup-backups')));
      await tester.pumpAndSettle();
      expect(find.textContaining('list changed'), findsOneWidget);
      expect(
        tester
            .widget<FilledButton>(find.byKey(const Key('cleanup-backups')))
            .onPressed,
        isNull,
      );
      await tester.tap(find.text('Refresh'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FilledButton>(find.byKey(const Key('cleanup-backups')))
            .onPressed,
        isNotNull,
      );
    },
  );
}
