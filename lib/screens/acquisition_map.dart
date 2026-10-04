import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../services/acquisition.dart';
import '../services/acquisition_map_data.dart';

class AcquisitionMap extends StatefulWidget {
  const AcquisitionMap({super.key, required this.site});
  final AcquisitionSite? site;

  @override
  State<AcquisitionMap> createState() => _AcquisitionMapState();
}

class _AcquisitionMapState extends State<AcquisitionMap> {
  final _transform = TransformationController();
  double _zoom = 6;
  Size? _viewport;
  static const _maxZoom = 12.0;
  // Fixed demo-area focus. It never follows a hidden random choice.
  static const _demoFocus = Offset(21287, -17319);

  @override
  void dispose() {
    _transform.dispose();
    super.dispose();
  }

  Matrix4 _matrix(double zoom, Size viewport, Offset center) =>
      Matrix4.identity()
        ..translateByDouble(
          (viewport.width / 2 - center.dx * zoom).clamp(
            viewport.width * (1 - zoom),
            0,
          ),
          (viewport.height / 2 - center.dy * zoom).clamp(
            viewport.height * (1 - zoom),
            0,
          ),
          0,
          1,
        )
        ..scaleByDouble(zoom, zoom, 1, 1);

  void _setZoom(double value, Size viewport) {
    final center = _transform.toScene(viewport.center(Offset.zero));
    setState(() {
      _zoom = value;
      _transform.value = _matrix(value, viewport, center);
    });
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<AcquisitionMapData>(
    future: AcquisitionMapData.bundled,
    initialData: AcquisitionMapData.cached,
    builder: (context, snapshot) {
      if (snapshot.hasError) {
        return Center(
          child: Text(
            'The world-map preview could not be loaded: ${snapshot.error}',
            style: Guide.small(),
          ),
        );
      }
      final map = snapshot.data;
      if (map == null) return const Center(child: CircularProgressIndicator());
      return Column(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(border: Border.all(color: Guide.ink)),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final viewport = Size(
                    constraints.maxWidth,
                    constraints.maxHeight,
                  );
                  final previous = _viewport;
                  _viewport = viewport;
                  if (previous == null) {
                    _transform.value = _matrix(
                      _zoom,
                      viewport,
                      map.toViewport(_demoFocus, viewport),
                    );
                  } else if (previous != viewport) {
                    final focus = map.fromViewport(
                      _transform.toScene(previous.center(Offset.zero)),
                      previous,
                    );
                    WidgetsBinding.instance.addPostFrameCallback((_) {
                      if (mounted && _viewport == viewport) {
                        _transform.value = _matrix(
                          _zoom,
                          viewport,
                          map.toViewport(focus, viewport),
                        );
                      }
                    });
                  }
                  final site = widget.site;
                  final marker = site == null
                      ? null
                      : map.toViewport(
                          AcquisitionMapData.project(site.worldX, site.worldY),
                          viewport,
                        );
                  return MouseRegion(
                    cursor: SystemMouseCursors.grab,
                    child: InteractiveViewer(
                      key: const ValueKey('acquisition-map'),
                      transformationController: _transform,
                      minScale: 1,
                      maxScale: _maxZoom,
                      onInteractionUpdate: (_) => setState(
                        () => _zoom = _transform.value
                            .getMaxScaleOnAxis()
                            .clamp(1, _maxZoom),
                      ),
                      child: SizedBox.expand(
                        child: Stack(
                          children: [
                            Positioned.fill(
                              child: Image.asset(
                                '${AcquisitionMapData.assetRoot}/T_Wld_ocean.png',
                                fit: BoxFit.cover,
                                excludeFromSemantics: true,
                              ),
                            ),
                            for (final capture in map.captures)
                              Positioned.fromRect(
                                rect: map.captureRect(capture, viewport),
                                child: Image.asset(
                                  '${AcquisitionMapData.assetRoot}/${capture.image}',
                                  fit: BoxFit.fill,
                                  excludeFromSemantics: true,
                                ),
                              ),
                            if (marker != null)
                              Positioned(
                                left: marker.dx - 16,
                                top: marker.dy - 32,
                                child: Transform.scale(
                                  scale: 1 / _zoom,
                                  alignment: Alignment.bottomCenter,
                                  child: Tooltip(
                                    message: site!.label,
                                    child: Semantics(
                                      label:
                                          'Acquisition location: ${site.label}',
                                      child: const Icon(
                                        Icons.location_on,
                                        key: ValueKey('acquisition-marker'),
                                        color: Color(0xffffcf4a),
                                        size: 32,
                                        shadows: [
                                          Shadow(
                                            color: Colors.black,
                                            blurRadius: 4,
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
          SizedBox(
            height: 48,
            child: Row(
              children: [
                Text('Zoom', style: Guide.small()),
                Expanded(
                  child: Slider(
                    key: const ValueKey('acquisition-zoom'),
                    min: 1,
                    max: _maxZoom,
                    value: _zoom,
                    label: '${(_zoom * 100).round()}%',
                    onChanged: (value) => _setZoom(value, _viewport!),
                  ),
                ),
                SizedBox(
                  width: 54,
                  child: Text(
                    '${(_zoom * 100).round()}%',
                    style: Guide.small(),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() {
                    _transform.value = Matrix4.identity();
                    _zoom = 1;
                  }),
                  child: const Text('Full map'),
                ),
              ],
            ),
          ),
          Text('Drag to move around the map.', style: Guide.small()),
        ],
      );
    },
  );
}
