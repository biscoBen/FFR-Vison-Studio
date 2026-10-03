import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../design/theme.dart';
import '../services/overworld_appearance.dart';

/// Preview the actual directional walking sheet used by the field importer.
class OverworldAnimPane extends StatefulWidget {
  const OverworldAnimPane({super.key});
  @override
  State<OverworldAnimPane> createState() => _OverworldAnimPaneState();
}

class _OverworldAnimPaneState extends State<OverworldAnimPane>
    with SingleTickerProviderStateMixin {
  late final AnimationController clock;
  ui.Image? image;
  String? error;
  int direction = 0;
  static const directions = [
    'South',
    'North',
    'West',
    'East',
    'Southwest',
    'Southeast',
    'Northwest',
    'Northeast',
  ];
  @override
  void initState() {
    super.initState();
    clock = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat();
    _load();
  }

  Future<void> _load() async {
    try {
      final bytes = await rootBundle.load(OverworldAppearance.sheet);
      final codec = await ui.instantiateImageCodec(
        bytes.buffer.asUint8List(bytes.offsetInBytes, bytes.lengthInBytes),
      );
      final frame = await codec.getNextFrame();
      codec.dispose();
      if (!mounted) {
        frame.image.dispose();
        return;
      }
      setState(() => image = frame.image);
    } catch (e) {
      if (mounted) {
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
                  builder: (_, _) => CustomPaint(
                    size: const Size(160, 160),
                    painter: _FieldPainter(
                      image!,
                      direction + 16,
                      1 + (clock.value * 6).floor().clamp(0, 5),
                    ),
                  ),
                ),
        ),
        DropdownButton<int>(
          value: direction,
          items: [
            for (var i = 0; i < directions.length; i++)
              DropdownMenuItem(
                value: i,
                child: Text(directions[i], style: Guide.small()),
              ),
          ],
          onChanged: (value) {
            if (value != null) {
              setState(() => direction = value);
            }
          },
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
