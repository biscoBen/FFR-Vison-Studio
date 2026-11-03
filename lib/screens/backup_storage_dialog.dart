import 'package:flutter/material.dart';

import '../services/api.dart';

String backupSize(num bytes) =>
    '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';

class BackupStorageDialog extends StatefulWidget {
  const BackupStorageDialog({super.key, required this.api});
  final Api api;

  @override
  State<BackupStorageDialog> createState() => _BackupStorageDialogState();
}

class _BackupStorageDialogState extends State<BackupStorageDialog> {
  Map<String, dynamic>? _report;
  String? _error;
  String? _result;
  bool _working = false;
  bool _automatic = true;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() {
      _working = true;
      _error = null;
      _report = null;
    });
    try {
      final report = await widget.api.backupStorage();
      if (mounted) {
        setState(() {
          _report = report;
          if (report['configured'] == true) {
            _automatic = report['automatic'] == true;
          }
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _cleanup() async {
    final report = _report;
    if (report == null) {
      return;
    }
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      final result = await widget.api.cleanupBackups(
        report['token'] as String,
        automatic: _automatic,
      );
      if (mounted) {
        setState(() {
          _report = result;
          _result =
              'Freed ${backupSize(result['freedBytes'] as num)} from ${result['removed']} older backups.';
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = '$error';
          _report = null;
        });
      }
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = _report;
    return PopScope(
      canPop: !_working,
      child: AlertDialog(
        title: const Text('Mod backup storage'),
        content: SizedBox(
          width: 510,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_working) const LinearProgressIndicator(),
                if (_error != null)
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                if (_result != null) ...[
                  Text(_result!),
                  const SizedBox(height: 12),
                ],
                if (report != null) ...[
                  Text(
                    '${report['backups']} mod backups use ${backupSize(report['backupBytes'] as num)} for the selected game.',
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Recover ${backupSize(report['reclaimBytes'] as num)} by permanently deleting ${report['removeCount']} older rollback copies.',
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Keeps the latest three rollback copies plus any originals needed by Restore the original game. '
                    'Your character edits, settings, artwork and installed mod are kept.',
                  ),
                  if ((report['skipped'] as num) > 0) ...[
                    const SizedBox(height: 8),
                    const Text(
                      'Some unrecognized backup folders were preserved.',
                    ),
                  ],
                  const SizedBox(height: 8),
                  CheckboxListTile(
                    key: const Key('backup-retention'),
                    contentPadding: EdgeInsets.zero,
                    value: _automatic,
                    onChanged: _working
                        ? null
                        : (value) => setState(() => _automatic = value!),
                    title: const Text(
                      'Maintain this limit after future successful installs',
                    ),
                    subtitle: Text(
                      report['automatic'] == true
                          ? 'Currently enabled.'
                          : 'Enabled when you apply cleanup.',
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'After cleanup, use Install the last build to retry a verified build that could not fit on disk.',
                  ),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: _working ? null : _refresh,
            child: const Text('Refresh'),
          ),
          TextButton(
            onPressed: _working ? null : () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          FilledButton(
            key: const Key('cleanup-backups'),
            onPressed: _working || report == null ? null : _cleanup,
            child: Text(
              report != null && (report['reclaimBytes'] as num) > 0
                  ? 'Free ${backupSize(report['reclaimBytes'] as num)}'
                  : 'Save backup limit',
            ),
          ),
        ],
      ),
    );
  }
}
