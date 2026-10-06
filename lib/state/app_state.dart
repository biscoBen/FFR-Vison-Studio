import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;

import '../services/api.dart';
import '../services/acquisition_locations.dart';
import '../services/acquisition.dart';
import '../services/bundled_features.dart';
import '../services/character_config.dart';
import '../services/crystal_fina.dart';
import '../services/downloader.dart';
import '../services/engine.dart';
import '../services/game_locator.dart';
import '../services/paths.dart';
import '../services/sephira_visions.dart';
import '../services/sprite_cache.dart';
import '../version.dart';
import 'catalog_helpers.dart';

/// Where the app is in its life: bootstrapping (downloads + engine), first-run setup, or ready.
enum Phase { boot, setup, ready, failed }

class Progress {
  Progress(this.label, {this.state = 'waiting', this.fraction, this.detail});
  final String label;
  String state; // waiting | working | done | failed
  double? fraction;
  String? detail;
}

/// Loose-typed views over the engine's JSON documents.
typedef JsonMap = Map<String, dynamic>;

class AppState extends ChangeNotifier {
  AppState({required this.hostBase, AppPaths? appPaths, BundledFeatures? bundledFeatures})
      : paths = appPaths ?? AppPaths.resolve(), features = bundledFeatures ?? BundledFeatures() { _loadSettings(); _afterUpdate(); }
  final String hostBase;
  final AppPaths paths;
  late final acquisitionLocations = AcquisitionLocations(file: File(p.join(paths.root, 'acquisition-caves.json')));
  final BundledFeatures features;
  late final Downloader dl = Downloader(hostBase);
  late final SpriteCache _sprites = SpriteCache(paths, dl);
  Engine? engine;
  Api? api;

  Phase phase = Phase.boot;
  String? fatal;
  final bootSteps = <Progress>[
    Progress('Download the engine'),
    Progress('Download the game-side data'),
    Progress('Download the Brave Exvius tables'),
    Progress('Download the unit icons'),
    Progress('Start the engine'),
  ];
  String? gameRoot;
  bool gameRunning = false;
  bool modInstalled = false;
  bool testingMaxMr = false;
  bool testingPracticeBattle = false;
  bool crystalCave = false;
  bool fieldLeader = false;
  bool dark = false; // the night edition of the guide
  bool sephiraEnabled = false;
  bool sephiraInitialized = false;
  bool sephiraWorking = false;
  String? sephiraProgress;
  List<JsonMap> sephiraPresets = [];
  List<JsonMap> get sephiraUnits => units.cast<JsonMap>().where(SephiraVisions.member).toList();
  int get includedUnitCount => units.cast<JsonMap>().where(SephiraVisions.included).length;
  final Map<String, List<String>> _anims = {};
  int backups = 0;
  int placed = 0;
  Progress? setupProgress;
  final setupLog = <String>[];

  JsonMap? manifest;
  JsonMap? hostIndex; // ffbe/index.json: units + forms with packs
  JsonMap? catalog;
  List<dynamic> units = [];
  String? selectedKey;
  bool dirty = false;
  JsonMap? buildState; // /api/build/log
  Timer? _buildTimer;
  Timer? _statusTimer;
  String? notice; // one-line message in the header for a few seconds
  String? banner; // a standing message (offline, old app); shown until the situation changes
  String? updateAvailable; // "1.0.0 build 5" when the host has a newer app
  bool engineDown = false; // the engine process ended on its own
  bool updating = false;
  String? updateStep;
  String? engineVersion;
  bool _stopping = false;

  JsonMap? get selected => units.cast<JsonMap?>().firstWhere((u) => u?['key'] == selectedKey, orElse: () => null);
  List<dynamic> nativeVisions = [];
  List<dynamic> partyCharacters = [];
  String get logsDir => p.join(paths.root, 'logs');
  String get downloadPage => hostBase.endsWith('/') ? hostBase : '$hostBase/';

  // ---------------------------------------------------------------- boot
  Future<void> boot() async {
    try {
      // Find the game first so the folder is already filled in while the packs download.
      if (!isTestBuild && gameRoot == null) GameLocator.detect().then((g) { if (g != null && gameRoot == null) { gameRoot = g; notifyListeners(); } });
      final installed = _readInstalled();
      final haveEngine = installed['engine'] != null && File(paths.engineExe).existsSync();
      JsonMap? man;
      String? why;
      try { man = await dl.manifest(); } catch (e) { why = e.toString(); }

      if (man == null) {
        // Offline (or the host is down): run what is installed.
        if (!haveEngine) throw StateError('Could not reach the download host ($why) and nothing is installed yet. Check the connection and try again.');
        _markInstalled(installed);
        banner = 'Could not reach the download host. Running the installed version; updates are checked next start.';
      } else {
        manifest = man;
        final tag = man['version'].toString();
        final minApp = (man['minApp'] ?? '').toString();
        if (!isTestBuild && compareTags(tag, appTag) > 0 && (man['packs'] as JsonMap?)?['app'] != null) {
          updateAvailable = man['displayVersion'] != null ? '${man['displayVersion']} build ${man['build']}' : tag;
        }
        final tooNew = minApp.isNotEmpty && compareTags(minApp, appTag) > 0;
        if (tooNew) {
          // The host's engine needs a newer app than this one. Keep what is installed rather than mixing versions.
          if (!haveEngine) throw StateError(isTestBuild ? 'This test build needs an update before it can use the latest packs. Close Studio and reopen the Sephira Studio Test shortcut.' : 'This copy of the app ($appLabel) is older than the packs on the host. Download the new app from $downloadPage.');
          _markInstalled(installed);
          banner = isTestBuild ? 'The latest packs need a newer test build. Close Studio and reopen the Sephira Studio Test shortcut to check; the installed packs keep working.' : 'A newer version is on the host and needs the new app. Press Update now, or download it from the page; this copy keeps working as it is.';
        } else {
          final packs = man['packs'] as JsonMap;
          // A pack carries its own version when its content is older than the manifest (it did not change in this build):
          // what is installed under that version is kept, so a new build only downloads what actually changed.
          Future<void> pack(int step, String name, String into, {bool optional = false}) async {
            final info = packs[name] as JsonMap?;
            final s = bootSteps[step];
            if (info == null) {
              if (optional) { s.state = 'done'; s.detail = 'not on this host'; notifyListeners(); return; }
              throw StateError('the host has no "$name" pack');
            }
            final ptag = (info['version'] ?? tag).toString();
            if (installed[name] == ptag && Directory(into).existsSync()) {
              s.state = 'done'; s.detail = 'version ${_pretty(ptag)}'; notifyListeners(); return;
            }
            s.state = 'working'; notifyListeners();
            final dest = p.join(paths.downloads, p.basename(info['url'] as String));
            final f = await dl.download(info['url'] as String, dest, sha256: info['sha256'] as String?, onProgress: (got, total) {
              s.fraction = total > 0 ? got / total : null;
              s.detail = '${(got / 1048576).toStringAsFixed(0)} MB';
              notifyListeners();
            });
            s.detail = 'unpacking'; s.fraction = null; notifyListeners();
            await Downloader.unzip(f, into);
            installed[name] = ptag; _writeInstalled(installed);
            s.state = 'done'; s.detail = 'version ${_pretty(ptag)}'; notifyListeners();
          }
          await pack(0, 'engine', paths.engineDir);
          await pack(1, 'base', paths.engineData);
          await pack(2, 'tables', p.join(paths.engineData, 'ffbe'));
          await pack(3, 'icons', paths.icons, optional: true);
        }
        try {
          hostIndex = await dl.json_('ffbe/index.json');
          File(p.join(paths.root, 'ffbe_index_cache.json')).writeAsStringSync(json.encode(hostIndex));
        } catch (_) {}
      }
      if (hostIndex == null) {
        try { hostIndex = json.decode(File(p.join(paths.root, 'ffbe_index_cache.json')).readAsStringSync()) as JsonMap; } catch (_) {}
      }
      await _startEngine(bootSteps[4]);
      if (_stopping) return;
      if (!isTestBuild) gameRoot ??= await GameLocator.detect();
      final st = await api!.status();
      phase = (st['setupNeeded'] == true) ? Phase.setup : Phase.ready;
      if (phase == Phase.ready) await loadAll();
      _statusTimer = Timer.periodic(const Duration(seconds: 8), (_) => refreshStatus());
    } catch (e) {
      if (_stopping) return;
      final working = bootSteps.where((s) => s.state == 'working');
      for (final s in working) { s.state = 'failed'; s.detail = e.toString(); }
      fatal = e.toString();
      phase = Phase.failed;
    }
    notifyListeners();
  }

  String _pretty(String tag) {
    final parts = tag.split('.');
    return parts.length == 4 ? '${parts.take(3).join('.')} build ${parts[3]}' : tag;
  }

  void _markInstalled(Map<String, dynamic> installed) {
    for (final (i, name) in ['engine', 'base', 'tables', 'icons'].indexed) {
      bootSteps[i].state = 'done';
      bootSteps[i].detail = installed[name] == null ? (name == 'icons' ? 'not downloaded yet' : '?') : 'installed ${_pretty(installed[name].toString())}';
    }
    notifyListeners();
  }

  Future<void> _startEngine(Progress s) async {
    s.state = 'working'; s.detail = null; notifyListeners();
    await engine?.stop();
    s.detail = 'Preparing bundled units'; notifyListeners();
    await features.prepareEngine(paths, engineRunning: engine?.running ?? false);
    final day = DateTime.now().toIso8601String().substring(0, 10);
    engine = Engine(
      paths.engineExe,
      logPath: p.join(logsDir, 'engine-$day.log'),
      logDir: logsDir,
      header: ['app $appLabel', if (appCommit.isNotEmpty) 'commit $appCommit', 'host $hostBase', 'engine ${File(paths.engineExe).path}'],
      onExit: (code) {
        engineDown = true;
        api = null;
        notifyListeners();
      },
    );
    await engine!.start();
    api = Api(engine!.baseUrl);
    _anims.clear();
    engineDown = false;
    s.state = 'done'; s.detail = 'port ${engine!.port}'; notifyListeners();
    await refreshStatus();
  }

  /// After the engine stopped on its own: start it again and reload everything.
  Future<void> restartEngine() async {
    try {
      await _startEngine(bootSteps[4]);
      if (_stopping) return;
      if (phase == Phase.ready) await loadAll();
      showNotice('The engine is back.');
    } catch (e) {
      showNotice('The engine could not be restarted: $e');
    }
  }

  Map<String, dynamic> _readInstalled() {
    try { return json.decode(File(paths.installedManifest).readAsStringSync()) as Map<String, dynamic>; } catch (_) { return {}; }
  }
  void _writeInstalled(Map<String, dynamic> m) => File(paths.installedManifest).writeAsStringSync(json.encode(m));

  Future<void> refreshStatus() async {
    if (api == null) return;
    try {
      final st = await api!.status();
      gameRunning = st['gameRunning'] == true;
      modInstalled = st['modInstalled'] == true;
      backups = (st['backups'] as num?)?.toInt() ?? 0;
      placed = (st['placed'] as num?)?.toInt() ?? 0;
      gameRoot = (st['gameRoot'] as String?) ?? gameRoot;
      engineVersion = st['engineVersion']?.toString();
      // a preparation that lost a table (interrupted, or a dump that failed) shows up here: go back to the setup page
      if (st['setupNeeded'] == true && phase == Phase.ready && setupProgress?.state != 'working') { phase = Phase.setup; setupProgress = null; }
      notifyListeners();
    } catch (_) {
      if (engine != null && !engine!.running && !_stopping) { engineDown = true; notifyListeners(); }
    }
  }

  /// Opens the folder with the engine logs in Explorer.
  Future<void> openLogs() async {
    Directory(logsDir).createSync(recursive: true);
    try { await Process.start('explorer.exe', [logsDir]); } catch (_) {}
  }

  // ---------------------------------------------------------------- first-run setup
  Future<void> runSetup(String game) async {
    setupProgress = Progress('Preparing the game\'s data', state: 'working');
    setupLog.clear();
    notifyListeners();
    try {
      await api!.setup(game);
      while (true) {
        await Future<void>.delayed(const Duration(seconds: 1));
        final l = await api!.setupLog();
        final lines = (l['log'] as List).cast<String>();
        setupLog..clear()..addAll(lines);
        setupProgress!.detail = lines.isEmpty ? null : lines.last;
        notifyListeners();
        if (l['running'] != true) {
          if (l['result'] == 'ok') {
            setupProgress!.state = 'done';
            if (_stopping) return;
            phase = Phase.ready;
            await loadAll();
          } else {
            setupProgress!.state = 'failed';
            setupProgress!.detail = lines.isEmpty ? 'the preparation did not finish' : lines.last;
          }
          break;
        }
      }
    } catch (e) {
      setupProgress!.state = 'failed';
      setupProgress!.detail = e.toString();
    }
    notifyListeners();
  }

  // ---------------------------------------------------------------- data
  Future<void> loadAll() async {
    catalog = await api!.catalog();
    units = await api!.spec();
    sephiraPresets = await SephiraVisions.bundled;
    if (sephiraUnits.isNotEmpty) {
      sephiraInitialized = true;
      sephiraEnabled = sephiraUnits.any(SephiraVisions.included);
    }
    units = units.map((u) {
      final migrated = CharacterConfig.retireComparisonAbilities(u as JsonMap);
      if (!identical(migrated, u)) dirty = true;
      return migrated;
    }).toList();
    try { testingMaxMr = await api!.testingMaxMr(); }
    catch (e) { notice = 'Could not load vision testing settings: $e'; }
    try { testingPracticeBattle = await api!.testingPracticeBattle(); }
    catch (e) { notice = 'Could not load shop battle testing settings: $e'; }
    try { crystalCave = await api!.crystalCave(); }
    catch (e) { notice = 'Could not load Crystal Fina cave settings: $e'; }
    try { fieldLeader = await api!.fieldLeader(); }
    catch (e) { notice = 'Could not load field leader settings: $e'; }
    try { nativeVisions = await api!.nativeVisions(); }
    catch (e) { notice = 'Could not load the original game visions: $e'; }
    try { partyCharacters = await api!.partyCharacters(); }
    catch (e) { notice = 'Could not load the party characters: $e'; }
    if (catalog?['ffbeResonance'] != null) {
      units = units.map((u) {
        final upgraded = migrateCgResonance(u as JsonMap);
        if (!identical(upgraded, u)) dirty = true;
        return upgraded;
      }).toList();
    }
    if (dirty) _saveSoon();
    await refreshStatus();
    notifyListeners();
  }

  void select(String? key) { selectedKey = key; notifyListeners(); }

  void update(JsonMap unit) {
    units = units.map((u) => (u as JsonMap)['key'] == unit['key'] ? unit : u).toList();
    dirty = true;
    _pendingEdits[unit['key'] as String] = unit;
    _rosterRevision++;
    notifyListeners();
    _saveSoon();
  }

  Timer? _saveTimer;
  Future<void> _rosterQueue = Future<void>.value();
  final _pendingEdits = <String, JsonMap>{};
  int _rosterRevision = 0;

  Future<T> _withRoster<T>(Future<T> Function() action) {
    final result = _rosterQueue.then((_) => action());
    _rosterQueue = result.then<void>((_) {}, onError: (Object error, StackTrace stack) {});
    return result;
  }

  List<dynamic> _mergePending(List<dynamic> remote) => remote.map((unit) => _pendingEdits[(unit as Map)['key']] ?? unit).toList();

  Future<void> _savePending() async {
    while (dirty && api != null) {
      final revision = _rosterRevision;
      final snapshot = json.decode(json.encode(units)) as List;
      await api!.saveSpec(snapshot);
      if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    }
  }
  void _saveSoon() {
    _saveTimer?.cancel();
    _saveTimer = Timer(const Duration(milliseconds: 700), save);
  }

  Future<void> save() async {
    try { await _withRoster(_savePending); notice = null; } catch (e) { notice = 'Could not save: $e'; }
    notifyListeners();
  }

  Future<void> removeAcquisitionCave(String id) => _withRoster(() async {
    if (building) { throw StateError('Wait for the current build to finish.'); }
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (acquisitionLocations.cave(id) == null) return;
    final catalog = await AcquisitionCatalog.bundled;
    await _savePending();
    if (id == 'crystal_cave' && crystalCave) {
      await api!.saveCrystalCave(false);
      crystalCave = false;
      notifyListeners();
    }
    await acquisitionLocations.remove(id);
    for (final unit in units.cast<JsonMap>().toList()) {
      final saved = unit[Acquisition.field];
      if (!Acquisition.valid(saved)) continue;
      final preferences = Acquisition.fromJson(saved as Map);
      if (preferences.location != id &&
          !(id == 'crystal_cave' && preferences.location == 'earth_shrine')) { continue; }
      update({...unit, Acquisition.field: preferences.choose(catalog.vendor(catalog.mitraShop)!).toJson()});
    }
    _saveTimer?.cancel();
    await _savePending();
  });

  Future<void> updateAcquisitionCave(CaveLocation cave) => _withRoster(() async {
    if (building) { throw StateError('Wait for the current build to finish.'); }
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    CaveLocation.fromJson(cave.toJson());
    final previous = acquisitionLocations.cave(cave.id);
    if (previous == null) { throw StateError('This cave was removed.'); }
    await _savePending();
    final catalog = await AcquisitionCatalog.bundled;
    await acquisitionLocations.update(cave);
    // Move the old opt-in Fina assignment to an explicit snapshot before editing.
    if (cave.id == 'crystal_cave' && crystalCave) {
      try {
        await api!.saveCrystalCave(false);
      } catch (_) {
        await acquisitionLocations.update(previous);
        rethrow;
      }
      crystalCave = false;
      for (final unit in units.cast<JsonMap>().where((u) => CrystalFina.matches(u))) {
        final saved = unit[Acquisition.field];
        final preferences = Acquisition.valid(saved)
            ? Acquisition.fromJson(saved as Map)
            : const Acquisition(location: 'crystal_cave');
        update({...unit, Acquisition.field: preferences.choose(cave.site, cave: cave.toJson()).toJson()});
      }
    }
    for (final unit in units.cast<JsonMap>().toList()) {
      final saved = unit[Acquisition.field];
      if (!Acquisition.valid(saved)) continue;
      final preferences = acquisitionLocations.migrate(Acquisition.fromJson(saved as Map), catalog);
      if (preferences.location != cave.id) continue;
      update({...unit, Acquisition.field: preferences.choose(cave.site, cave: cave.toJson()).toJson()});
    }
    _saveTimer?.cancel();
    await _savePending();
  });

  Future<bool> removeUnit(String key) => _withRoster(() async {
    try {
      if (building) { throw StateError('Wait for the current build to finish.'); }
      if (crystalCave && units.any((u) => u['key'] == key && CrystalFina.matches(u as Map))) {
        throw StateError('Turn off Crystal Fina cave before removing her profile.');
      }
      await _savePending();
      await api!.deleteUnit(key);
      _pendingEdits.remove(key);
      units = _mergePending(await api!.spec());
      await _savePending();
      if (selectedKey == key) selectedKey = null;
      notifyListeners();
      return true;
    } catch (e) {
      showNotice('Could not remove the unit: $e');
      return false;
    }
  });

  /// All artwork and ID allocation are prepared before changing the roster.
  /// Enabling a previously initialized collection preserves edits and removals.
  Future<void> setSephiraEnabled(bool value) => _withRoster(() async {
    _checkSephiraChange();
    _saveTimer?.cancel();
    await _savePending();
    var next = _mergePending(await api!.spec());
    try {
      sephiraWorking = true;
      notifyListeners();
      if (value && !sephiraInitialized) next = await _prepareSephira(next);
      next = next.map((u) => SephiraVisions.member(u as Map)
          ? SephiraVisions.setEnabled(u as JsonMap, value) : u).toList();
      await _commitSephira(next, enabled: value);
    } finally {
      sephiraWorking = false;
      sephiraProgress = null;
      notifyListeners();
    }
  });

  Future<void> restoreSephira({String? presetId, bool reset = false}) => _withRoster(() async {
    _checkSephiraChange();
    _saveTimer?.cancel();
    await _savePending();
    try {
      sephiraWorking = true;
      notifyListeners();
      final current = _mergePending(await api!.spec());
      final next = await _prepareSephira(current, presetId: presetId, reset: reset);
      if (reset && current.isNotEmpty) {
        final backup = File(p.join(paths.configBackups, 'sephira-${DateTime.now().microsecondsSinceEpoch}.json'));
        await backup.parent.create(recursive: true);
        await backup.writeAsString(CharacterConfig.encodeAll(current), flush: true);
      }
      await _commitSephira(next, enabled: sephiraEnabled);
    } finally {
      sephiraWorking = false;
      sephiraProgress = null;
      notifyListeners();
    }
  });

  void _checkSephiraChange() {
    if (building) throw StateError('Wait for the current build to finish.');
    if (api == null || engineDown) throw StateError('The engine is not running.');
  }

  Future<List<dynamic>> _prepareSephira(List<dynamic> current, {String? presetId, bool reset = false}) async {
    if (sephiraPresets.isEmpty) sephiraPresets = await SephiraVisions.bundled;
    final existing = {for (final u in current.cast<JsonMap>().where(SephiraVisions.member)) SephiraVisions.presetId(u): u};
    String? adoptedKey;
    // The cave has one Crystal Fina identity. Adopt an existing custom Fina,
    // retaining her kit, ID and acquisition until an explicit preset reset.
    if (!existing.containsKey('crystal_fina') &&
        (presetId == null || presetId == 'crystal_fina') &&
        sephiraPresets.any((p) => p['id'] == 'crystal_fina')) {
      final candidates = current.cast<JsonMap>().where((u) => u['native'] == null &&
          u['party'] == null && CrystalFina.matches(u) && !SephiraVisions.member(u)).toList();
      if (candidates.length > 1) throw StateError('More than one Crystal Fina is in the roster. Keep one before enabling the collection.');
      if (candidates.isNotEmpty) {
        adoptedKey = candidates.single['key'] as String;
        final adopted = {...candidates.single, SephiraVisions.field:
          {'version': 1, 'preset': 'crystal_fina', 'enabled': sephiraEnabled}};
        existing['crystal_fina'] = adopted;
        current = [for (final u in current) u['key'] == adoptedKey ? adopted : u];
      }
    }
    final wanted = sephiraPresets.where((p) =>
        (presetId == null || p['id'] == presetId) && (reset || !existing.containsKey(p['id']))).toList();
    if (presetId != null && sephiraPresets.every((p) => p['id'] != presetId)) {
      throw StateError('This preset is not in the bundled collection.');
    }
    final unresolved = wanted.where((p) => p['profile'] == null).toList();
    if (unresolved.isNotEmpty) {
      throw StateError('Versions and kits are still being selected for ${unresolved.map((p) => p['name']).join(', ')}.');
    }
    if (wanted.isEmpty) return current;
    final targets = wanted.map((p) => existing[p['id']]).toList();
    final sources = [for (final p in wanted) {
      ...CharacterConfig.copy(p['profile'] as JsonMap),
      SephiraVisions.field: {'version': 1, 'preset': p['id'], 'enabled': sephiraEnabled},
      if (existing[p['id']]?.containsKey(Acquisition.field) == true)
        Acquisition.field: CharacterConfig.copy(existing[p['id']]![Acquisition.field] as JsonMap),
    }];
    final reservedSkills = <int>{
      for (final skill in catalog?['skills'] as List? ?? [])
        if (skill['id'] is num) (skill['id'] as num).toInt(),
    };
    final loaded = CharacterConfig.restoreAll(sources, current, targets, reservedSkillIds: reservedSkills);
    final revision = _rosterRevision;
    for (var i = 0; i < loaded.length; i++) {
      sephiraProgress = 'Preparing ${wanted[i]['name']} (${i + 1}/${loaded.length})';
      notifyListeners();
      await _checkCharacterArtwork(loaded[i]);
    }
    // A reset must never silently overwrite an edit made during preparation.
    if (reset && revision != _rosterRevision) {
      throw StateError('A character changed while preparing presets. Your edits are kept; retry the reset.');
    }
    final replaced = {for (var i = 0; i < loaded.length; i++) if (targets[i] != null) targets[i]!['key']: loaded[i]};
    return [
      for (final u in _mergePending(current)) replaced[u['key']] ??
          (u['key'] == adoptedKey ? {...u as JsonMap, SephiraVisions.field:
            {'version': 1, 'preset': 'crystal_fina', 'enabled': sephiraEnabled}} : u),
      for (var i = 0; i < loaded.length; i++) if (targets[i] == null) loaded[i],
    ];
  }

  Future<void> _commitSephira(List<dynamic> next, {required bool enabled}) async {
    if (next.isNotEmpty) CharacterConfig.validateAll(next);
    final revision = _rosterRevision;
    await api!.saveSpec(CharacterConfig.copy({'units': next})['units'] as List);
    units = _mergePending(next).map((u) => SephiraVisions.member(u as Map)
        ? SephiraVisions.setEnabled(u as JsonMap, enabled) : u).toList();
    if (revision == _rosterRevision) { dirty = false; _pendingEdits.clear(); }
    await _savePending();
    sephiraEnabled = enabled;
    sephiraInitialized = true;
    try {
      final f = File(paths.settingsFile);
      final j = f.existsSync() ? json.decode(await f.readAsString()) as Map : <String, dynamic>{};
      j['sephiraEnabled'] = enabled;
      j['sephiraInitialized'] = true;
      await f.parent.create(recursive: true);
      await f.writeAsString(json.encode(j), flush: true);
    } catch (e) { notice = 'Visions saved; could not save the section setting: $e'; }
    _anims.clear();
  }

  /// The face icon of a unit form, from the icons pack on disk (one download at setup; nothing is fetched per row: the host
  /// answered the old one-request-per-icon pickers with 429s once many people used the app at the same time).
  File iconFile(String form) => File(p.join(paths.icons, '$form.png'));

  /// Download only missing sprite files and let the engine index a repaired pack.
  Future<void> ensureSprites(String form, {void Function(String)? onStep}) async {
    final forms = (hostIndex?['forms'] as JsonMap?) ?? {};
    final info = forms[form] as JsonMap?;
    final changed = await _sprites.ensure(form, info, onStep: onStep);
    if (!changed && _sprites.previewReady(form)) return;
    onStep?.call('indexing');
    await api!.rebuildFfbeIndex();
    _anims.remove(form);
    _sprites.previewMarker(form).writeAsStringSync('1');
  }

  /// Prepare the complete on-demand unit pack before displaying a hosted look.
  /// New packs include the unit record as well as sheets; sheets alone leave the
  /// engine's lightweight picker record with an empty animation list.
  Future<void> prepareUnitPreview(String ffbeId, String form, {void Function(String)? onStep}) async {
    final client = api;
    if (client == null) { throw StateError('The engine is not running.'); }
    JsonMap job;
    try {
      job = await client.prepareAssets(ffbeId, form);
    } on ApiException catch (error) {
      if (error.statusCode != 404 && error.statusCode != 405) { rethrow; }
      // Older engines with complete local FFBE tables use sprite-only packs.
      await ensureSprites(form, onStep: onStep);
      return;
    }
    final id = job['job'];
    if (id is! String || id.isEmpty) { throw StateError('The engine did not start unit preparation.'); }
    final deadline = DateTime.now().add(const Duration(minutes: 10));
    while (true) {
      final progress = await client.assetProgress(id);
      onStep?.call((progress['stage'] ?? 'Preparing unit previews').toString());
      if (progress['state'] == 'done') { _anims.clear(); return; }
      if (progress['state'] == 'failed') { throw StateError((progress['error'] ?? 'Unit preparation failed.').toString()); }
      if (progress['state'] != 'running') { throw StateError('The engine returned an unknown unit preparation status.'); }
      if (DateTime.now().isAfter(deadline)) { throw TimeoutException('Unit preparation took too long. Select the unit again to retry.'); }
      await Future<void>.delayed(const Duration(milliseconds: 250));
    }
  }

  /// Animation names for a form, from the engine, cached.
  Future<List<String>> animsFor(String form) async {
    final c = _anims[form];
    if (c != null) return c;
    final a = await api!.anims(form);
    if (a.isNotEmpty) _anims[form] = a;
    return a;
  }

  /// A restored config may have artwork but no prepared engine preview data.
  /// Repair only this character on opening it, never the full hosted roster.
  Future<List<String>> characterAnims(JsonMap unit) async {
    final form = (unit['ffbe'] as Map?)?['id'] as String?;
    if (form == null) return [];
    final existing = await animsFor(form);
    if (CrystalFina.matches(unit) || unit['ffbe']['source'] == 'CUSTOM') return existing;
    if (existing.isNotEmpty && _sprites.hasSheets(form)) return existing;
    await _checkCharacterArtwork(unit);
    _anims.remove(form);
    return animsFor(form);
  }

  Future<JsonMap> addUnit(String ffbeId, String form, String name, {void Function(String)? onStep}) => _withRoster(() async {
    if (building) { throw StateError('Wait for the current build to finish.'); }
    await _savePending();
    await ensureSprites(form, onStep: onStep);
    onStep?.call('adding to the mod');
    final u = await api!.addUnit(ffbeId, form: form, name: name);
    units = _mergePending(await api!.spec());
    await _savePending();
    selectedKey = u['key'] as String?;
    notifyListeners();
    return u;
  });

  bool get hasCrystalFina => units.any((u) => u['native'] == null && u['party'] == null && CrystalFina.matches(u as Map));

  Future<JsonMap> snapshotCharacter(String key) => _withRoster(() async {
    if (api != null && !engineDown) { await _savePending(); }
    final unit = units.cast<JsonMap>().where((u) => u['key'] == key).firstOrNull;
    if (unit == null) { throw StateError('This character has been removed.'); }
    return CharacterConfig.copy(unit);
  });

  Future<List<JsonMap>> snapshotCharacters() => _withRoster(() async {
    if (api != null && !engineDown) { await _savePending(); }
    return units.cast<JsonMap>().map(CharacterConfig.copy).toList();
  });

  Future<void> _checkCharacterArtwork(JsonMap saved) async {
    if (saved['party'] != null) {
      final original = await api!.partyCharacter(saved['id'] as int);
      if (original['party']?['id'] != saved['party']['id']) { throw StateError('This party character is not available in the prepared game.'); }
      if (saved['ffbe'] == null) { return; }
    }
    if (saved['native'] != null) {
      final original = await api!.nativeVision(saved['id'] as int);
      if (original['native']?['id'] != saved['native']['id']) { throw StateError('This original vision is not available in the prepared game.'); }
      if (saved['ffbe'] == null) { return; }
    }
    if (CrystalFina.matches(saved)) { await features.ensureUnitAssets(paths); }
    final ffbe = saved['ffbe'] as JsonMap;
    final form = ffbe['id'] as String;
    final hosted = ((hostIndex?['units'] as List?) ?? []).cast<JsonMap>().where(
      (u) => (u['packs'] as List? ?? []).map((f) => f.toString()).contains(form),
    ).firstOrNull;
    final base = ffbe['base']?.toString();
    final uid = ffbe['source'] == 'CUSTOM' ? null : hosted?['id']?.toString() ??
        (base != null && RegExp(r'^\d+$').hasMatch(base) &&
         (ffbe['dir'] as String).replaceAll('\\', '/').startsWith('units/ffbe/') ? base : null);
    String directory(String relative) => p.joinAll([paths.engineDir, ...relative.replaceAll('\\', '/').split('/')]);
    bool hasArtwork(String relative, String id) =>
        ['unit_anime_$id.png', 'unit_cgg_$id.csv'].every((name) {
          final file = File(p.join(directory(relative), name));
          return file.existsSync() && file.lengthSync() > 0;
        });
    Future<void> restoreForm(String id, String relative) async {
      if (uid == null) return;
      if (hasArtwork(relative, id) && _sprites.hasSheets(id) && (await api!.anims(id)).isNotEmpty) return;
      await prepareUnitPreview(uid, id);
      final source = Directory(_sprites.directory(id));
      if (!source.existsSync()) return;
      final target = Directory(directory(relative))..createSync(recursive: true);
      for (final file in source.listSync().whereType<File>()) {
        if (p.basename(file.path).startsWith('.')) continue;
        final destination = File(p.join(target.path, p.basename(file.path)));
        // Retain locally edited artwork; restore only missing or empty files.
        if (!destination.existsSync() || destination.lengthSync() == 0) {
          await file.copy(destination.path);
        }
      }
    }
    await restoreForm(form, ffbe['dir'] as String);
    if (ffbe['baseForm'] is String && ffbe['baseDir'] is String && ffbe['baseForm'] != form) {
      await restoreForm(ffbe['baseForm'] as String, ffbe['baseDir'] as String);
      if (!hasArtwork(ffbe['baseDir'] as String, ffbe['baseForm'] as String)) {
        throw StateError('The base-form artwork for ${saved['en']} is missing. Choose its model using Add a unit first, then load its saved config.');
      }
    }
    if (!hasArtwork(ffbe['dir'] as String, form)) {
      throw StateError('The artwork for ${saved['en']} is missing. Add or import this character using Add a unit first, then load its saved config.');
    }
  }

  Future<List<JsonMap>> loadAllCharacterConfigs(List<JsonMap> saved, {required List<String?> expectedTargetKeys}) => _withRoster(() async {
    CharacterConfig.validateAll(saved);
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    _saveTimer?.cancel();
    await _savePending();
    for (final unit in saved) { await _checkCharacterArtwork(unit); }
    await _savePending();
    final current = _mergePending(await api!.spec());
    final targets = CharacterConfig.targets(saved, current);
    if (!listEquals(targets.map((u) => u?['key'] as String?).toList(), expectedTargetKeys)) {
      throw StateError('The roster changed while choosing the file. Load it again to review the characters being restored.');
    }
    final loaded = CharacterConfig.restoreAll(saved, current, targets);
    final backup = File(p.join(paths.configBackups, 'roster-${DateTime.now().microsecondsSinceEpoch}.json'));
    await backup.parent.create(recursive: true);
    await backup.writeAsString(const JsonEncoder.withIndent('  ').convert(current), flush: true);
    final replacements = {for (var i = 0; i < saved.length; i++) if (targets[i] != null) targets[i]!['key']: loaded[i]};
    final next = [
      for (final unit in _mergePending(current)) replacements[unit['key']] ?? unit,
      for (var i = 0; i < loaded.length; i++) if (targets[i] == null) loaded[i],
    ];
    final revision = _rosterRevision;
    await api!.saveSpec(json.decode(json.encode(next)) as List);
    units = _mergePending(next);
    if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    await _savePending();
    _anims.clear();
    selectedKey = null;
    notifyListeners();
    return loaded;
  });

  /// Restore a single spec through the same queue as autosave, remove and build.
  /// The full roster is backed up before replacement, and unrelated edits made
  /// while the request is in flight are merged and saved afterward.
  Future<JsonMap> loadCharacterConfig(JsonMap saved, {required String? expectedTargetKey}) => _withRoster(() async {
    CharacterConfig.validate(saved);
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    _saveTimer?.cancel();
    await _savePending();
    await _checkCharacterArtwork(saved);
    final current = _mergePending(await api!.spec());
    final target = CharacterConfig.target(saved, current);
    if (target?['key'] != expectedTargetKey) { throw StateError('The roster changed while choosing the file. Load it again to review the character being restored.'); }
    final unit = CharacterConfig.restore(saved, current, replacing: target);
    final backup = File(p.join(paths.configBackups, 'roster-${DateTime.now().microsecondsSinceEpoch}.json'));
    await backup.parent.create(recursive: true);
    await backup.writeAsString(const JsonEncoder.withIndent('  ').convert(current), flush: true);
    final next = _mergePending([
      for (final existing in current) if (existing['key'] != target?['key']) existing,
    ]);
    if (target == null) {
      next.add(unit);
    } else {
      // Keep the character's place in the roster when replacing its setup.
      next.insert(current.indexWhere((u) => u['key'] == target['key']), unit);
    }
    final revision = _rosterRevision;
    await api!.saveSpec(json.decode(json.encode(next)) as List);
    units = _mergePending(next);
    if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    await _savePending();
    _anims.clear();
    selectedKey = unit['key'] as String;
    notifyListeners();
    return unit;
  });

  Future<JsonMap> addBundledUnit({void Function(String)? onStep}) => _withRoster(() async {
    if (api == null) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    if (hasCrystalFina) { throw StateError('Crystal Fina is already in your roster.'); }
    _saveTimer?.cancel();
    await _savePending();
    onStep?.call('Preparing Crystal Fina');
    await features.ensureUnitAssets(paths);
    final current = _mergePending(await api!.spec());
    final unit = CrystalFina.instantiate(await features.profile(), current);
    final next = [...current, unit];
    final revision = _rosterRevision;
    onStep?.call('Adding to the mod');
    await api!.saveSpec(json.decode(json.encode(next)) as List);
    units = _mergePending(next);
    if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    await _savePending();
    selectedKey = unit['key'] as String;
    notifyListeners();
    return unit;
  });

  /// Original visions keep their game identity. Merely opening the editor
  /// creates an unchanged snapshot; the builder only applies later differences.
  Future<JsonMap> editNativeVision(int id, {JsonMap? appearance, bool? testAcquire, bool selectEditor = true}) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    _saveTimer?.cancel(); await _savePending();
    final current = _mergePending(await api!.spec());
    final matches = current.where((u) => u['native']?['id'] == id).toList();
    if (matches.length > 1) { throw StateError('This original vision has duplicate overrides.'); }
    final unit = CharacterConfig.copy(matches.isEmpty ? await api!.nativeVision(id) : matches.single as JsonMap);
    if (unit['id'] != id || unit['native']?['id'] != id || current.any((u) => u['id'] == id && u['native'] == null)) {
      throw StateError('This original vision conflicts with a roster entry. Your roster has not been changed.');
    }
    if (appearance != null) {
      unit['ffbe'] = CharacterConfig.copy(appearance['ffbe'] as JsonMap);
      unit['menuScale'] = appearance['menuScale'] ?? 2.52;
      if (appearance['icon'] != null) { unit['icon'] = CharacterConfig.copy(appearance['icon'] as JsonMap); }
      await _checkCharacterArtwork(unit);
    }
    if (testAcquire != null) {
      if (testAcquire) { unit['testAcquire'] = true; } else { unit.remove('testAcquire'); }
    }
    CharacterConfig.validate(unit);
    final next = [for (final u in current) u['native']?['id'] == id ? unit : u, if (matches.isEmpty) unit];
    final revision = _rosterRevision;
    await api!.saveSpec(json.decode(json.encode(next)) as List);
    units = _mergePending(next);
    if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    await _savePending(); if (selectEditor) { selectedKey = unit['key'] as String; } _anims.clear(); notifyListeners();
    return unit;
  });

  Future<void> setTestingMaxMr(bool value) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    await api!.saveTestingMaxMr(value);
    testingMaxMr = value; notifyListeners();
  });

  bool get showUnverifiedSkills => catalogShowsUnverified(catalog ?? {});
  bool get useAbilityChanges => (catalog?['abilityModes'] as Map?)?['useChanges'] == true;

  Future<void> setAbilityModes({bool? showUnverified, bool? useChanges}) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    final value = await api!.saveAbilityModes(
      showUnverified: showUnverified ?? showUnverifiedSkills,
      useChanges: useChanges ?? useAbilityChanges,
    );
    catalog = {...?catalog, 'abilityModes': value};
    notifyListeners();
  });

  Future<void> setTestingPracticeBattle(bool value) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    await api!.saveTestingPracticeBattle(value);
    testingPracticeBattle = value; notifyListeners();
  });

  Future<void> setCrystalCave(bool value) async {
    // The acquired item must refer to the real, currently allocated profile.
    // Use the existing roster allocator and preserve every current edit.
    if (value && !hasCrystalFina) { await addBundledUnit(); }
    await _withRoster(() async {
      if (api == null || engineDown) { throw StateError('The engine is not running.'); }
      if (building) { throw StateError('Wait for the current build to finish.'); }
      await api!.saveCrystalCave(value);
      crystalCave = value; notifyListeners();
    });
  }

  Future<void> setFieldLeader(bool value) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    await api!.saveFieldLeader(value);
    fieldLeader = value; notifyListeners();
  });

  Future<JsonMap> editPartyCharacter(int id, {JsonMap? appearance, JsonMap? overworld, int? battleVoice, bool clearVoice = false, bool clearBattle = false, bool clearOverworld = false}) => _withRoster(() async {
    if (api == null || engineDown) { throw StateError('The engine is not running.'); }
    if (building) { throw StateError('Wait for the current build to finish.'); }
    _saveTimer?.cancel(); await _savePending();
    final current = _mergePending(await api!.spec());
    final matches = current.where((u) => u['party']?['id'] == id).toList();
    if (matches.length > 1) { throw StateError('This party character has duplicate overrides.'); }
    final unit = CharacterConfig.copy(matches.isEmpty ? await api!.partyCharacter(id) : matches.single as JsonMap);
    if (current.any((u) => u['id'] == id && u['party'] == null)) {
      throw StateError('This party character conflicts with a roster entry.');
    }
    if (clearBattle) {
      for (final field in ['ffbe', 'menuScale', 'icon']) { unit.remove(field); }
    } else if (appearance != null) {
      unit['ffbe'] = CharacterConfig.copy(appearance['ffbe'] as JsonMap);
      await _checkCharacterArtwork(unit);
    }
    if (clearOverworld) { unit.remove('overworld'); }
    else if (overworld != null) { unit['overworld'] = CharacterConfig.copy(overworld); }
    if (clearVoice || battleVoice == id) { unit.remove('battleVoice'); }
    else if (battleVoice != null) { unit['battleVoice'] = battleVoice; }
    CharacterConfig.validate(unit);
    final next = [for (final u in current) u['party']?['id'] == id ? unit : u, if (matches.isEmpty) unit];
    final revision = _rosterRevision;
    await api!.saveSpec(json.decode(json.encode(next)) as List);
    units = _mergePending(next);
    if (_rosterRevision == revision) { dirty = false; _pendingEdits.clear(); }
    await _savePending(); selectedKey = unit['key'] as String; _anims.clear(); notifyListeners();
    return unit;
  });

  void useOriginalModel(JsonMap unit) {
    final restored = CharacterConfig.copy(unit);
    final baseline = restored['native']['baseline'] as Map;
    for (final field in ['ffbe', 'menuScale', 'icon']) {
      if (baseline.containsKey(field)) { restored[field] = json.decode(json.encode(baseline[field])); }
      else { restored.remove(field); }
    }
    update(restored); _anims.clear();
  }

  // ---------------------------------------------------------------- self-update
  /// A running exe cannot replace itself, so: stage the new app next to the app data, write a small script that waits for
  /// this process to end, copies the staged folder over the one the exe lives in and starts the new exe, then leave.
  Future<void> updateApp() async {
    if (isTestBuild) {
      showNotice('Close Studio and reopen the Sephira Studio Test shortcut to get test updates.');
      return;
    }
    final info = (manifest?['packs'] as JsonMap?)?['app'] as JsonMap?;
    if (info == null || updating) return;
    final exePath = Platform.resolvedExecutable;
    final exeDir = File(exePath).parent.path;
    try { final t = File(p.join(exeDir, '.write_test')); t.writeAsStringSync('x'); t.deleteSync(); }
    catch (_) { showNotice('The app folder is read-only, so it cannot update itself. Download the new version from the page.'); return; }
    updating = true; updateStep = 'downloading'; notifyListeners();
    try {
      final ver = manifest!['version'].toString();
      final f = await dl.download(info['url'] as String, p.join(paths.downloads, 'app-$ver.zip'), sha256: info['sha256'] as String?, onProgress: (got, total) {
        updateStep = 'downloading ${(got / 1048576).toStringAsFixed(0)} MB'; notifyListeners();
      });
      final staging = p.join(paths.root, 'app-staging', ver);
      if (Directory(staging).existsSync()) Directory(staging).deleteSync(recursive: true);
      updateStep = 'unpacking'; notifyListeners();
      await Downloader.unzip(f, staging);
      final inner = Directory(staging).listSync().whereType<Directory>().toList();
      final src = inner.length == 1 ? inner.first.path : staging;
      if (!File(p.join(src, p.basename(exePath))).existsSync() && !File(p.join(src, 'FFR Vision Studio.exe')).existsSync()) throw StateError('the downloaded app has no executable');
      final newExe = File(p.join(src, p.basename(exePath))).existsSync() ? p.basename(exePath) : 'FFR Vision Studio.exe';
      // The helper is a PowerShell script: it waits for this process to end, copies the staged folder over the exe's folder,
      // starts the new exe and removes itself. It is started through `cmd /c start` because a console child started detached
      // straight from Dart dies with this process (and a cmd script with `tasklist | find` hangs without a console).
      final ps1 = File(p.join(paths.root, 'update.ps1'));
      ps1.writeAsStringSync([
        r'$ErrorActionPreference = "SilentlyContinue"',
        r'$t = 0',
        'while ((Get-Process -Id $pid -ErrorAction SilentlyContinue) -and \$t -lt 120) { Start-Sleep -Seconds 1; \$t++ }',
        'robocopy "$src" "$exeDir" /E /IS /IT /NFL /NDL /NJH /NJS | Out-Null',
        'Remove-Item -Recurse -Force "${p.join(paths.root, 'app-staging')}"',
        'Start-Process -FilePath "${p.join(exeDir, newExe)}" -WorkingDirectory "$exeDir"',
        r'Remove-Item -Force $MyInvocation.MyCommand.Path',
      ].join('\r\n'));
      updateStep = 'restarting'; notifyListeners();
      await Process.start('cmd.exe', ['/c', 'start', '""', '/min', 'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', ps1.path], mode: ProcessStartMode.detached);
      await shutdown();
      exit(0);
    } catch (e) {
      updating = false; updateStep = null;
      showNotice('The update did not go through: $e. The download page has the new version.');
    }
  }

  /// After a self-update: drop the helper and say what happened, once.
  void _afterUpdate() {
    try {
      for (final n in ['update.cmd', 'update.ps1']) { final f = File(p.join(paths.root, n)); if (f.existsSync()) f.deleteSync(); }
      final st = Directory(p.join(paths.root, 'app-staging'));
      if (st.existsSync()) st.deleteSync(recursive: true);
      final f = File(paths.settingsFile);
      final j = f.existsSync() ? json.decode(f.readAsStringSync()) as Map : <String, dynamic>{};
      final last = j['lastRun']?.toString();
      if (last != null && last != appTag) banner = 'Updated to $appLabel.';
      j['lastRun'] = appTag;
      f.writeAsStringSync(json.encode(j));
    } catch (_) {}
  }

  // ---------------------------------------------------------------- settings
  void _loadSettings() {
    try {
      final f = File(paths.settingsFile);
      if (f.existsSync()) {
        final j = json.decode(f.readAsStringSync()) as Map;
        dark = j['dark'] == true;
        sephiraEnabled = j['sephiraEnabled'] == true;
        sephiraInitialized = j['sephiraInitialized'] == true;
      }
    } catch (_) {}
  }

  /// One-line message in the header for a few seconds.
  void showNotice(String s) {
    notice = s; notifyListeners();
    Future.delayed(const Duration(seconds: 6), () { if (notice == s) { notice = null; notifyListeners(); } });
  }

  void setDark(bool v) {
    dark = v; notifyListeners();
    try {
      final f = File(paths.settingsFile);
      final j = f.existsSync() ? json.decode(f.readAsStringSync()) as Map : <String, dynamic>{};
      j['dark'] = dark;
      f.writeAsStringSync(json.encode(j));
    } catch (_) {}
  }

  // ---------------------------------------------------------------- build / install
  bool get building => buildState?['running'] == true;

  Future<void> startBuild({required bool install}) => _withRoster(() async {
    try {
      if (building) { throw StateError('A build is already running.'); }
      await _savePending();
      await api!.build(install: install);
    } catch (e) {
      showNotice(e.toString()); return;
    }
    buildState = {'running': true, 'log': <String>[], 'stage': 'Starting'};
    notifyListeners();
    _buildTimer?.cancel();
    _buildTimer = Timer.periodic(const Duration(milliseconds: 1200), (t) async {
      try {
        buildState = await api!.buildLog();
        if (buildState?['running'] != true) { t.cancel(); await refreshStatus(); }
      } catch (_) {}
      notifyListeners();
    });
  });

  /// Removes what the studio placed in the game folder and puts back what was there before; or puts one backup back.
  Future<Map<String, dynamic>> restoreGame({String? backup}) async {
    final r = await api!.restoreGame(backup: backup);
    showNotice(r['message']?.toString() ?? 'Done.');
    await refreshStatus();
    return r;
  }

  Future<void> installLast() async {
    try {
      final r = await api!.install();
      buildState = {'running': false, 'result': 'ok', 'log': buildState?['log'] ?? <String>[], 'stage': 'Done', 'message': r['message'], 'install': true};
      await refreshStatus();
    } catch (e) { showNotice(e.toString()); }
    notifyListeners();
  }

  Future<void> shutdown() async {
    _stopping = true;
    _buildTimer?.cancel(); _statusTimer?.cancel(); _saveTimer?.cancel();
    await save();
    await engine?.stop();
  }

  @override
  void dispose() {
    _stopping = true;
    _buildTimer?.cancel(); _statusTimer?.cancel(); _saveTimer?.cancel();
    engine?.stop();
    acquisitionLocations.dispose();
    super.dispose();
  }
}
