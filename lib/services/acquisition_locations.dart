import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'acquisition.dart';

class CaveEntrance {
  const CaveEntrance(this.id, this.name, this.image, this.mesh);
  final String id, name, image, mesh;
}

class CaveLocation {
  const CaveLocation({
    required this.id,
    required this.name,
    required this.entrance,
    required this.worldX,
    required this.worldY,
  });
  final String id, name, entrance;
  final double worldX, worldY;
  static const original = CaveLocation(
    id: 'crystal_cave',
    name: 'Crystal Fina cave',
    entrance: 'rock_cave',
    worldX: 17600,
    worldY: 21400,
  );
  AcquisitionSite get site =>
      AcquisitionSite(id, name, worldX, worldY, kind: 'cave');
  Map<String, dynamic> toJson() => {
    'version': 1,
    'id': id,
    'name': name,
    'entrance': entrance,
    'worldX': worldX,
    'worldY': worldY,
  };
  factory CaveLocation.fromJson(Map value) {
    if (!Acquisition.validCave(value)) {
      throw const FormatException('Invalid saved cave placement.');
    }
    return CaveLocation(
      id: value['id'] as String,
      name: value['name'] as String,
      entrance: value['entrance'] as String,
      worldX: (value['worldX'] as num).toDouble(),
      worldY: (value['worldY'] as num).toDouble(),
    );
  }
}

class AcquisitionCatalog {
  const AcquisitionCatalog({
    required this.vendors,
    required this.entrances,
    required this.mitraShop,
  });
  final List<AcquisitionSite> vendors;
  final List<CaveEntrance> entrances;
  final String mitraShop;
  static AcquisitionCatalog? cached;
  static final Future<AcquisitionCatalog> bundled = _load();
  static Future<AcquisitionCatalog> _load() async {
    final data = json.decode(
      await rootBundle.loadString('assets/acquisition_map/locations.json'),
    ) as Map;
    if (data['schema'] != 1) {
      throw const FormatException('Unsupported acquisition location catalog.');
    }
    final shops = (data['vendors'] as List)
        .map(
          (v) => AcquisitionSite(
            v['id'] as String,
            v['name'] as String,
            (v['worldX'] as num?)?.toDouble(),
            (v['worldY'] as num?)?.toDouble(),
          ),
        )
        .toList();
    final entrances = (data['entrances'] as List)
        .map(
          (v) => CaveEntrance(
            v['id'] as String,
            v['name'] as String,
            v['image'] as String,
            v['mesh'] as String,
          ),
        )
        .toList();
    if (shops.isEmpty ||
        entrances.isEmpty ||
        shops.map((v) => v.id).toSet().length != shops.length ||
        entrances.map((v) => v.id).toSet().length != entrances.length ||
        !shops.any((v) => v.id == data['mitraShop'])) {
      throw const FormatException('The acquisition catalog is incomplete.');
    }
    return cached = AcquisitionCatalog(
      vendors: List.unmodifiable(shops),
      entrances: List.unmodifiable(entrances),
      mitraShop: data['mitraShop'] as String,
    );
  }

  AcquisitionSite? vendor(String id) =>
      vendors.where((v) => v.id == id).firstOrNull;
  CaveEntrance? entrance(String id) =>
      entrances.where((v) => v.id == id).firstOrNull;
}

/// Shared placements; assigned cave snapshots travel with each vision's spec.
class AcquisitionLocations extends ChangeNotifier {
  AcquisitionLocations({this.file}) {
    try {
      if (file?.existsSync() == true) {
        final value = json.decode(file!.readAsStringSync());
        if (value is! Map || value['version'] != 1 || value['caves'] is! List) {
          throw const FormatException('Unsupported cave list.');
        }
        final caves = (value['caves'] as List)
            .map((v) => CaveLocation.fromJson(v as Map))
            .toList();
        if (caves.map((v) => v.id).toSet().length != caves.length) {
          throw const FormatException('Duplicate saved cave identities.');
        }
        _caves = List.unmodifiable(caves);
      }
    } catch (error) {
      loadError = error;
    }
  }
  final File? file;
  Object? loadError;
  bool _writing = false;
  List<CaveLocation> _caves = const [CaveLocation.original];
  List<CaveLocation> get caves => _caves;
  CaveLocation? cave(String id) => caves.where((v) => v.id == id).firstOrNull;
  List<AcquisitionSite> sites(AcquisitionCatalog catalog) => [
    ...catalog.vendors,
    ...caves.map((v) => v.site),
  ];
  AcquisitionSite? site(Acquisition preferences, AcquisitionCatalog catalog) =>
      catalog.vendor(preferences.location) ?? cave(preferences.location)?.site;

  Acquisition choose(
    Acquisition preferences,
    AcquisitionSite site, {
    bool? random,
  }) => preferences.choose(site, cave: cave(site.id)?.toJson(), random: random);

  Acquisition initial(AcquisitionCatalog catalog, {Random? rng}) {
    final all = sites(catalog);
    final site = all[(rng ?? Random()).nextInt(all.length)];
    return choose(Acquisition(location: site.id), site);
  }

  Acquisition reroll(
    Acquisition preferences,
    bool random,
    AcquisitionCatalog catalog, {
    Random? rng,
  }) {
    final all = sites(catalog)
        .where((s) => s.id != preferences.location)
        .toList();
    if (all.isEmpty) return preferences.copyWith(random: random);
    return choose(
      preferences,
      all[(rng ?? Random()).nextInt(all.length)],
      random: random,
    );
  }

  /// The former Earth Shrine choice was native, not a custom cave. Preserve old
  /// files while moving that retired UI choice to the existing custom cave.
  Acquisition migrate(Acquisition preferences, AcquisitionCatalog catalog) {
    if (preferences.location == 'mitra_shop') {
      return choose(preferences, catalog.vendor(catalog.mitraShop)!);
    }
    if (preferences.location == 'earth_shrine' ||
        preferences.location == 'crystal_cave' && preferences.cave == null) {
      return choose(
        preferences,
        cave('crystal_cave')?.site ?? catalog.vendor(catalog.mitraShop)!,
      );
    }
    return preferences;
  }

  Future<void> add(CaveLocation value) async {
    _checkWritable();
    CaveLocation.fromJson(value.toJson());
    final previous = cave(value.id);
    if (previous != null) {
      if (json.encode(previous.toJson()) == json.encode(value.toJson())) return;
      throw StateError(
        'This cave ID already belongs to a different saved placement.',
      );
    }
    await _saveCaves([...caves, value]);
  }

  Future<void> remove(String id) async {
    _checkWritable();
    if (cave(id) == null) return;
    await _saveCaves(caves.where((c) => c.id != id).toList());
  }

  void _checkWritable() {
    if (loadError != null) {
      throw StateError(
        'The saved cave list could not be read. It has been preserved.',
      );
    }
    if (_writing) throw StateError('A cave placement is being saved.');
  }

  Future<void> _saveCaves(List<CaveLocation> next) async {
    _writing = true;
    try {
      if (file != null) {
        final pending = File('${file!.path}.pending');
        await pending.writeAsString(
          json.encode({
            'version': 1,
            'caves': next.map((v) => v.toJson()).toList(),
          }),
          flush: true,
        );
        await pending.rename(file!.path);
      }
      _caves = List.unmodifiable(next);
      notifyListeners();
    } finally {
      _writing = false;
    }
  }
}
