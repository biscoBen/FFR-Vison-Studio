import 'package:flutter/material.dart';

import '../../design/theme.dart';
import '../../services/acquisition.dart';
import '../acquisition_map.dart';

class AcquisitionStep extends StatefulWidget {
  const AcquisitionStep({super.key, required this.unit, required this.set});
  final Map<String, dynamic> unit;
  final ValueChanged<Map<String, dynamic>> set;

  @override
  State<AcquisitionStep> createState() => _AcquisitionStepState();
}

class _AcquisitionStepState extends State<AcquisitionStep> {
  late Acquisition _preferences;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final saved = widget.unit[Acquisition.field];
    _preferences = Acquisition.valid(saved)
        ? Acquisition.fromJson(saved as Map)
        : Acquisition.initial();
    if (!Acquisition.valid(saved)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) widget.set({Acquisition.field: _preferences.toJson()});
      });
    }
  }

  @override
  void didUpdateWidget(covariant AcquisitionStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.unit['key'] != widget.unit['key']) {
      _load();
    } else if (Acquisition.valid(widget.unit[Acquisition.field])) {
      _preferences = Acquisition.fromJson(
        widget.unit[Acquisition.field] as Map,
      );
    }
  }

  void _change(Acquisition value) {
    setState(() => _preferences = value);
    widget.set({Acquisition.field: value.toJson()});
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SwitchListTile(
            key: const ValueKey('acquisition-hide'),
            contentPadding: EdgeInsets.zero,
            title: const Text('Hide for spoilers'),
            value: _preferences.hideSpoilers,
            onChanged: (value) =>
                _change(_preferences.copyWith(hideSpoilers: value)),
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
                  value: _preferences.random,
                  onChanged: (value) => _change(_preferences.reroll(value)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _preferences.hideSpoilers
                    ? Padding(
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        child: Text('Location hidden', style: Guide.small()),
                      )
                    : Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        children: [
                          for (final site in Acquisition.sites)
                            SizedBox(
                              width: 170,
                              child: CheckboxListTile(
                                key: ValueKey('acquisition-site-${site.id}'),
                                dense: true,
                                contentPadding: EdgeInsets.zero,
                                controlAffinity:
                                    ListTileControlAffinity.leading,
                                title: Text(site.label),
                                value: _preferences.location == site.id,
                                onChanged: _preferences.random
                                    ? null
                                    : (_) => _change(
                                        _preferences.copyWith(
                                          location: site.id,
                                        ),
                                      ),
                              ),
                            ),
                        ],
                      ),
              ),
            ],
          ),
          Text(
            'Acquisition preview — saved for planning; game installation still uses the existing acquisition rules.',
            style: Guide.small(),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: AcquisitionMap(
              site: _preferences.hideSpoilers ? null : _preferences.site,
            ),
          ),
        ],
      ),
    );
  }
}
