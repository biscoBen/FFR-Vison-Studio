import 'dart:math';

/// Studio planning preferences only; the mod builder does not consume these.
class AcquisitionSite {
  const AcquisitionSite(
    this.id,
    this.label,
    this.worldX,
    this.worldY, {
    this.kind = 'shop',
  });
  final String id, label;
  final double? worldX, worldY;
  final String kind;
  bool get hasPosition => worldX != null && worldY != null;
}

class Acquisition {
  const Acquisition({
    required this.location,
    this.random = true,
    this.hideSpoilers = true,
    this.cave,
  });
  static const field = 'studioAcquisition';
  // Compatibility anchors for configurations saved before the shared cave pool.
  static const sites = [
    AcquisitionSite('mitra_shop', 'Mitra shop', 16598, 21654),
    AcquisitionSite('earth_shrine', 'Earth Shrine', 18040, 20920, kind: 'cave'),
    AcquisitionSite(
      'crystal_cave',
      'Crystal Fina cave',
      17600,
      21400,
      kind: 'cave',
    ),
  ];
  final String location;
  final bool random, hideSpoilers;
  final Map<String, dynamic>? cave;
  AcquisitionSite get site => sites.firstWhere((s) => s.id == location);

  static bool valid(dynamic value) {
    if (value is! Map ||
        value['random'] is! bool ||
        value['hideSpoilers'] is! bool) {
      return false;
    }
    if (value['version'] == 1) {
      return value.length == 4 && sites.any((s) => s.id == value['location']);
    }
    if (value['version'] != 2 || value.length != 5) return false;
    final location = value['location'];
    if (value['cave'] == null) {
      return location == 'mitra_shop' ||
          location is String && RegExp(r'^shop_[0-9]{1,9}$').hasMatch(location);
    }
    return validCave(value['cave']) && value['cave']['id'] == location;
  }

  static bool validCave(dynamic value) =>
      value is Map &&
      value.length == 6 &&
      value['id'] is String &&
      (value['id'] == 'crystal_cave' ||
          RegExp(r'^cave_[a-z0-9_]{1,64}$').hasMatch(value['id'])) &&
      value['name'] is String &&
      value['name'].trim().isNotEmpty &&
      value['name'].length <= 80 &&
      value['entrance'] is String &&
      RegExp(r'^[a-z0-9_]{1,64}$').hasMatch(value['entrance']) &&
      value['version'] == 1 &&
      value['worldX'] is num &&
      value['worldX'].isFinite &&
      value['worldX'] >= -24500 &&
      value['worldX'] <= 25300 &&
      value['worldY'] is num &&
      value['worldY'].isFinite &&
      value['worldY'] >= -23700 &&
      value['worldY'] <= 23700;

  factory Acquisition.fromJson(Map value) => Acquisition(
    location: value['location'] as String,
    random: value['random'] as bool,
    hideSpoilers: value['hideSpoilers'] as bool,
    cave: value['cave'] == null
        ? null
        : Map<String, dynamic>.from(value['cave'] as Map),
  );

  factory Acquisition.initial({Random? rng}) =>
      Acquisition(location: sites[(rng ?? Random()).nextInt(sites.length)].id);

  Acquisition copyWith({String? location, bool? random, bool? hideSpoilers}) =>
      Acquisition(
        location: location ?? this.location,
        random: random ?? this.random,
        hideSpoilers: hideSpoilers ?? this.hideSpoilers,
        cave: location == null ? cave : null,
      );

  Acquisition choose(
    AcquisitionSite site, {
    Map<String, dynamic>? cave,
    bool? random,
  }) => Acquisition(
    location: site.id,
    random: random ?? this.random,
    hideSpoilers: hideSpoilers,
    cave: cave,
  );

  /// Exclude the previous choice so a reroll visibly picks a fresh location.
  Acquisition reroll(bool random, {Random? rng}) {
    final alternatives = sites.where((s) => s.id != location).toList();
    return copyWith(
      random: random,
      location: alternatives[(rng ?? Random()).nextInt(alternatives.length)].id,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': cave != null || location.startsWith('shop_') ? 2 : 1,
    'random': random,
    'hideSpoilers': hideSpoilers,
    'location': location,
    if (cave != null || location.startsWith('shop_')) 'cave': cave,
  };
}
