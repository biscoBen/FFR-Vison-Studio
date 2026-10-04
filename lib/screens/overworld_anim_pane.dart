import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../services/overworld_appearance.dart';

/// Preview the actual directional walking sheet used by the field importer.
class OverworldAnimPane extends StatefulWidget {
  const OverworldAnimPane({super.key, this.model = OverworldAppearance.model});
  final String model;
  @override
  State<OverworldAnimPane> createState() => _OverworldAnimPaneState();
}

class _OverworldAnimPaneState extends State<OverworldAnimPane>
    with SingleTickerProviderStateMixin {
  late final AnimationController clock;
  ui.Image? image;
  String? error;
  int direction = 2;
  String motion = 'move';
  int _loadSequence = 0;
  static const directions = [
    (2, 'South'),
    (8, 'North'),
    (4, 'West'),
    (6, 'East'),
    (1, 'Southwest'),
    (3, 'Southeast'),
    (7, 'Northwest'),
    (9, 'Northeast'),
  ];
  List<(int, String)> get available =>
      OverworldAppearance.data(widget.model)['directions'] == 8
      ? directions
      : directions.take(4).toList();
  @override
  void initState() {
    super.initState();
    clock = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat();
    _load();
    _timing();
  }

  void _timing() {
    final frames = OverworldAppearance.frames(widget.model, motion, direction);
    final delay = motion == 'dash'
        ? 5
        : motion == 'move'
        ? 8
        : 1;
    clock.duration = Duration(
      microseconds: (frames.length * delay * 1000000 / 60).round(),
    );
    clock.repeat();
  }

  @override
  void didUpdateWidget(OverworldAnimPane oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.model != widget.model) {
      direction = 2;
      motion = 'move';
      error = null;
      image?.dispose();
      image = null;
      _timing();
      _load();
    }
  }

  Future<void> _load() async {
    final seq = ++_loadSequence;
    try {
      final bytes = await OverworldAppearance.assetBytes(widget.model, 'sheet');
      final codec = await ui.instantiateImageCodec(bytes);
      final frame = await codec.getNextFrame();
      codec.dispose();
      if (!mounted || seq != _loadSequence) {
        frame.image.dispose();
        return;
      }
      setState(() => image = frame.image);
    } catch (e) {
      if (mounted && seq == _loadSequence) {
        setState(() => error = 'Could not load the walking preview.');
      }
    }
  }

  @override
  void dispose() {
    clock.dispose();
    image?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Container(
    height: 210,
    decoration: BoxDecoration(
      color: Guide.paper2,
      border: Border.all(color: Guide.ink, width: 2),
    ),
    child: Column(
      children: [
        Expanded(
          child: image == null
              ? Center(
                  child: Text(
                    error ?? 'Loading walking sprites',
                    style: Guide.small(),
                  ),
                )
              : AnimatedBuilder(
                  animation: clock,
                  builder: (_, _) {
                    final frames = OverworldAppearance.frames(
                      widget.model,
                      motion,
                      direction,
                    );
                    final frame =
                        frames[(clock.value * frames.length).floor().clamp(
                          0,
                          frames.length - 1,
                        )];
                    return CustomPaint(
                      size: const Size(160, 160),
                      painter: _FieldPainter(image!, frame[0], frame[1]),
                    );
                  },
                ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            DropdownButton<int>(
              value: direction,
              items: [
                for (final item in available)
                  DropdownMenuItem(
                    value: item.$1,
                    child: Text(item.$2, style: Guide.small()),
                  ),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => direction = value);
                  _timing();
                }
              },
            ),
            DropdownButton<String>(
              value: motion,
              items: [
                for (final item in [
                  ('idle', 'Idle'),
                  ('move', 'Walk'),
                  ('dash', 'Run'),
                ])
                  DropdownMenuItem(
                    value: item.$1,
                    child: Text(item.$2, style: Guide.small()),
                  ),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => motion = value);
                  _timing();
                }
              },
            ),
          ],
        ),
      ],
    ),
  );
}

class _FieldPainter extends CustomPainter {
  _FieldPainter(this.image, this.row, this.frame);
  final ui.Image image;
  final int row, frame;
  @override
  void paint(Canvas canvas, Size size) {
    final side = size.shortestSide;
    canvas.drawImageRect(
      image,
      Rect.fromLTWH(frame * 64, row * 64, 64, 64),
      Rect.fromLTWH(
        (size.width - side) / 2,
        (size.height - side) / 2,
        side,
        side,
      ),
      Paint()..filterQuality = FilterQuality.none,
    );
  }

  @override
  bool shouldRepaint(_FieldPainter old) =>
      old.image != image || old.row != row || old.frame != frame;
}
