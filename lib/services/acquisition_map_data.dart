import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/services.dart';

class MapCapture {
  const MapCapture(this.image, this.center, this.size);
  final String image;
  final Offset center;
  final Size size;
}

/// Native world-map capture coordinates, shared by imagery and markers.
class AcquisitionMapData {
  const AcquisitionMapData(this.wholeSize, this.worldOffset, this.captures);
  final Size wholeSize;
  final Offset worldOffset;
  final List<MapCapture> captures;
  static const assetRoot = 'assets/acquisition_map';
  static AcquisitionMapData? _cached;
  static AcquisitionMapData? get cached => _cached;
  static final Future<AcquisitionMapData> bundled = _load();

  static Future<AcquisitionMapData> _load() async {
    final data = json.decode(
      await rootBundle.loadString('$assetRoot/manifest.json'),
    ) as Map;
    if (data['schema'] != 1 ||
        data['mapId'] != 1000 ||
        (data['projection'] as List).join(',') != 'worldY,-worldX') {
      throw const FormatException('Unsupported world-map capture data.');
    }
    final whole = data['wholeSize'] as List;
    final offset = data['worldOffset'] as List;
    final captures = (data['tiles'] as List)
        .map(
          (tile) => MapCapture(
            tile['image'] as String,
            Offset(
              (tile['center'][0] as num).toDouble(),
              (tile['center'][1] as num).toDouble(),
            ),
            Size(
              (tile['size'][0] as num).toDouble(),
              (tile['size'][1] as num).toDouble(),
            ),
          ),
        )
        .toList();
    return _cached = AcquisitionMapData(
      Size((whole[0] as num).toDouble(), (whole[1] as num).toDouble()),
      Offset((offset[0] as num).toDouble(), (offset[1] as num).toDouble()),
      captures,
    );
  }

  // Unreal's north is +X and east is +Y; the native map is east/right,
  // north/up. Capture centers are already expressed in these map coordinates.
  static Offset project(double worldX, double worldY) =>
      Offset(worldY, -worldX);

  Rect fittedRect(Size viewport) {
    final scale = math.min(
      viewport.width / wholeSize.width,
      viewport.height / wholeSize.height,
    );
    return Rect.fromCenter(
      center: viewport.center(Offset.zero),
      width: wholeSize.width * scale,
      height: wholeSize.height * scale,
    );
  }

  Offset toViewport(Offset point, Size viewport) {
    final rect = fittedRect(viewport);
    return Offset(
      rect.center.dx +
          (point.dx - worldOffset.dx) / wholeSize.width * rect.width,
      rect.center.dy +
          (point.dy - worldOffset.dy) / wholeSize.height * rect.height,
    );
  }

  Offset fromViewport(Offset point, Size viewport) {
    final rect = fittedRect(viewport);
    return Offset(
      worldOffset.dx +
          (point.dx - rect.center.dx) / rect.width * wholeSize.width,
      worldOffset.dy +
          (point.dy - rect.center.dy) / rect.height * wholeSize.height,
    );
  }

  Rect captureRect(MapCapture capture, Size viewport) {
    final fitted = fittedRect(viewport);
    return Rect.fromCenter(
      center: toViewport(capture.center, viewport),
      width: capture.size.width / wholeSize.width * fitted.width,
      height: capture.size.height / wholeSize.height * fitted.height,
    );
  }
}
