import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/services.dart';

class TerrainPatch {
  TerrainPatch(Map p)
    : x = (p['x'] as num).toDouble(),
      y = (p['y'] as num).toDouble(),
      z = (p['z'] as num).toDouble(),
      dx = (p['dx'] as num).toDouble(),
      dy = (p['dy'] as num).toDouble(),
      dz = (p['dz'] as num).toDouble(),
      heights = ByteData.sublistView(
        Uint8List.fromList(zlib.decode(base64.decode(p['heights'] as String))),
      );
  final double x, y, z, dx, dy, dz;
  final ByteData heights;
  double at(int u, int v) =>
      z +
      (heights.getUint16((v * 128 + u) * 2, Endian.little) - 32768) / 128 * dz;
  bool contains(double px, double py) =>
      px >= x && px <= x + 127 * dx && py >= y && py <= y + 127 * dy;
  double sample(double px, double py) {
    final u = (px - x) / dx, v = (py - y) / dy;
    final a = math.min(126, u.floor()), b = math.min(126, v.floor());
    final du = u - a, dv = v - b;
    return (at(a, b) * (1 - du) + at(a + 1, b) * du) * (1 - dv) +
        (at(a, b + 1) * (1 - du) + at(a + 1, b + 1) * du) * dv;
  }
}

class CaveTerrain {
  CaveTerrain(this.patches);
  final List<TerrainPatch> patches;
  static CaveTerrain? cached;
  static final bundled = _load();
  static Future<CaveTerrain> _load() async {
    final data = json.decode(
      await rootBundle.loadString(
        'assets/existing_visions/payload/cave_terrain.json',
      ),
    ) as Map;
    if (data['schema'] != 1 || data['size'] != 128) {
      throw const FormatException('Unsupported cave terrain.');
    }
    return cached = CaveTerrain(
      (data['patches'] as List).map((p) => TerrainPatch(p as Map)).toList(),
    );
  }

  double? height(double x, double y) =>
      patches.where((p) => p.contains(x, y)).firstOrNull?.sample(x, y);
}
