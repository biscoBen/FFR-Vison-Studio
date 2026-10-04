import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';

import '../services/cave_terrain.dart';

typedef Point3 = (double, double, double);

class PlacementScene {
  PlacementScene(
    this.meshes,
    this.props,
    this.terrainImages,
    this.foliage,
    this.images,
  );
  final Map<String, dynamic> meshes;
  final List<dynamic> props;
  final List<dynamic> terrainImages, foliage;
  final Map<String, ui.Image> images;
  static PlacementScene? cached;
  static final bundled = _load();
  static Future<PlacementScene> _load() async {
    final data = json.decode(
      await rootBundle.loadString(
        'assets/acquisition_map/placement_scene.json',
      ),
    ) as Map;
    final manifest = json.decode(
      await rootBundle.loadString('assets/acquisition_map/scenery.json'),
    ) as Map;
    final bytes = (await rootBundle.load('assets/acquisition_map/scenery.zip'))
        .buffer
        .asUint8List();
    if (sha256.convert(bytes).toString() != manifest['sha256']) {
      throw const FormatException('Native scenery checksum mismatch.');
    }
    final archive = ZipDecoder().decodeBytes(bytes);
    final raw = archive.findFile('scene.json')!.content;
    if (sha256.convert(raw).toString() != manifest['sceneSha256']) {
      throw const FormatException('Native scenery catalog checksum mismatch.');
    }
    final scenery = json.decode(utf8.decode(raw)) as Map;
    final images = <String, ui.Image>{};
    for (final entry in (scenery['files'] as Map).entries) {
      final content = archive.findFile(entry.key as String)!.content;
      if (sha256.convert(content).toString() != entry.value) {
        throw const FormatException('Native scenery image checksum mismatch.');
      }
      final codec = await ui.instantiateImageCodec(content);
      images[entry.key as String] = (await codec.getNextFrame()).image;
      codec.dispose();
    }
    return cached = PlacementScene(
      Map<String, dynamic>.from(data['meshes'] as Map),
      scenery['props'] as List,
      scenery['terrain'] as List,
      scenery['foliage'] as List,
      images,
    );
  }
}

/// Native painted terrain, shaded world meshes and tree/bush instances.
class CaveTerrainPreview extends StatefulWidget {
  const CaveTerrainPreview({
    super.key,
    required this.terrain,
    required this.world,
    required this.z,
    required this.entrance,
    required this.yaw,
    required this.scale,
    required this.onMove,
  });
  final CaveTerrain terrain;
  final Offset world;
  final double z, yaw, scale;
  final String entrance;
  final ValueChanged<Offset> onMove;
  @override
  State<CaveTerrainPreview> createState() => _CaveTerrainPreviewState();
}

class _CaveTerrainPreviewState extends State<CaveTerrainPreview> {
  late Offset _center = widget.world;
  double _span = 1600;
  double? _centerZ;
  Offset? _dragOrigin, _dragWorld;
  @override
  Widget build(BuildContext context) => Column(
    children: [
      Expanded(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final size = Size(constraints.maxWidth, constraints.maxHeight);
            final units = size.width / _span;
            _centerZ ??=
                widget.terrain.height(_center.dx, _center.dy) ?? widget.z;
            void start(DragStartDetails event) {
              _dragOrigin = event.localPosition;
              _dragWorld = widget.world;
            }

            void move(DragUpdateDetails event) {
              final delta = event.localPosition - _dragOrigin!;
              widget.onMove(
                _dragWorld! +
                    Offset(
                      -delta.dy / (units * .866025403784),
                      delta.dx / units,
                    ),
              );
            }

            return GestureDetector(
              key: const ValueKey('cave-terrain-drag'),
              behavior: HitTestBehavior.opaque,
              // Axis recognizers use the same touch threshold as the enclosing
              // scroll view. A pan recognizer loses vertical drags to scrolling.
              dragStartBehavior: DragStartBehavior.down,
              onHorizontalDragStart: start,
              onVerticalDragStart: start,
              onHorizontalDragUpdate: move,
              onVerticalDragUpdate: move,
              child: FutureBuilder<PlacementScene>(
                future: PlacementScene.bundled,
                initialData: PlacementScene.cached,
                builder: (context, snapshot) {
                  if (snapshot.hasError) {
                    return Text(
                      'Could not load the placement preview: ${snapshot.error}',
                    );
                  }
                  if (!snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  return CustomPaint(
                    size: size,
                    painter: _TerrainPainter(
                      widget.terrain,
                      snapshot.data,
                      _center,
                      _centerZ!,
                      units,
                      widget.world,
                      widget.z,
                      widget.entrance,
                      widget.yaw,
                      widget.scale,
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
      Row(
        children: [
          const Text('Area'),
          Expanded(
            child: Slider(
              min: 600,
              max: 4000,
              value: _span,
              onChanged: (v) => setState(() => _span = v),
            ),
          ),
          TextButton(
            onPressed: () => setState(() {
              _center = widget.world;
              _centerZ = null;
            }),
            child: const Text('Center cave'),
          ),
        ],
      ),
      const Text(
        'Drag to move the entrance. Native terrain paint, scenery and trees.\nSimplified lighting; available reference regions only.',
        textAlign: TextAlign.center,
      ),
    ],
  );
}

class _TerrainPainter extends CustomPainter {
  _TerrainPainter(
    this.terrain,
    this.scene,
    this.center,
    this.centerZ,
    this.units,
    this.world,
    this.z,
    this.entrance,
    this.yaw,
    this.scale,
  );
  final CaveTerrain terrain;
  final PlacementScene? scene;
  final Offset center, world;
  final double centerZ, units, z, yaw, scale;
  final String entrance;
  Offset project(Point3 p, Size size) => Offset(
    size.width / 2 + (p.$2 - center.dy) * units,
    size.height * .65 -
        ((p.$1 - center.dx) * .866025403784 + (p.$3 - centerZ) * .5) * units,
  );
  double depth(Point3 p) => p.$1 * .5 - p.$3 * .866025403784;
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawColor(const Color(0xff202d36), BlendMode.src);
    final faces = <(List<Point3>, Color)>[];
    final radius = size.width / units;
    for (final p in terrain.patches) {
      if ((p.x + 127 * p.dx < center.dx - radius) ||
          p.x > center.dx + radius ||
          p.y + 127 * p.dy < center.dy - radius ||
          p.y > center.dy + radius) {
        continue;
      }
      final painted = scene?.terrainImages
          .where(
            (t) =>
                ((t['x'] as num) - p.x).abs() < .01 &&
                ((t['y'] as num) - p.y).abs() < .01,
          )
          .firstOrNull;
      final image = painted == null ? null : scene?.images[painted['image']];
      final positions = <Offset>[], uv = <Offset>[], colors = <Color>[];
      for (var v = 0; v < 127; v += 2) {
        for (var u = 0; u < 127; u += 2) {
          final a = math.min(127, u + 2), b = math.min(127, v + 2);
          if ((p.x + u * p.dx - center.dx).abs() > radius ||
              (p.y + v * p.dy - center.dy).abs() > radius) {
            continue;
          }
          Point3 point(int i, int j) =>
              (p.x + i * p.dx, p.y + j * p.dy, p.at(i, j));
          final height = (p.at(u, v) + p.at(a, b)) / 2;
          final color = height < 0
              ? const Color(0xff315878)
              : height > 300
              ? const Color(0xff7c7c72)
              : const Color(0xff52734d);
          for (final ids in [
            [(u, v), (a, v), (a, b)],
            [(u, v), (a, b), (u, b)],
          ]) {
            if (image == null) {
              faces.add(([for (final q in ids) point(q.$1, q.$2)], color));
            } else {
              final nx = (p.at(u, v) - p.at(a, v)) / ((a - u) * p.dx),
                  ny = (p.at(u, v) - p.at(u, b)) / ((b - v) * p.dy);
              final light =
                  (.75 +
                          (.4 * nx + .5 * ny + .75) /
                              math.sqrt(nx * nx + ny * ny + 1) *
                              .25)
                      .clamp(.45, 1.0);
              for (final q in ids) {
                positions.add(project(point(q.$1, q.$2), size));
                uv.add(Offset(q.$1 + .5, q.$2 + .5));
                colors.add(
                  Color.fromRGBO(
                    (255 * light).round(),
                    (255 * light).round(),
                    (255 * light).round(),
                    1,
                  ),
                );
              }
            }
          }
        }
      }
      if (positions.isNotEmpty) {
        final vertices = ui.Vertices(
          ui.VertexMode.triangles,
          positions,
          textureCoordinates: uv,
          colors: colors,
        );
        canvas.drawVertices(
          vertices,
          BlendMode.modulate,
          Paint()
            ..shader = ui.ImageShader(
              image!,
              ui.TileMode.clamp,
              ui.TileMode.clamp,
              Float64List.fromList([
                1,
                0,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                0,
                1,
              ]),
            )
            ..filterQuality = FilterQuality.medium,
        );
        vertices.dispose();
      }
    }
    for (final prop in scene?.props ?? []) {
      final bounds = prop['bounds'] as List?;
      if (bounds != null &&
          ((bounds[1][0] as num) < center.dx - radius ||
              (bounds[0][0] as num) > center.dx + radius ||
              (bounds[1][1] as num) < center.dy - radius ||
              (bounds[0][1] as num) > center.dy + radius)) {
        continue;
      }
      final v = (prop['vertices'] as List)
          .map(
            (p) => (
              (p[0] as num).toDouble(),
              (p[1] as num).toDouble(),
              (p[2] as num).toDouble(),
            ),
          )
          .toList();
      if (bounds == null &&
          !v.any(
            (p) =>
                (p.$1 - center.dx).abs() < radius &&
                (p.$2 - center.dy).abs() < radius,
          )) {
        continue;
      }
      for (final f in prop['faces'] as List) {
        final rgb = f[1] as List;
        faces.add((
          [for (final i in f[0] as List) v[i as int]],
          Color.fromRGBO(rgb[0] as int, rgb[1] as int, rgb[2] as int, 1),
        ));
      }
    }
    final mesh = scene?.meshes[entrance] as Map?;
    if (mesh != null) {
      final angle = yaw * math.pi / 180,
          c = math.cos(angle),
          s = math.sin(angle);
      final vertices = (mesh['vertices'] as List).map((v) {
        final x = (v[0] as num).toDouble() * scale,
            y = (v[1] as num).toDouble() * scale;
        return (
          world.dx + x * c - y * s,
          world.dy + x * s + y * c,
          z + (v[2] as num).toDouble() * scale,
        );
      }).toList();
      for (final t in mesh['triangles'] as List) {
        faces.add((
          [for (final i in t) vertices[i as int]],
          const Color(0xffc5b98c),
        ));
      }
    }
    faces.sort((a, b) => depth(b.$1[0]).compareTo(depth(a.$1[0])));
    for (final face in faces) {
      final path = Path();
      final a = project(face.$1[0], size);
      path.moveTo(a.dx, a.dy);
      for (final p in face.$1.skip(1)) {
        final q = project(p, size);
        path.lineTo(q.dx, q.dy);
      }
      path.close();
      canvas.drawPath(
        path,
        Paint()
          ..color = face.$2
          ..isAntiAlias = false,
      );
    }
    final foliage =
        (scene?.foliage ?? [])
            .where(
              (f) =>
                  ((f['at'][0] as num) - center.dx).abs() < radius &&
                  ((f['at'][1] as num) - center.dy).abs() < radius,
            )
            .toList()
          ..sort((a, b) => (b['at'][0] as num).compareTo(a['at'][0] as num));
    for (final f in foliage) {
      // Native captures identify the coast; low terrain also includes towns.
      if (f['onLand'] == false) {
        continue;
      }
      final at = project((
        (f['at'][0] as num).toDouble(),
        (f['at'][1] as num).toDouble(),
        (f['at'][2] as num).toDouble(),
      ), size);
      final image = scene!.images[f['image']]!;
      final width = (f['width'] as num) * units,
          height = (f['height'] as num) * units;
      canvas.drawImageRect(
        image,
        Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble()),
        Rect.fromLTWH(at.dx - width / 2, at.dy - height, width, height),
        Paint()..filterQuality = FilterQuality.medium,
      );
    }
    final at = project((world.dx, world.dy, z), size);
    canvas.drawCircle(at, 6, Paint()..color = const Color(0xffffcf4a));
    canvas.drawLine(
      at - const Offset(12, 0),
      at + const Offset(12, 0),
      Paint()..color = Colors.white,
    );
    canvas.drawLine(
      at - const Offset(0, 12),
      at + const Offset(0, 12),
      Paint()..color = Colors.white,
    );
  }

  @override
  bool shouldRepaint(covariant _TerrainPainter oldDelegate) => true;
}
