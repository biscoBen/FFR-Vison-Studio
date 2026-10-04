import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../services/acquisition.dart';
import '../services/acquisition_map_data.dart';

class AcquisitionMap extends StatefulWidget {
  const AcquisitionMap({
    super.key,
    required this.site,
    this.caves = const [],
    this.onAddCave,
    this.onRemoveCave,
    this.onEditCave,
    this.addActionLabel = 'Add cave here',
  });
  final AcquisitionSite? site;
  final List<AcquisitionSite> caves;
  final ValueChanged<Offset>? onAddCave;
  final ValueChanged<String>? onRemoveCave;
  final ValueChanged<String>? onEditCave;
  final String addActionLabel;

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

  bool _focusSelection = false;
  @override
  void didUpdateWidget(covariant AcquisitionMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.site?.id != widget.site?.id &&
        widget.site?.hasPosition == true) {
      _focusSelection = true;
    }
  }

  Future<void> _menu(
    TapDownDetails details,
    AcquisitionMapData map,
    Size viewport,
  ) async {
    final scene = _transform.toScene(details.localPosition);
    final canAdd =
        widget.onAddCave != null && map.fittedRect(viewport).contains(scene);
    final projected = map.fromViewport(scene, viewport);
    final nearby = widget.caves.where((c) => c.hasPosition).where((c) {
      final point = MatrixUtils.transformPoint(
        _transform.value,
        map.toViewport(
          AcquisitionMapData.project(c.worldX!, c.worldY!),
          viewport,
        ),
      );
      final bounds = c.id == widget.site?.id
          ? Rect.fromLTWH(point.dx - 16, point.dy - 32, 32, 32)
          : Rect.fromLTWH(point.dx - 8, point.dy - 8, 16, 16);
      return bounds.inflate(4).contains(details.localPosition);
    }).toList();
    if (!canAdd &&
        ((widget.onRemoveCave == null && widget.onEditCave == null) ||
            nearby.isEmpty)) {
      return;
    }
    final overlay =
        Overlay.of(context).context.findRenderObject()! as RenderBox;
    final anchor = overlay.globalToLocal(details.globalPosition);
    final action = await showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        anchor.dx,
        anchor.dy,
        overlay.size.width - anchor.dx,
        overlay.size.height - anchor.dy,
      ),
      items: [
        if (canAdd)
          PopupMenuItem(value: 'add', child: Text(widget.addActionLabel)),
        if (widget.onEditCave != null)
          for (final cave in nearby)
            PopupMenuItem(
              value: 'edit:${cave.id}',
              child: Text('Edit placement: ${cave.label}'),
            ),
        if (widget.onRemoveCave != null)
          for (final cave in nearby)
            PopupMenuItem(
              value: 'remove:${cave.id}',
              child: Text('Remove cave: ${cave.label}'),
            ),
      ],
    );
    if (mounted && action == 'add') {
      widget.onAddCave?.call(Offset(-projected.dy, projected.dx));
    } else if (mounted && action?.startsWith('remove:') == true) {
      widget.onRemoveCave?.call(action!.substring('remove:'.length));
    } else if (mounted && action?.startsWith('edit:') == true) {
      widget.onEditCave?.call(action!.substring('edit:'.length));
    }
  }

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
                      map.toViewport(
                        widget.site?.hasPosition == true
                            ? AcquisitionMapData.project(
                                widget.site!.worldX!,
                                widget.site!.worldY!,
                              )
                            : _demoFocus,
                        viewport,
                      ),
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
                  if (_focusSelection && widget.site?.hasPosition == true) {
                    _focusSelection = false;
                    final target = map.toViewport(
                      AcquisitionMapData.project(
                        widget.site!.worldX!,
                        widget.site!.worldY!,
                      ),
                      viewport,
                    );
                    WidgetsBinding.instance.addPostFrameCallback((_) {
                      if (mounted) {
                        _transform.value = _matrix(_zoom, viewport, target);
                      }
                    });
                  }
                  final site = widget.site;
                  final marker = site?.hasPosition != true
                      ? null
                      : map.toViewport(
                          AcquisitionMapData.project(
                            site!.worldX!,
                            site.worldY!,
                          ),
                          viewport,
                        );
                  return MouseRegion(
                    cursor: SystemMouseCursors.grab,
                    child: GestureDetector(
                      key: const ValueKey('acquisition-map-context'),
                      onSecondaryTapDown:
                          widget.onAddCave == null &&
                              widget.onRemoveCave == null &&
                              widget.onEditCave == null
                          ? null
                          : (details) => _menu(details, map, viewport),
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
                              for (final cave in widget.caves.where(
                                (c) => c.id != site?.id,
                              ))
                                Positioned(
                                  left:
                                      map
                                          .toViewport(
                                            AcquisitionMapData.project(
                                              cave.worldX!,
                                              cave.worldY!,
                                            ),
                                            viewport,
                                          )
                                          .dx -
                                      8,
                                  top:
                                      map
                                          .toViewport(
                                            AcquisitionMapData.project(
                                              cave.worldX!,
                                              cave.worldY!,
                                            ),
                                            viewport,
                                          )
                                          .dy -
                                      8,
                                  child: Transform.scale(
                                    scale: 1 / _zoom,
                                    child: Tooltip(
                                      message: cave.label,
                                      child: Icon(
                                        key: ValueKey(
                                          'acquisition-cave-${cave.id}',
                                        ),
                                        Icons.circle_outlined,
                                        size: 16,
                                        color: Color(0xff83d9ff),
                                      ),
                                    ),
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
