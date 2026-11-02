import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:url_launcher/url_launcher.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../services/tablet_shards.dart';

class TabletShardsScreen extends StatefulWidget {
  const TabletShardsScreen({
    super.key,
    this.gameRoot,
    this.findSaves,
    this.loadSave,
    this.pickSave,
  });
  final String? gameRoot;
  final Future<List<TabletSaveFile>> Function(String?)? findSaves;
  final Future<TabletSave> Function(String)? loadSave;
  final Future<String?> Function()? pickSave;
  @override
  State<TabletShardsScreen> createState() => _TabletShardsScreenState();
}

class _TabletShardsScreenState extends State<TabletShardsScreen> {
  List<TabletShard> _shards = [];
  List<TabletSaveFile> _files = [];
  final _manualPaths = <String>{};
  String? _path, _error;
  TabletSave? _save;
  bool _busy = true, _onlyMissing = true, _showUnvisited = false;
  int? _chapter;
  int _request = 0;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    final request = ++_request;
    setState(() {
      _busy = true;
      _error = null;
      _save = null;
    });
    try {
      final shards = _shards.isEmpty ? await TabletShard.bundled() : _shards;
      final files =
          await (widget.findSaves?.call(widget.gameRoot) ??
              findTabletSaves(gameRoot: widget.gameRoot));
      for (final file in _files.where((f) => _manualPaths.contains(f.path))) {
        if (!files.any((f) => f.path == file.path)) {
          files.add(file);
        }
      }
      if (!mounted || request != _request) {
        return;
      }
      final path = files.any((f) => f.path == _path)
          ? _path
          : files.firstOrNull?.path;
      setState(() {
        _shards = shards;
        _files = files;
        _path = path;
      });
      if (path != null) {
        final save = await (widget.loadSave ?? readTabletSave)(path);
        if (!mounted || request != _request) {
          return;
        }
        setState(() {
          _save = save;
        });
      }
    } catch (e) {
      if (mounted && request == _request) {
        setState(() {
          _error = _message(e);
        });
      }
    } finally {
      if (mounted && request == _request) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  String _message(Object e) => e is TabletSaveException
      ? e.message
      : e is FileSystemException
      ? 'The save could not be opened. Check that the file is accessible, then try Refresh or choose another save.'
      : 'The shard check could not finish. Try Refresh or choose another save.';

  Future<void> _read(String path) async {
    final request = ++_request;
    setState(() {
      _busy = true;
      _error = null;
      _save = null;
      _path = path;
      _chapter = null;
    });
    try {
      final save = await (widget.loadSave ?? readTabletSave)(path);
      if (mounted && request == _request) {
        setState(() {
          _save = save;
        });
      }
    } catch (e) {
      if (mounted && request == _request) {
        setState(() {
          _error = _message(e);
        });
      }
    } finally {
      if (mounted && request == _request) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  Future<void> _choose() async {
    try {
      final path = widget.pickSave != null
          ? await widget.pickSave!()
          : (await FilePicker.platform.pickFiles(
              type: FileType.custom,
              allowedExtensions: ['sav'],
              dialogTitle: 'Choose a Resonance save',
              initialDirectory: _path == null ? null : p.dirname(_path!),
            ))?.files.single.path;
      if (path == null || !mounted) {
        return;
      }
      if (!_files.any((f) => f.path == path)) {
        _manualPaths.add(path);
        setState(() {
          _files = [..._files, TabletSaveFile(path, DateTime.now())];
        });
      }
      await _read(path);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = _message(e);
        });
      }
    }
  }

  String _date(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')} '
      '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

  String _metadata(TabletSave save) {
    final parts = <String>[];
    if (save.savedTicks > 621355968000000000) {
      try {
        parts.add(
          'Saved ${_date(DateTime.fromMicrosecondsSinceEpoch((save.savedTicks - 621355968000000000) ~/ 10, isUtc: true).toLocal())}',
        );
      } on ArgumentError {
        /* Unsupported timestamps do not affect the shard records. */
      }
    }
    if (save.playSeconds.isFinite && save.playSeconds > 0) {
      final minutes = save.playSeconds ~/ 60;
      parts.add(
        'Play time ${minutes ~/ 60}:${(minutes % 60).toString().padLeft(2, '0')}',
      );
    }
    return parts.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final save = _save;
    final found = save == null
        ? 0
        : _shards
              .where((s) => save.status(s) == TabletShardStatus.collected)
              .length;
    final unvisited = save == null
        ? 0
        : _shards
              .where((s) => save.status(s) == TabletShardStatus.unvisited)
              .length;
    final missing = _shards.length - found - unvisited;
    final visible =
        save?.visible(
          _shards,
          onlyMissing: _onlyMissing,
          showUnvisited: _showUnvisited,
          chapter: _chapter,
        ) ??
        <TabletShard>[];
    final groups = <String, List<TabletShard>>{};
    for (final shard in visible) {
      groups
          .putIfAbsent('${shard.chapter}:${shard.location}', () => [])
          .add(shard);
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Band('Tablet shards'),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  GuideButton(
                    'Choose save',
                    icon: Icons.folder_open,
                    small: true,
                    onPressed: _busy || _shards.isEmpty ? null : _choose,
                  ),
                  const SizedBox(width: 10),
                  GuideButton(
                    'Refresh',
                    icon: Icons.refresh,
                    small: true,
                    onPressed: _busy ? null : _refresh,
                  ),
                  if (_busy)
                    const Padding(
                      padding: EdgeInsets.only(left: 14),
                      child: SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Reads your last written save on this PC. Save in-game, then Refresh. Files are never changed or uploaded.',
                style: Guide.small(),
              ),
              if (_files.isNotEmpty) ...[
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  key: ValueKey('shard-slot-$_path'),
                  initialValue: _path,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Save slot'),
                  items: [
                    for (final file in _files)
                      DropdownMenuItem(
                        value: file.path,
                        child: Tooltip(
                          message: file.path,
                          child: Text(
                            '${file.name} · ${file.folder}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                  ],
                  onChanged: _busy
                      ? null
                      : (value) {
                          if (value != null) {
                            _read(value);
                          }
                        },
                ),
              ],
            ],
          ),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(18),
            children: [
              if (_error != null)
                Box(child: Text(_error!, style: Guide.text(Guide.red))),
              if (!_busy && _error == null && save == null)
                Box(
                  child: Text(
                    'No save slots found. Choose a GameSaveData*.sav file from %LOCALAPPDATA%\\FFRS\\Steam\\<Steam ID>\\.',
                    style: Guide.text(),
                  ),
                ),
              if (save != null) ...[
                Box(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$found / ${_shards.length} collected',
                        key: const Key('shard-total'),
                        style: Guide.h2(),
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: found / _shards.length,
                        color: Guide.gold,
                        backgroundColor: Guide.paper3,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '$missing missing in visited areas · $unvisited in unvisited areas',
                        style: Guide.text(),
                      ),
                      if (_metadata(save).isNotEmpty)
                        Text(_metadata(save), style: Guide.small()),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    ChoiceChip(
                      label: const Text('All chapters'),
                      selected: _chapter == null,
                      onSelected: (_) => setState(() {
                        _chapter = null;
                      }),
                    ),
                    for (var ch = 1; ch <= 8; ch++)
                      Builder(
                        builder: (context) {
                          final chapterShards = _shards
                              .where((s) => s.chapter == ch)
                              .toList();
                          final reached = chapterShards.any(
                            (s) =>
                                save.status(s) != TabletShardStatus.unvisited,
                          );
                          final count = chapterShards
                              .where(
                                (s) =>
                                    save.status(s) ==
                                    TabletShardStatus.collected,
                              )
                              .length;
                          return ChoiceChip(
                            label: Text(
                              'Ch. $ch · ${_showUnvisited || reached ? '$count/${chapterShards.length}' : '?'}',
                            ),
                            selected: _chapter == ch,
                            onSelected: !_showUnvisited && !reached
                                ? null
                                : (_) => setState(() {
                                    _chapter = ch;
                                  }),
                          );
                        },
                      ),
                  ],
                ),
                Wrap(
                  spacing: 22,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Checkbox(
                          key: const Key('shards-only-missing'),
                          value: _onlyMissing,
                          onChanged: (v) => setState(() {
                            _onlyMissing = v!;
                          }),
                        ),
                        const Text('Only missing'),
                      ],
                    ),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Checkbox(
                          key: const Key('shards-show-unvisited'),
                          value: _showUnvisited,
                          onChanged: (v) => setState(() {
                            _showUnvisited = v!;
                            if (!v) {
                              _chapter = null;
                            }
                          }),
                        ),
                        const Text('Show unvisited areas (spoilers)'),
                      ],
                    ),
                  ],
                ),
                if (visible.isEmpty)
                  Text(
                    found == _shards.length
                        ? 'All 99 tablet shards collected.'
                        : 'No shards match these filters. Unvisited areas stay hidden until spoilers are enabled.',
                    style: Guide.text(),
                  ),
                for (final group in groups.values) ...[
                  Box(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Chapter ${group.first.chapter} · ${group.first.location}',
                          style: Guide.h2(),
                        ),
                        const SizedBox(height: 8),
                        for (final shard in group)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 5),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  save.status(shard) ==
                                          TabletShardStatus.collected
                                      ? Icons.check_circle_outline
                                      : save.status(shard) ==
                                            TabletShardStatus.unvisited
                                      ? Icons.explore_outlined
                                      : Icons.diamond_outlined,
                                  color:
                                      save.status(shard) ==
                                          TabletShardStatus.collected
                                      ? Guide.green
                                      : Guide.inkSoft,
                                  size: 18,
                                ),
                                const SizedBox(width: 8),
                                SizedBox(
                                  width: 36,
                                  child: Text(
                                    '#${shard.number}',
                                    style: Guide.num(),
                                  ),
                                ),
                                Expanded(
                                  child: Text(shard.hint, style: Guide.text()),
                                ),
                                const SizedBox(width: 10),
                                Text(switch (save.status(shard)) {
                                  TabletShardStatus.collected => 'Collected',
                                  TabletShardStatus.missing => 'Missing',
                                  TabletShardStatus.unvisited => 'Unvisited',
                                }, style: Guide.small()),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
                if (!_showUnvisited && unvisited > 0)
                  Text(
                    '$unvisited shards are hidden because their areas are not recorded in this save.',
                    style: Guide.small(),
                  ),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  TextButton(
                    onPressed: () => launchUrl(
                      Uri.parse('https://github.com/heydavee/ffr-shard-finder'),
                    ),
                    child: const Text('Shard mapping: heydavee (MIT)'),
                  ),
                  TextButton(
                    onPressed: () => launchUrl(
                      Uri.parse(
                        'https://www.powerpyx.com/final-fantasy-resonance-all-tablet-shard-locations/',
                      ),
                    ),
                    child: const Text('Location guide: PowerPyx'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
