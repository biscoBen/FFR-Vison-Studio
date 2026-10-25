import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';

import 'overworld_catalog.dart';
import 'battle_voice.dart';

class OverworldAppearance {
  // Keep existing portable Vagrant Rain choices valid.
  static const model = 'vagrant_knight_rain';
  static const sheet =
      'assets/existing_visions/payload/vagrant_knight_rain_field.png';
  static const profile = <String, dynamic>{'version': 1, 'model': model};
  static Map<String, dynamic> get models =>
      overworldCatalog['models'] as Map<String, dynamic>;
  static const nativeGuests = <String,Map<String,dynamic>>{
    'native_charlotte': {'name':'Charlotte','nativeId':1016,'nativeField':470,'directions':4,
      'portrait':'assets/native_portraits/100004306.png','form':'native_charlotte'},
  };

  static int? nativeId(String model) => nativeGuests[model]?['nativeId'] as int? ?? BattleVoice.names.keys
      .where((id) => model == 'native_party_$id').firstOrNull;
  static Map<String, dynamic> data(String model) {
    if (nativeGuests.containsKey(model)) return Map<String,dynamic>.from(nativeGuests[model]!);
    final id = nativeId(model);
    return id != null
      ? {'name': BattleVoice.names[id], 'directions': 8, 'nativeParty': id, 'form': model}
      : models[model] as Map<String, dynamic>;
  }
  static Map<String, dynamic> profileFor(String model) {
    if (!models.containsKey(model) && nativeId(model) == null) {
      throw FormatException('Unsupported overworld model.');
    }
    return {'version': 1, 'model': model};
  }

  static List<Map<String, dynamic>> get entries => [
    for (final e in BattleVoice.names.entries)
      {'id':'native_party_${e.key}', 'name':e.value, 'jpname':'',
       'nativeParty':e.key, 'packs':['native_party_${e.key}'], 'hasSprites':true, 'directions':8},
    for (final e in nativeGuests.entries)
      {...e.value,'id':e.key,'jpname':'','packs':[e.key],'hasSprites':true},
    ...([
    for (final entry in models.entries)
      {
        'id': entry.key,
        'name': entry.value['name'],
        'jpname': '',
        'ffbeId': entry.value['base'],
        'iconForm': entry.value['form'],
        'packs': [entry.value['form']],
        'hasSprites': true,
        'directions': entry.value['directions'],
      },
    ]..sort((a, b) => (a['name'] as String).compareTo(b['name'] as String))),
  ];

  static Map<String, dynamic> detailFor(String model) {
    final entry = data(model);
    return {
      'id': model,
      'name': entry['name'],
      'jpname': '',
      'maxForm': entry['form'],
      'forms': {entry['form']: <String, dynamic>{}},
    };
  }

  static bool valid(dynamic value) =>
      value is Map &&
      value.length == 2 &&
      value['version'] is int &&
      value['version'] == 1 &&
      value['model'] is String &&
      (models.containsKey(value['model']) || nativeId(value['model'] as String) != null);

  static Archive? _archive;
  static Future<Archive>? _loading;
  static final _bytes = <String, Uint8List>{};
  static Future<Archive> _loadArchive() async {
    if (_archive != null) {
      return _archive!;
    }
    return _loading ??= () async {
      try {
        final raw = await rootBundle.load(
          'assets/existing_visions/payload/overworld_assets.zip',
        );
        final bytes = raw.buffer.asUint8List(
          raw.offsetInBytes,
          raw.lengthInBytes,
        );
        if (sha256.convert(bytes).toString() !=
            overworldCatalog['archive_sha256']) {
          throw StateError(
            'The field sprite archive failed checksum validation.',
          );
        }
        return _archive = ZipDecoder().decodeBytes(bytes);
      } finally {
        _loading = null;
      }
    }();
  }

  static Future<Uint8List> assetBytes(String model, String kind) async {
    final entry = data(model);
    final key = entry[kind] as String;
    if (_bytes.containsKey(key)) {
      return _bytes[key]!;
    }
    final archive = await _loadArchive();
    final file = archive.findFile(entry[kind] as String);
    if (file == null) {
      throw StateError('A field sprite asset is missing.');
    }
    final bytes = Uint8List.fromList(file.content);
    if (sha256.convert(bytes).toString() != entry['${kind}_sha256']) {
      throw StateError('A field sprite asset failed checksum validation.');
    }
    return _bytes[key] = bytes;
  }

  static List<List<int>> frames(String model, String motion, int direction) => [
    for (final frame
        in (data(model)['motions'] as Map)['$motion$direction'] as List)
      (frame as List).cast<int>(),
  ];
}
