import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';

import '../services/cave_terrain.dart';

typedef Point3 = (double, double, double);

class PlacementScene {
  PlacementScene(this.meshes, this.props);
  final Map<String, dynamic> meshes;
  final List<dynamic> props;
  static final bundled = _load();
  static Future<PlacementScene> _load() async {
    final data = json.decode(
      await rootBundle.loadString(
        'assets/acquisition_map/placement_scene.json',
      ),
    ) as Map;
    return PlacementScene(
      Map<String, dynamic>.from(data['meshes'] as Map),
      data['props'] as List,
    );
  }
}

/// Native terrain geometry, native entrance geometry and simplified prop bounds.
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
                builder: (context, snapshot) {
                  if (snapshot.hasError) {
                    return Text(
                      'Could not load the placement preview: ${snapshot.error}',
                    );
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
        'Drag to move the entrance. Native terrain; simplified prop outlines.\nGame lighting, shaders and instanced foliage are not shown.',
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
      for (var v = 0; v < 127; v += 4) {
        for (var u = 0; u < 127; u += 4) {
          final a = math.min(127, u + 4), b = math.min(127, v + 4);
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
          faces.add(([point(u, v), point(a, v), point(a, b)], color));
          faces.add(([point(u, v), point(a, b), point(u, b)], color));
        }
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
      canvas.drawPath(path, Paint()..color = face.$2);
      canvas.drawPath(
        path,
        Paint()
          ..color = Colors.black.withValues(alpha: .12)
          ..style = PaintingStyle.stroke
          ..strokeWidth = .4,
      );
    }
    for (final prop in scene?.props ?? []) {
      final vertices = (prop['corners'] as List)
          .map(
            (p) => (
              (p[0] as num).toDouble(),
              (p[1] as num).toDouble(),
              (p[2] as num).toDouble(),
            ),
          )
          .toList();
      if ((vertices[0].$1 - center.dx).abs() > radius ||
          (vertices[0].$2 - center.dy).abs() > radius) {
        continue;
      }
      final paint = Paint()
        ..color = const Color(0xff9db08b)
        ..strokeWidth = 1;
      for (final edge in const [
        (0, 1),
        (0, 2),
        (0, 4),
        (1, 3),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 7),
        (4, 5),
        (4, 6),
        (5, 7),
        (6, 7),
      ]) {
        canvas.drawLine(
          project(vertices[edge.$1], size),
          project(vertices[edge.$2], size),
          paint,
        );
      }
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
