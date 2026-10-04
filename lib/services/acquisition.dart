import 'dart:math';

/// Studio planning preferences only; the mod builder does not consume these.
class AcquisitionSite {
  const AcquisitionSite(this.id, this.label, this.worldX, this.worldY);
  final String id, label;
  final double worldX, worldY;
}

class Acquisition {
  const Acquisition({
    required this.location,
    this.random = true,
    this.hideSpoilers = true,
  });
  static const field = 'studioAcquisition';
  // Native world anchors: Earth Shrine
  // (18040,20920), cave (17600,21400), Mitra (16598,21654).
  static const sites = [
    AcquisitionSite('mitra_shop', 'Mitra shop', 16598, 21654),
    AcquisitionSite('earth_shrine', 'Earth Shrine', 18040, 20920),
    AcquisitionSite('crystal_cave', 'Crystal cave', 17600, 21400),
  ];
  final String location;
  final bool random, hideSpoilers;
  AcquisitionSite get site => sites.firstWhere((s) => s.id == location);

  static bool valid(dynamic value) =>
      value is Map &&
      value.length == 4 &&
      value['version'] == 1 &&
      value['random'] is bool &&
      value['hideSpoilers'] is bool &&
      sites.any((s) => s.id == value['location']);

  factory Acquisition.fromJson(Map value) => Acquisition(
    location: value['location'] as String,
    random: value['random'] as bool,
    hideSpoilers: value['hideSpoilers'] as bool,
  );

  factory Acquisition.initial({Random? rng}) =>
      Acquisition(location: sites[(rng ?? Random()).nextInt(sites.length)].id);

  Acquisition copyWith({String? location, bool? random, bool? hideSpoilers}) =>
      Acquisition(
        location: location ?? this.location,
        random: random ?? this.random,
        hideSpoilers: hideSpoilers ?? this.hideSpoilers,
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
    'version': 1,
    'random': random,
    'hideSpoilers': hideSpoilers,
    'location': location,
  };
}
