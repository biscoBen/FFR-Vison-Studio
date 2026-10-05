import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../services/acquisition_locations.dart';
import '../services/cave_terrain.dart';
import 'acquisition_map.dart';
import 'cave_terrain_preview.dart';

Future<CaveLocation?> showCavePlacement(
  BuildContext context,
  AcquisitionLocations locations,
  AcquisitionCatalog catalog,
  Offset world, {
  CaveLocation? existing,
  Future<void> Function(CaveLocation)? save,
}) => showDialog<CaveLocation>(
  context: context,
  builder: (_) => _CavePlacementDialog(
    locations: locations,
    catalog: catalog,
    world: world,
    existing: existing,
    save: save,
  ),
);

class _CavePlacementDialog extends StatefulWidget {
  const _CavePlacementDialog({
    required this.locations,
    required this.catalog,
    required this.world,
    this.existing,
    this.save,
  });
  final AcquisitionLocations locations;
  final AcquisitionCatalog catalog;
  final Offset world;
  final CaveLocation? existing;
  final Future<void> Function(CaveLocation)? save;
  @override
  State<_CavePlacementDialog> createState() => _CavePlacementDialogState();
}

class _CavePlacementDialogState extends State<_CavePlacementDialog> {
  late final _name = TextEditingController(
    text: widget.existing?.name ?? 'Cave ${widget.locations.caves.length + 1}',
  );
  late String _entrance =
      widget.existing?.entrance ?? widget.catalog.entrances.first.id;
  late Offset _world = widget.world;
  final _x = TextEditingController(),
      _y = TextEditingController(),
      _z = TextEditingController();
  late double _yaw = widget.existing?.yaw ?? 105;
  late double _scale = widget.existing?.scale ?? .75;
  double _height = 0;
  CaveTerrain? _terrain;
  bool _saving = false, _threeD = true;
  late bool _placing = widget.existing != null;
  late bool _entranceChosen = widget.existing != null;
  String? _error;
  @override
  void initState() {
    super.initState();
    _terrain = CaveTerrain.cached;
    _height =
        widget.existing?.worldZ ?? _terrain?.height(_world.dx, _world.dy) ?? 0;
    _sync();
    CaveTerrain.bundled
        .then((terrain) {
          if (!mounted) return;
          setState(() {
            _terrain = terrain;
            _height =
                widget.existing?.worldZ ??
                terrain.height(_world.dx, _world.dy) ??
                0;
            _sync();
          });
        })
        .catchError((Object error) {
          if (mounted) {
            setState(() => _error = 'Could not load terrain: $error');
          }
        });
  }

  void _sync() {
    _x.text = _world.dx.toStringAsFixed(2);
    _y.text = _world.dy.toStringAsFixed(2);
    _z.text = _height.toStringAsFixed(2);
  }

  void _move(Offset value) {
    final before = _terrain?.height(_world.dx, _world.dy);
    final after = _terrain?.height(value.dx, value.dy);
    setState(() {
      _world = Offset(
        value.dx.clamp(-24500, 25300),
        value.dy.clamp(-23700, 23700),
      );
      if (before != null && after != null) {
        _height = (_height + after - before).clamp(-2000, 10000);
      }
      _sync();
    });
  }

  bool _readFields() {
    final x = double.tryParse(_x.text),
        y = double.tryParse(_y.text),
        z = double.tryParse(_z.text);
    if (x == null ||
        y == null ||
        z == null ||
        !x.isFinite ||
        !y.isFinite ||
        !z.isFinite ||
        x < -24500 ||
        x > 25300 ||
        y < -23700 ||
        y > 23700 ||
        z < -2000 ||
        z > 10000) {
      setState(
        () => _error = 'Enter valid coordinates within the world map, and height −2000 to 10000.',
      );
      return false;
    }
    setState(() {
      _world = Offset(
        _x.text == _world.dx.toStringAsFixed(2) ? _world.dx : x,
        _y.text == _world.dy.toStringAsFixed(2) ? _world.dy : y,
      );
      _height = _z.text == _height.toStringAsFixed(2) ? _height : z;
      _error = null;
    });
    return true;
  }

  @override
  void dispose() {
    for (final c in [_name, _x, _y, _z]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (!_readFields()) return;
    if (_name.text.trim().isEmpty || _name.text.trim().length > 80) {
      setState(() => _error = 'Enter a cave name of 1–80 characters.');
      return;
    }
    final cave = CaveLocation(
      id:
          widget.existing?.id ??
          'cave_${DateTime.now().microsecondsSinceEpoch.toRadixString(36)}',
      name: _name.text.trim(),
      entrance: _entrance,
      worldX: _world.dx,
      worldY: _world.dy,
      worldZ: _height,
      yaw: _yaw,
      scale: _scale,
    );
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      if (widget.save != null) {
        await widget.save!(cave);
      } else {
        await widget.locations.add(cave);
      }
      if (mounted) Navigator.pop(context, cave);
    } catch (error) {
      if (mounted) {
        setState(() {
          _saving = false;
          _error = error.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(
      !_placing
          ? 'Choose cave entrance'
          : widget.existing == null
          ? 'Add cave'
          : 'Edit cave placement',
    ),
    content: SizedBox(
      width: 940,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: !_placing
              ? [
                  Text(
                    'Select an entrance, then position it on the map.',
                    style: Guide.small(),
                  ),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final entrance in widget.catalog.entrances)
                        SizedBox(
                          width: 180,
                          child: InkWell(
                            key: ValueKey('cave-entrance-${entrance.id}'),
                            onTap: _saving
                                ? null
                                : () => setState(() {
                                    _entrance = entrance.id;
                                    _entranceChosen = true;
                                  }),
                            child: Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                border: Border.all(
                                  color:
                                      _entranceChosen &&
                                          _entrance == entrance.id
                                      ? Guide.blue
                                      : Guide.inkSoft,
                                  width:
                                      _entranceChosen &&
                                          _entrance == entrance.id
                                      ? 3
                                      : 1,
                                ),
                              ),
                              child: Column(
                                children: [
                                  Image.asset(
                                    'assets/acquisition_map/${entrance.image}',
                                    height: 70,
                                    width: 150,
                                    fit: BoxFit.contain,
                                  ),
                                  Text(entrance.name),
                                  if (_entranceChosen &&
                                      _entrance == entrance.id)
                                    const Icon(Icons.check, size: 16),
                                ],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                  Text(
                    'Model previews use simplified lighting; the shrine glow appears in-game.',
                    style: Guide.small(),
                  ),
                ]
              : [
                  TextField(
                    key: const ValueKey('cave-name'),
                    controller: _name,
                    enabled: !_saving,
                    maxLength: 80,
                    decoration: const InputDecoration(labelText: 'Cave name'),
                  ),
                  TextButton.icon(
                    key: const ValueKey('cave-change-entrance'),
                    onPressed: _saving
                        ? null
                        : () => setState(() => _placing = false),
                    icon: const Icon(Icons.edit),
                    label: Text(
                      'Entrance: ${widget.catalog.entrances.firstWhere((e) => e.id == _entrance).name} · Change',
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      TextButton(
                        onPressed: _saving
                            ? null
                            : () => setState(() => _threeD = !_threeD),
                        child: Text(
                          _threeD ? 'Show world map' : 'Show 3D terrain',
                        ),
                      ),
                      const Spacer(),
                      TextButton(
                        key: const ValueKey('cave-ground'),
                        onPressed:
                            _saving ||
                                _terrain?.height(_world.dx, _world.dy) == null
                            ? null
                            : () {
                                setState(() {
                                  _height = _terrain!.height(
                                    _world.dx,
                                    _world.dy,
                                  )!;
                                  _sync();
                                });
                              },
                        child: const Text('Snap to ground'),
                      ),
                    ],
                  ),
                  SizedBox(
                    height: 340,
                    child: _threeD
                        ? _terrain == null
                              ? const Center(child: CircularProgressIndicator())
                              : CaveTerrainPreview(
                                  terrain: _terrain!,
                                  world: _world,
                                  z: _height,
                                  entrance: _entrance,
                                  yaw: _yaw,
                                  scale: _scale,
                                  onMove: _saving ? (_) {} : _move,
                                )
                        : AcquisitionMap(
                            site: CaveLocation(
                              id: 'cave_preview',
                              name: 'Entrance footprint center',
                              entrance: _entrance,
                              worldX: _world.dx,
                              worldY: _world.dy,
                            ).site,
                            onAddCave: _saving ? null : _move,
                            addActionLabel: 'Move cave here',
                          ),
                  ),
                  if (_terrain != null &&
                      _terrain!.height(_world.dx, _world.dy) == null)
                    Text(
                      'Native terrain is unavailable here. Set height manually and check the installed placement.',
                      style: Guide.small(Guide.red),
                    ),
                  Row(
                    children: [
                      for (final entry in [
                        ('X / north', _x, 'cave-x'),
                        ('Y / east', _y, 'cave-y'),
                        ('Z / base height', _z, 'cave-z'),
                      ])
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.all(4),
                            child: TextField(
                              key: ValueKey(entry.$3),
                              controller: entry.$2,
                              enabled: !_saving,
                              decoration: InputDecoration(labelText: entry.$1),
                              onSubmitted: (_) => _readFields(),
                              onEditingComplete: _readFields,
                            ),
                          ),
                        ),
                      TextButton(
                        onPressed: _saving
                            ? null
                            : () {
                                if (_readFields()) {
                                  setState(() {
                                    _height -= 10;
                                    _sync();
                                  });
                                }
                              },
                        child: const Text('Z −10'),
                      ),
                      TextButton(
                        onPressed: _saving
                            ? null
                            : () {
                                if (_readFields()) {
                                  setState(() {
                                    _height += 10;
                                    _sync();
                                  });
                                }
                              },
                        child: const Text('Z +10'),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      Text('Rotation ${_yaw.round()}°'),
                      Expanded(
                        child: Slider(
                          min: -180,
                          max: 180,
                          value: _yaw,
                          onChanged: _saving
                              ? null
                              : (v) => setState(() => _yaw = v),
                        ),
                      ),
                      Text('Size ${(_scale * 100).round()}%'),
                      Expanded(
                        child: Slider(
                          key: const ValueKey('cave-scale'),
                          min: .25,
                          max: 2,
                          value: _scale,
                          onChanged: _saving
                              ? null
                              : (v) => setState(() => _scale = v),
                        ),
                      ),
                    ],
                  ),
                  Text(
                    'The marker is the entrance’s footprint center. Drag in 3D or right-click on the map to move it.\nMoving preserves your height offset above native terrain. Rebuild/install to apply changes.',
                    style: Guide.small(),
                  ),
                  if (_error != null)
                    Text(_error!, style: Guide.small(Guide.red)),
                ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: _saving ? null : () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      TextButton(
        key: ValueKey(_placing ? 'cave-add' : 'cave-entrance-next'),
        onPressed: !_placing
            ? _entranceChosen
                  ? () => setState(() => _placing = true)
                  : null
            : _saving || _terrain == null
            ? null
            : _save,
        child: Text(
          !_placing
              ? 'Position cave'
              : _saving
              ? 'Saving…'
              : widget.existing == null
              ? 'Add cave'
              : 'Save placement',
        ),
      ),
    ],
  );
}
