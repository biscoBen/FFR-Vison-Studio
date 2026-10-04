import 'dart:convert';

import 'package:flutter/material.dart';

import '../../design/theme.dart';
import '../../services/acquisition.dart';
import '../../services/acquisition_locations.dart';
import '../acquisition_map.dart';
import '../cave_placement_dialog.dart';

class AcquisitionStep extends StatefulWidget {
  const AcquisitionStep({
    super.key,
    required this.unit,
    required this.set,
    required this.locations,
  });
  final Map<String, dynamic> unit;
  final ValueChanged<Map<String, dynamic>> set;
  final AcquisitionLocations locations;

  @override
  State<AcquisitionStep> createState() => _AcquisitionStepState();
}

class _AcquisitionStepState extends State<AcquisitionStep> {
  Acquisition? _preferences;
  AcquisitionCatalog? _catalog;
  bool _initialized = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final saved = widget.unit[Acquisition.field];
    _preferences = Acquisition.valid(saved)
        ? Acquisition.fromJson(saved as Map)
        : null;
    _initialized = false;
    _error = null;
  }

  void _initialize(AcquisitionCatalog catalog) {
    _catalog = catalog;
    if (_initialized) return;
    _initialized = true;
    _preferences = _preferences == null
        ? widget.locations.initial(catalog)
        : widget.locations.migrate(_preferences!, catalog);
    final value = _preferences!;
    final key = widget.unit['key'];
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted || widget.unit['key'] != key) return;
      if (value.cave != null) {
        try {
          await widget.locations.add(CaveLocation.fromJson(value.cave!));
        } catch (error) {
          if (mounted) setState(() => _error = error.toString());
          return;
        }
      }
      if (mounted &&
          widget.unit['key'] == key &&
          json.encode(_preferences!.toJson()) == json.encode(value.toJson()) &&
          json.encode(widget.unit[Acquisition.field]) !=
              json.encode(value.toJson())) {
        widget.set({Acquisition.field: value.toJson()});
      }
    });
  }

  @override
  void didUpdateWidget(covariant AcquisitionStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.unit['key'] != widget.unit['key'] ||
        oldWidget.locations != widget.locations) {
      _load();
    } else if (Acquisition.valid(widget.unit[Acquisition.field])) {
      final saved = Acquisition.fromJson(widget.unit[Acquisition.field] as Map);
      _preferences = _catalog == null
          ? saved
          : widget.locations.migrate(saved, _catalog!);
    }
  }

  void _change(Acquisition value) {
    setState(() => _preferences = value);
    widget.set({Acquisition.field: value.toJson()});
  }

  void _choose(AcquisitionSite site) =>
      _change(widget.locations.choose(_preferences!, site));

  Future<void> _addCave(Offset world) async {
    final added = await showCavePlacement(
      context,
      widget.locations,
      _catalog!,
      world,
    );
    if (!mounted || added == null) return;
    if (!_preferences!.random) _choose(added.site);
  }

  Widget _choice(
    String kind,
    String title,
    List<AcquisitionSite> sites,
    AcquisitionSite? selected,
  ) => Row(
    children: [
      SizedBox(
        width: 95,
        child: CheckboxListTile(
          key: ValueKey('acquisition-kind-$kind'),
          dense: true,
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          title: Text(title),
          value: selected?.kind == kind,
          onChanged: _preferences!.random || sites.isEmpty
              ? null
              : (_) =>
                    _choose(selected?.kind == kind ? selected! : sites.first),
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: DropdownButton<String>(
          key: ValueKey('acquisition-$kind-list'),
          isExpanded: true,
          value:
              selected?.kind == kind && sites.any((s) => s.id == selected!.id)
              ? selected!.id
              : null,
          hint: Text(kind == 'shop' ? 'Choose vendor' : 'Choose custom cave'),
          items: [
            for (final site in sites)
              DropdownMenuItem(
                value: site.id,
                child: Text(
                  site.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
          ],
          onChanged: _preferences!.random
              ? null
              : (id) => _choose(sites.firstWhere((s) => s.id == id)),
        ),
      ),
    ],
  );

  @override
  Widget build(BuildContext context) => FutureBuilder<AcquisitionCatalog>(
    future: AcquisitionCatalog.bundled,
    initialData: AcquisitionCatalog.cached,
    builder: (context, snapshot) {
      if (snapshot.hasError) {
        return Center(
          child: Text(
            'The acquisition catalog could not be loaded: ${snapshot.error}',
          ),
        );
      }
      final catalog = snapshot.data;
      if (catalog == null) {
        return const Center(child: CircularProgressIndicator());
      }
      _initialize(catalog);
      return AnimatedBuilder(
        animation: widget.locations,
        builder: (context, _) {
          final preferences = _preferences!;
          final selected = widget.locations.site(preferences, catalog);
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SwitchListTile(
                  key: const ValueKey('acquisition-hide'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Hide for spoilers'),
                  value: preferences.hideSpoilers,
                  onChanged: (value) =>
                      _change(preferences.copyWith(hideSpoilers: value)),
                ),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 150,
                      child: SwitchListTile(
                        key: const ValueKey('acquisition-random'),
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Random'),
                        value: preferences.random,
                        onChanged: (value) => _change(
                          widget.locations.reroll(preferences, value, catalog),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: preferences.hideSpoilers
                          ? Padding(
                              padding: const EdgeInsets.symmetric(vertical: 18),
                              child: Text(
                                'Location hidden',
                                style: Guide.small(),
                              ),
                            )
                          : Column(
                              children: [
                                _choice(
                                  'shop',
                                  'Shop',
                                  catalog.vendors,
                                  selected,
                                ),
                                _choice(
                                  'cave',
                                  'Cave',
                                  widget.locations.caves
                                      .map((v) => v.site)
                                      .toList(),
                                  selected,
                                ),
                              ],
                            ),
                    ),
                  ],
                ),
                if (!preferences.hideSpoilers && selected?.hasPosition == false)
                  Text(
                    'This vendor has no mapped overworld location in the supplied game data.',
                    style: Guide.small(),
                  ),
                if (!preferences.hideSpoilers && selected == null)
                  Text(
                    'The saved location is not in the current catalog. Choose another location to change it.',
                    style: Guide.small(),
                  ),
                Text(
                  'Acquisition preview — locations are saved in Studio; in-game placement will be connected later.',
                  style: Guide.small(),
                ),
                if (_error != null || widget.locations.loadError != null)
                  Text(
                    _error ??
                        'The saved cave list could not be loaded and has been preserved: ${widget.locations.loadError}',
                    style: Guide.small(Guide.red),
                  ),
                const SizedBox(height: 12),
                Expanded(
                  child: AcquisitionMap(
                    site: preferences.hideSpoilers ? null : selected,
                    caves: preferences.hideSpoilers
                        ? const []
                        : widget.locations.caves.map((v) => v.site).toList(),
                    onAddCave: widget.locations.loadError == null
                        ? _addCave
                        : null,
                  ),
                ),
                Text(
                  '${widget.locations.caves.length} / 30 planned caves · Right-click the map to add a cave.',
                  style: Guide.small(),
                ),
              ],
            ),
          );
        },
      );
    },
  );
}
