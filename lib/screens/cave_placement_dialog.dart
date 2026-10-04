import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../services/acquisition_locations.dart';

Future<CaveLocation?> showCavePlacement(
  BuildContext context,
  AcquisitionLocations locations,
  AcquisitionCatalog catalog,
  Offset world,
) => showDialog<CaveLocation>(
  context: context,
  builder: (_) => _CavePlacementDialog(
    locations: locations,
    catalog: catalog,
    world: world,
  ),
);

class _CavePlacementDialog extends StatefulWidget {
  const _CavePlacementDialog({
    required this.locations,
    required this.catalog,
    required this.world,
  });
  final AcquisitionLocations locations;
  final AcquisitionCatalog catalog;
  final Offset world;
  @override
  State<_CavePlacementDialog> createState() => _CavePlacementDialogState();
}

class _CavePlacementDialogState extends State<_CavePlacementDialog> {
  late final _name = TextEditingController(
    text: 'Cave ${widget.locations.caves.length + 1}',
  );
  late String _entrance = widget.catalog.entrances.first.id;
  bool _saving = false;
  String? _error;
  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    if (_name.text.trim().isEmpty || _name.text.trim().length > 80) {
      setState(() => _error = 'Enter a cave name of 1–80 characters.');
      return;
    }
    final cave = CaveLocation(
      id: 'cave_${DateTime.now().microsecondsSinceEpoch.toRadixString(36)}',
      name: _name.text.trim(),
      entrance: _entrance,
      worldX: widget.world.dx,
      worldY: widget.world.dy,
    );
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.locations.add(cave);
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
    title: const Text('Add cave'),
    content: SizedBox(
      width: 620,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              key: const ValueKey('cave-name'),
              controller: _name,
              enabled: !_saving,
              maxLength: 80,
              decoration: const InputDecoration(labelText: 'Cave name'),
            ),
            Text('Choose the entrance appearance.', style: Guide.small()),
            Text(
              'Model previews use simplified lighting.',
              style: Guide.small(),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                for (final entrance in widget.catalog.entrances)
                  SizedBox(
                    width: 180,
                    child: InkWell(
                      key: ValueKey('cave-entrance-${entrance.id}'),
                      onTap: _saving
                          ? null
                          : () => setState(() => _entrance = entrance.id),
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: _entrance == entrance.id
                                ? Guide.blue
                                : Guide.inkSoft,
                            width: _entrance == entrance.id ? 3 : 1,
                          ),
                        ),
                        child: Column(
                          children: [
                            Image.asset(
                              'assets/acquisition_map/${entrance.image}',
                              height: 100,
                              width: 160,
                              fit: BoxFit.contain,
                            ),
                            const SizedBox(height: 6),
                            Text(entrance.name, textAlign: TextAlign.center),
                            if (_entrance == entrance.id)
                              const Icon(Icons.check, size: 20),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Saved map placement. The cave interior and in-game acquisition will be connected later.',
              style: Guide.small(),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(_error!, style: Guide.small(Guide.red)),
              ),
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
        key: const ValueKey('cave-add'),
        onPressed: _saving ? null : _add,
        child: Text(_saving ? 'Saving…' : 'Add cave'),
      ),
    ],
  );
}
