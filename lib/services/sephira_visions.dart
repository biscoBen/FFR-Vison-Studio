import 'dart:convert';

import 'package:flutter/services.dart';

import 'character_config.dart';
import 'acquisition.dart';
import 'crystal_fina.dart';

/// Optional, editable presets. Membership lives in portable character configs;
/// disabled entries retain their IDs and edits but are omitted by the builder.
class SephiraVisions {
  static const field = 'sephiraVision';
  static const asset = 'assets/sephira_visions/catalog.json';
  static const retired = {'great_dragon'};
  /// Permanent save identities. Never reuse retired slots or choose an ID by
  /// roster order. These also match the standalone Fina identity (13503).
  static const fixedIds = <String, int>{
    'a2': 13502, 'christine': 13501, 'crystal_fina': 13503,
    'barusa': 13531, 'fran': 13504, 'lunafreya': 13505,
    'minfilia': 13506, 'folka': 13507, 'fryevia': 13508,
    'lenneth': 13509, 'lila': 13510, 'mystea': 13511,
    'reberta': 13512, 'snow_white': 13513, 'aria': 13514,
    'eiko': 13515, 'alice': 13516, 'mog': 13517, 'lilith': 13518,
    'freya': 13519, 'trance_terra': 13521, 'ariana': 13522,
    'elephim': 13523, 'jade': 13524, 'primm': 13525, 'relm': 13526,
    'rikku': 13527, 'nalu': 13528, 'elza': 13529, 'lunera': 13530,
  };

  /// Kit templates retain their historical IDs for migration comparisons.
  /// Instantiate them at the permanent identity with all private links remapped.
  static Map<String, dynamic> fixedProfile(Map<String, dynamic> preset) {
    final profile = preset['profile'] as Map<String, dynamic>?;
    final id = fixedIds[preset['id']];
    if (profile == null || id == null) throw StateError('This Sephira preset has no fixed save identity.');
    return CharacterConfig.restore(profile, [], replacing: {...profile, 'id': id});
  }

  /// Repair older allocations by preset identity, preserving whole kits and all
  /// cross-vision references. Unrelated characters may never be renumbered to
  /// make room; an occupied fixed slot fails before the caller writes anything.
  static List<dynamic> pinIdentities(List<dynamic> units) {
    final ids = [for (final u in units)
      member(u as Map) ? fixedIds[presetId(u)] ?? u['id'] : u['id']];
    if (!units.asMap().entries.any((e) => e.value['id'] != ids[e.key])) return units;
    final sources = [for (final u in units) CharacterConfig.copy(u as Map<String,dynamic>)..remove(field)];
    final targets = [for (var i=0; i<units.length; i++) {...units[i] as Map<String,dynamic>, 'id':ids[i]}];
    final next = CharacterConfig.restoreAll(sources, [], targets);
    for (var i=0; i<next.length; i++) {
      if (next[i]['id'] != ids[i]) {
        throw StateError('A fixed Sephira vision ID is occupied by another character. '
            'Your roster was kept; remove the conflicting added entry before applying the update.');
      }
      if ((units[i] as Map).containsKey(field)) next[i][field] = CharacterConfig.copy(units[i] as Map<String,dynamic>)[field];
    }
    CharacterConfig.validateAll(next);
    return next;
  }
  static Future<List<Map<String, dynamic>>> get bundled async =>
      parse(await rootBundle.loadString(asset));

  static List<Map<String, dynamic>> parse(String contents) {
    final document = json.decode(contents);
    if (document is! Map || document['schema'] != 1 || document['presets'] is! List) {
      throw const FormatException('Unsupported Sephira vision catalog.');
    }
    final ids = <String>{};
    final result = <Map<String, dynamic>>[];
    for (final value in document['presets']) {
      if (value is! Map<String, dynamic> || value['id'] is! String ||
          !ids.add(value['id'] as String) || value['name'] is! String ||
          value['theme'] is! String) {
        throw const FormatException('Invalid Sephira vision preset.');
      }
      final profile = value['profile'];
      if (profile != null) {
        if (profile is! Map<String, dynamic>) {
          throw const FormatException('Invalid Sephira vision profile.');
        }
        CharacterConfig.validate(profile);
      }
      result.add(value);
    }
    final profiles = result.map((p) => p['profile']).whereType<Map<String, dynamic>>().toList();
    if (profiles.isNotEmpty) CharacterConfig.validateAll(profiles);
    return result;
  }

  static bool member(Map unit) => unit[field] is Map;
  static String? presetId(Map unit) => member(unit) ? unit[field]['preset'] as String? : null;
  static bool retiredMember(Map unit) => retired.contains(presetId(unit));
  static bool included(Map unit) => !member(unit) ||
      (!retiredMember(unit) && unit[field]['enabled'] == true);

  /// Change the reviewed artwork/resonance once, retaining the saved identity,
  /// complete regular kit, mastery grants and acquisition edits.
  static Map<String, dynamic> repairAppearance(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (!member(unit) || unit['native'] != null || unit['party'] != null) return unit;
    final update = presets.where((p) => p['id'] == presetId(unit)).firstOrNull?['appearanceUpdate'];
    if (update is! Map || update['schema'] != 1 ||
        (unit['sephiraAppearanceRevision'] as int? ?? 0) >= update['version'] ||
        unit['ffbe']?['id'] != update['from']) {
      return unit;
    }
    final result = CharacterConfig.copy(unit);
    for (final entry in (update['fields'] as Map).entries) {
      result[entry.key as String] = json.decode(json.encode(entry.value));
    }
    result['ffbe']['dir'] = 'units/ffbe/${unit['key']}/sprites/${result['ffbe']['id']}';
    (result['command'] as Map).addAll(update['command'] as Map);
    (result['master'] as Map).addAll(update['master'] as Map);
    result['sephiraAppearanceRevision'] = update['version'];
    CharacterConfig.validate(result);
    return result;
  }

  static bool hasRecipeUpdate(Map unit, List<Map<String, dynamic>> presets) {
    final id = presetId(unit);
    if (id == null) return false;
    final current = unit['sephiraRecipe'];
    return presets.any((p) {
      final profile = p['profile'];
      final latest = profile is Map ? profile['sephiraRecipe'] : null;
      return p['id'] == id && latest is int &&
          (latest > (current is int ? current : 0) ||
           (p['kitUpdate'] is Map && (unit['sephiraKitRevision'] as int? ?? 0) < p['kitUpdate']['version']) ||
           (p['mrRestoration'] is Map && (unit['sephiraMrRevision'] as int? ?? 0) < p['mrRestoration']['version']));
    });
  }

  /// Restore the original equipable MR skills once, retaining custom recipes,
  /// permanent rewards and all unrelated settings. Full edited tiers stay open.
  static Map<String, dynamic> repairEquipableMr(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets, {bool strict = false,
  }) {
    if (!member(unit) || (unit['sephiraRecipe'] as int? ?? 0) < 7) return unit;
    final update = presets.where((p)=>p['id']==presetId(unit)).firstOrNull?['mrRestoration'];
    if (update is! Map || (unit['sephiraMrRevision'] as int? ?? 0)>=update['version']) return unit;
    try {
      final result=CharacterConfig.copy(unit);
      bool same(List a,List b)=>a[0]==b[0] && a[1]==b[1] && (a.length>2?a[2]:-1)==(b.length>2?b[2]:-1);
      for (final step in update['steps'] as List? ?? [update]) {
        if ((result['sephiraMrRevision'] as int? ?? 0)>=step['version']) continue;
        for (final op in step['mr'] as List) {
          final choices=(result['synchro'][op['rank']] as List).where((g)=>['ActiveSkill','PassiveSkill'].contains(g[0])).toList();
          if (choices.length!=1 || (!same(choices.single as List,op['from'] as List) && !same(choices.single as List,op['to'] as List))) {
            throw StateError('${unit['en']} MR${op['rank']} was edited. Resolve this reward before applying its MR update.');
          }
        }
        for (final op in step['mr'] as List) {
          result['synchro'][op['rank']]=[for (final g in result['synchro'][op['rank']] as List)
            if (same(g as List,op['from'] as List)) List<dynamic>.from(op['to'] as List) else g];
        }
        for (final op in step['remove'] as List) {
          for (final tier in result['awakening'] as List) {
            (tier as List).removeWhere((g)=>g[0]==op[1] && g[1]==op[2]);
          }
        }
        for (final op in step['move'] as List? ?? []) {
          final found=<({int rank, List grant})>[
            for (var rank=0;rank<4;rank++) for (final g in result['awakening'][rank] as List)
              if (g[0]=='ActiveSkill' && (result['skills'][g[1].toString()] as Map?)?['from']==op[0])
                (rank:rank,grant:g as List),
          ];
          if (found.length>1) throw StateError('${unit['en']} has multiple learned copies of its moved awakening skill.');
          if (found.isEmpty) continue;
          final match=found.single;
          final target=op[2] as int;
          if (match.rank==target) continue;
          if (match.rank!=op[1]) throw StateError('${unit['en']} has an edited awakening placement. Resolve it before applying the update.');
          if ((result['awakening'][target] as List).length>=8) {
            throw StateError('${unit['en']} tier ${target+1} needs an awakening slot for its MR update.');
          }
          (result['awakening'][match.rank] as List).remove(match.grant);
          (result['awakening'][target] as List).add(match.grant);
        }
        for (final op in step['add'] as List) {
          final preferred=op[0] as int;
          int? rank;
          if (step['exactAwakeningRanks']==true) {
            final found=[for (var r=0;r<4;r++) if ((result['awakening'][r] as List).any((g)=>g[0]==op[1] && g[1]==op[2])) r];
            if (found.length==1 && found.single==preferred) continue;
            if (found.isNotEmpty) throw StateError('${unit['en']} has an edited awakening bonus placement. Resolve it before applying the update.');
            rank=(result['awakening'][preferred] as List).length<8?preferred:null;
          } else {
            if (['awakening','synchro'].any((f)=>(result[f] as List).any((t)=>(t as List).any((g)=>g[0]==op[1] && g[1]==op[2])))) continue;
            rank=[for (var r=preferred;r<4;r++) r].where((r)=>(result['awakening'][r] as List).length<8).firstOrNull;
          }
          if (rank==null) throw StateError('${unit['en']} needs an awakening slot in tier ${preferred+1} for its MR update. Move an extra ability first.');
          (result['awakening'][rank] as List).add([op[1],op[2],-1]);
        }
        for (final entry in (step['passiveText'] as Map? ?? {}).entries) {
          (result.putIfAbsent('sephiraPassiveText',()=> <String,dynamic>{}) as Map)
              .putIfAbsent(entry.key,()=>Map<String,dynamic>.from(entry.value as Map));
        }
        result['sephiraMrRevision']=step['version'];
      }
      CharacterConfig.validate(result);
      return result;
    } on StateError {
      if (strict) rethrow;
      return unit;
    }
  }

  /// Apply the two reviewed kits once. Preserve private skill identities and
  /// combat edits, unrelated learned grants, stats, artwork and acquisition.
  /// A full edited tier stays openable; the explicit update reports the issue.
  static Map<String, dynamic> repairKit(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets, {bool strict = false,
  }) {
    if (unit['native'] != null || unit['party'] != null) return unit;
    final id = presetId(unit) ?? (CrystalFina.matches(unit) ? 'crystal_fina' : null);
    final preset = presets.where((p) => p['id'] == id).firstOrNull;
    final update = preset?['kitUpdate'];
    if (update is! Map || (unit['sephiraKitRevision'] as int? ?? 0) >= update['version']) return unit;
    try {
      final result = CharacterConfig.copy(unit);
      // Explicit reward moves are reviewed together with the awakening kit.
      // Validate the whole batch before changing anything, keeping edited MRs open.
      final rewardMoves = update['mr'] as List? ?? [];
      for (final op in rewardMoves) {
        final kinds={'ActiveSkill','PassiveSkill',op['from'][0],op['to'][0]};
        final choices = (result['synchro'][op['rank']] as List)
            .where((g) => kinds.contains(g[0])).toList();
        if (choices.length!=1 ||
            (json.encode(choices.single)!=json.encode(op['from']) && json.encode(choices.single)!=json.encode(op['to']))) {
          throw StateError('${unit['en']} MR${op['rank']} was edited. Resolve it before applying its kit update.');
        }
      }
      if (update['mrOnly'] == true) {
        for (final op in rewardMoves) {
          result['synchro'][op['rank']] = [for (final grant in result['synchro'][op['rank']] as List)
            if (json.encode(grant)==json.encode(op['from']) || json.encode(grant)==json.encode(op['to']))
              List<dynamic>.from(op['to'] as List) else grant];
        }
        result['sephiraKitRevision'] = update['version'];
        CharacterConfig.validate(result);
        return result;
      }
      final template = CharacterConfig.restore(preset!['profile'] as Map<String, dynamic>, [], replacing: unit);
      final owned = result['skills'] as Map;
      String grantKey(List g) {
        final recipe = g[0] == 'ActiveSkill' ? owned[g[1].toString()] as Map? : null;
        return recipe != null ? 'custom:${recipe['from']}' : '${g[0]}:${g[1]}';
      }
      final managed = Set<String>.from(update['managed'] as List);
      if (!member(unit) && id == 'crystal_fina') {
        // The earlier independent preset had a different borrowed kit.
        for (final source in [240230,240010,210050,230060,210120,445020,230070,230140,300110]) {
          managed.add('ActiveSkill:$source');
        }
        managed.add('custom:445020');
      }
      final awakening = <List<dynamic>>[];
      for (var rank = 0; rank < 4; rank++) {
        final grants = <dynamic>[];
        for (final raw in template['awakening'][rank] as List) {
          final grant = List<dynamic>.from(raw as List);
          final recipe = grant[0] == 'ActiveSkill' ? template['skills'][grant[1].toString()] as Map? : null;
          if (recipe != null) {
            final existing = owned.entries.where((e) => (e.value as Map)['from'] == recipe['from']).toList();
            if (existing.length > 1) throw StateError('${unit['en']} has multiple copies of ${recipe['en']}. Choose one before applying its kit update.');
            if (existing.isNotEmpty) {
              grant[1] = int.parse(existing.single.key.toString());
            } else {
              final occupied = {for (final key in owned.keys) for (final delta in [0,1,2]) int.parse(key.toString()) + delta};
              final base = CharacterConfig.skillBase(unit['id'] as int);
              final target = [grant[1] as int, for (var n = 1; n < 32; n++) base+n*3]
                  .where((v) => [v,v+1,v+2].every((x) => !occupied.contains(x))).firstOrNull;
              if (target == null) throw StateError('${unit['en']} has no space for the updated kit.');
              final copy = CharacterConfig.copy(recipe as Map<String, dynamic>);
              copy['jp'] = '${copy['jp']}_KitUpdate_$target';
              owned[target.toString()] = copy;
              grant[1] = target;
            }
          }
          grants.add(grant);
        }
        grants.addAll((result['awakening'][rank] as List).where((g) => !managed.contains(grantKey(g as List))));
        if (grants.length > 8) throw StateError('${unit['en']} tier ${rank+1} has no room for its kit update. Move an extra ability first.');
        awakening.add(grants);
      }
      result['awakening'] = awakening;
      for (final op in rewardMoves) {
        result['synchro'][op['rank']] = [for (final grant in result['synchro'][op['rank']] as List)
          if (json.encode(grant)==json.encode(op['from']) || json.encode(grant)==json.encode(op['to']))
            List<dynamic>.from(op['to'] as List) else grant];
      }
      if (rewardMoves.isNotEmpty) {
        result['sephiraPassiveText'] = CharacterConfig.copy(template['sephiraPassiveText'] as Map<String,dynamic>);
      }
      final replacement = update['passiveReplacement'];
      if (replacement is List) {
        for (final tier in result['synchro'] as List) {
          for (final g in tier as List) {
            if (g[0] == 'PassiveSkill' && g[1] == replacement[0]) g[1] = replacement[1];
          }
        }
        final labels = Map<String, dynamic>.from(result['sephiraPassiveText'] as Map? ?? {});
        final retained = {for (final f in ['awakening','synchro']) for (final tier in result[f] as List)
          for (final g in tier as List) if (g[0] == 'PassiveSkill') g[1]};
        if (!retained.contains(replacement[0])) labels.remove(replacement[0].toString());
        labels[replacement[1].toString()] = preset['profile']['sephiraPassiveText'][replacement[1].toString()];
        result['sephiraPassiveText'] = labels;
      }
      // Retain old recipe definitions for already-learned/save references.
      // Their removed awakening grants no longer expose them in this kit.
      // Spirits read this vision's MR rows through their stable VisionId. Only
      // replace our previous generic text, retaining deliberate descriptions.
      final master = result['master'] as Map;
      if ((update['masterDescriptions'] as List? ?? []).contains(master['desc'])) {
        master['desc'] = template['master']['desc'];
      }
      result['sephiraKitRevision'] = update['version'];
      CharacterConfig.validate(result);
      return result;
    } on StateError {
      if (strict) rethrow;
      return unit;
    }
  }

  static bool valid(dynamic value) => value is Map && value.length == 3 &&
      value['version'] == 1 && value['preset'] is String &&
      (value['preset'] as String).isNotEmpty && value['enabled'] is bool;

  /// Replace the shipped audio-off default once, without resetting the kit.
  /// The marker lets a later explicit mute remain muted across restarts.
  static Map<String, dynamic> repairLbAudio(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (unit['native'] != null || unit['party'] != null) return unit;
    final id = presetId(unit) ?? (CrystalFina.matches(unit) ? 'crystal_fina' : null);
    final expected = presets.where((p) => p['id'] == id).firstOrNull?['profile'];
    final lb = unit['lb_custom'];
    if (expected is! Map || lb is! Map || lb['sephiraAudio'] == 1 ||
        unit['ffbe']?['id'] != expected['ffbe']?['id'] ||
        lb['ffbe_lb_id'] != expected['lb_custom']?['ffbe_lb_id'] ||
        lb['presentation'] != 'ffbe' ||
        !['none', 'native'].contains(lb['audio']) ||
        lb['audio_bank'] != null || lb['audio_system_bank'] != null) {
      return unit;
    }
    final result = CharacterConfig.copy(unit);
    (result['lb_custom'] as Map).addAll(
        <String, dynamic>{'audio': 'native', 'audio_codec': 'host', 'sephiraAudio': 1});
    return result;
  }

  /// Replace only our shipped technical descriptions, retaining deliberate text
  /// edits and every identity, learned reward, combat field and acquisition.
  static Map<String, dynamic> repairDescriptions(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (unit['native'] != null || unit['party'] != null) return unit;
    final id = presetId(unit) ?? (CrystalFina.matches(unit) ? 'crystal_fina' : null);
    final preset = presets.where((p) => p['id'] == id).firstOrNull;
    final update = preset?['descriptionUpdate'];
    if (update is! Map || update['schema'] != 1) return unit;
    var changed = false;
    final result = CharacterConfig.copy(unit);
    final skills = result['skills'];
    if (skills is Map) {
      for (final recipe in skills.values.whereType<Map>()) {
        for (final text in (update['skills'] as List).whereType<Map>()) {
          if (recipe['from'] == text['from'] &&
              recipe['desc'] == text['before']) {
            recipe['desc'] = text['after'];
            recipe['descAuto'] = false;
            changed = true;
            break;
          }
        }
      }
    }
    final lb = result['lb_custom'];
    final text = update['resonance'];
    final required = text is Map ? text['requiresActive'] : null;
    final matchingSkills = required == null ? null : <int>{
      for (final field in ['awakening', 'synchro'])
        for (final tier in result[field] as List)
          for (final grant in tier as List)
            if (grant[0] == 'ActiveSkill' && (grant[1] == required ||
                (skills as Map?)?[grant[1].toString()]?['from'] == required)) grant[1] as int,
    };
    final hasRequired = matchingSkills == null || matchingSkills.length == 1;
    if (lb is Map && text is Map && lb['from'] == text['from'] &&
        hasRequired && !(required != null && (lb['set'] as Map?)?.containsKey('effectBundleList') == true) &&
        (lb['desc'] == text['before'] || (text['previous'] as List? ?? []).contains(lb['desc']))) {
      lb['desc'] = text['after'];
      lb['descAuto'] = false;
      changed = true;
    }
    return changed ? result : unit;
  }

  /// Move command-bound MR defaults into the vision's existing bonus slots.
  /// General bonuses take their place in MR; complete kits keep the same
  /// abilities, passive count, AP costs and permanent stats.
  static Map<String, dynamic> repairMasteryScope(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (unit['native'] != null || unit['party'] != null ||
        (unit['sephiraRecipe'] as int? ?? 0) < 7) { return unit; }
    final preset = presets.where((p) => p['id'] == presetId(unit)).firstOrNull;
    final update = preset?['masteryScopeUpdate'];
    if (update is! Map || update['schema'] != 1) return unit;
    var changed = false;
    final result = CharacterConfig.copy(unit);
    for (final swap in update['swaps'] as List) {
      final rank = swap[0] as int, bound = swap[1] as int, general = swap[2] as int;
      final reward = (result['synchro'][rank] as List).where((g) =>
          g[0] == 'PassiveSkill' && g[1] == bound).firstOrNull;
      if (reward == null) continue; // Repaired already, or deliberately edited.
      final awakening = result['awakening'] as List;
      final bonus = awakening.expand((t) => t as List).where((g) =>
          g[0] == 'PassiveSkill' && g[1] == general).firstOrNull;
      if (bonus != null) {
        bonus[1] = bound;
      } else {
        final target = awakening.skip(swap[3] as int).where((t) => (t as List).length < 8).firstOrNull;
        if (target == null) return unit; // Keep an edited, full kit openable.
        (target as List).add(['PassiveSkill',bound,-1]);
      }
      reward[1] = general;
      changed = true;
    }
    if (!changed) return unit;
    result['sephiraPassiveText'] = {
      ...?result['sephiraPassiveText'] as Map?, ...?preset!['profile']['sephiraPassiveText'] as Map?,
    };
    CharacterConfig.validate(result);
    return result;
  }

  static Map<String, dynamic> repairDefaultAcquisition(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (unit['native'] != null || unit['party'] != null) return unit;
    final preset = presets.where((p) => p['id'] == presetId(unit)).firstOrNull;
    final update = preset?['acquisitionUpdate'];
    if (update is! Map || update['schema'] != 1) return unit;
    if ((unit['sephiraAcquisition'] as Map?)?['location'] != update['before']) return unit;
    final result = CharacterConfig.copy(unit);
    var changed = false;
    for (final field in ['studioAcquisition','sephiraAcquisition']) {
      final value = result[field];
      if (value is Map && value['version'] == 3 && value['location'] == update['before']) {
        value['location'] = update['after']; changed = true;
      }
    }
    return changed ? result : unit;
  }

  /// Independent bundled Fina shares the collection's additive bonus repair.
  /// Already-updated entries and deliberate later edits are left alone.
  static Map<String, dynamic> repairIndependentBonuses(
    Map<String, dynamic> unit, List<Map<String, dynamic>> presets,
  ) {
    if (member(unit) || !CrystalFina.matches(unit) || unit['native'] != null ||
        unit['party'] != null || unit['sephiraRecipe'] != 6) { return unit; }
    final preset = presets.where((p) => p['id'] == 'crystal_fina').firstOrNull;
    if (preset == null) return unit;
    // An edited standalone kit must remain openable even when it is full.
    try { return updateProgression(unit, preset); }
    on StateError { return unit; }
  }

  static Map<String, dynamic> setEnabled(Map<String, dynamic> unit, bool enabled) => {
    ...unit,
    field: {...unit[field] as Map, 'enabled': enabled},
  };

  static Map<String, dynamic> instantiate(
    Map<String, dynamic> preset,
    List<dynamic> roster, {
    required bool enabled,
    Map<String, dynamic>? replacing,
  }) {
    final profile = preset['profile'];
    if (profile is! Map<String, dynamic>) {
      throw StateError('The version and kit for ${preset['name']} are not finalized yet.');
    }
    final result = CharacterConfig.restoreAll([fixedProfile(preset)], roster, [replacing], requireSavedIds: true).single;
    result[field] = {'version': 1, 'preset': preset['id'], 'enabled': enabled};
    return result;
  }

  /// Apply the requested progression/acquisition revision without resetting
  /// artwork, combat edits, identities or user-added learned abilities.
  static Map<String, dynamic> updateProgression(
    Map<String, dynamic> unit, Map<String, dynamic> preset,
  ) {
    final latest = preset['profile']['sephiraRecipe'] as int;
    if (latest>=7 && preset['mrRestoration'] is Map && (unit['sephiraRecipe'] as int? ?? 0)<7) {
      final legacy=CharacterConfig.copy(preset);
      (legacy['profile'] as Map).addAll(CharacterConfig.copy(preset['mrRestoration']['before'] as Map<String,dynamic>));
      legacy['awakeningBalance']=CharacterConfig.copy(preset['mrRestoration']['beforeAwakeningBalance'] as Map<String,dynamic>);
      (legacy['profile'] as Map).remove('sephiraMrRevision');
      legacy.remove('mrRestoration');
      return repairEquipableMr(updateProgression(unit,legacy),[preset],strict:true);
    }
    if ((unit['sephiraRecipe'] as int? ?? 0) >= latest) {
      return repairEquipableMr(repairKit(repairMasteryScope(CharacterConfig.copy(unit), [preset]), [preset], strict: true),[preset],strict:true);
    }
    if (latest >= 7) {
      var previous = unit;
      if ((unit['sephiraRecipe'] as int? ?? 0) < 6) {
        // Revision 6 owns the MR curation; applying only revision 7 must never
        // reset an already-curated (and possibly edited) mastery schedule.
        final legacy = CharacterConfig.copy(preset);
        legacy['profile']['sephiraRecipe'] = 6;
        previous = updateProgression(unit, legacy);
      }
      final result = CharacterConfig.copy(previous);
      final learned = {for (final field in ['awakening','synchro'])
        for (final tier in result[field] as List) for (final grant in tier as List)
          '${grant[0]}:${grant[1]}'};
      final additions = preset['awakeningBalance']['grants'] as List;
      for (final bonus in additions) {
        final identity = bonus['id'] as int;
        if (!learned.add('PassiveSkill:$identity')) continue;
        final start = bonus['rank'] as int;
        final awakening = result['awakening'] as List;
        final rank = [for (var r = start; r < 4; r++) r]
            .where((r) => (awakening[r] as List).length < 8).firstOrNull;
        if (rank == null) {
          throw StateError('${unit['en']} has no room for its awakening bonuses. Free an awakening slot before applying the update.');
        }
        (awakening[rank] as List).add(['PassiveSkill', identity, -1]);
      }
      result['sephiraRecipe'] = 7;
      CharacterConfig.validate(result);
      return repairEquipableMr(repairKit(repairMasteryScope(result, [preset]), [preset], strict: true),[preset],strict:true);
    }
    if (latest >= 6) {
      var previous = unit;
      if ((unit['sephiraRecipe'] as int? ?? 0) < 5) {
        // Apply earlier source/acquisition migrations against their own layout,
        // before curating passives. A new allocation is not an old MR template.
        final legacy = CharacterConfig.copy(preset);
        (legacy['profile'] as Map).addAll(
            CharacterConfig.copy(preset['revision5Progression'] as Map<String, dynamic>));
        legacy['profile']['sephiraRecipe'] = 5;
        previous = updateProgression(unit, legacy);
      }
      return _passiveMastery(previous, preset);
    }
    final template = CharacterConfig.restore(
        preset['profile'] as Map<String, dynamic>, [], replacing: unit);
    final result = CharacterConfig.copy(unit);
    _replaceProtectedRewards(result, template, preset);
    // Revision 5 corrects sources in place. Preserve the already-applied MR
    // schedule, custom acquisition, stats, artwork and unrelated combat edits.
    if ((unit['sephiraRecipe'] as int? ?? 0) >= 4) {
      result['sephiraRecipe'] = latest;
      CharacterConfig.validate(result);
      return result;
    }
    final available = <String, List<dynamic>>{};
    String key(List g) => '${g[0]}:${g[1]}';
    for (final field in ['awakening', 'synchro']) {
      for (final tier in result[field] as List) {
        for (final raw in tier as List) {
          final g = List<dynamic>.from(raw as List);
          if (g[0] != 'ActiveSkill' && g[0] != 'PassiveSkill') continue;
          if (available.containsKey(key(g))) {
            throw StateError('${unit['en']} has duplicate learned abilities. Edit those before applying the MR update.');
          }
          available[key(g)] = g;
        }
      }
    }
    final chosen = <List<dynamic>?>[];
    for (final rank in [1, 3, 5, 7, 9]) {
      final preferred = (template['synchro'][rank] as List).first as List;
      final match = available[key(preferred)];
      chosen.add(match);
    }
    // Honor removed/replaced abilities: fill a missing selection from the
    // saved kit instead of silently restoring a deleted combat ability.
    for (var i = 0; i < chosen.length; i++) {
      if (chosen[i] != null) continue;
      chosen[i] = available.values.where((g) =>
          !chosen.any((v) => v != null && key(v) == key(g))).firstOrNull;
    }
    if (chosen.any((v) => v == null)) throw StateError('${unit['en']} needs five learned abilities for its MR rewards.');
    final picked = chosen.map((g) => key(g!)).toSet();
    final awakening = [
      for (final tier in result['awakening'] as List)
        [for (final g in tier as List) if (!picked.contains(key(g as List))) List<dynamic>.from(g)],
    ];
    final retained = awakening.expand((t) => t).map(key).toSet();
    void awaken(List<dynamic> g, {bool early = false}) {
      final order = early ? [0, 1, 2, 3] : [3, 2, 1, 0];
      final rank = order.where((r) => awakening[r].length < 8).firstOrNull;
      if (rank == null) throw StateError('${unit['en']} has no room for its retained awakening abilities.');
      awakening[rank].add(g); retained.add(key(g));
    }
    for (final g in available.values) {
      if (!picked.contains(key(g)) && !retained.contains(key(g))) awaken(g);
    }
    // Only the eight newly authored low-tier alternatives are eligible filler.
    // Never fill a short edited kit by restoring arbitrary deleted abilities.
    final sourceBase = CharacterConfig.skillBase(preset['profile']['id'] as int);
    final targetBase = CharacterConfig.skillBase(unit['id'] as int);
    for (final identity in preset['masteryFillers'] as List? ?? []) {
      if (awakening.expand((t) => t).length >= 20) break;
      final mapped = targetBase + (identity as int) - sourceBase;
      final recipe = CharacterConfig.copy(template['skills'][mapped.toString()] as Map<String, dynamic>);
      final owned = result['skills'] as Map;
      var free = mapped;
      if (owned.containsKey(free.toString())) {
        free = List.generate(100, (i) => targetBase + i)
            .firstWhere((i) => !owned.containsKey(i.toString()));
        recipe['jp'] = '${recipe['jp']}_MR4_$free';
      }
      owned[free.toString()] = recipe;
      awaken(['ActiveSkill', free, -1], early: true);
    }
    final mastery = template['synchro'] as List;
    for (var i = 0; i < chosen.length; i++) {
      mastery[[1, 3, 5, 7, 9][i]][0] = chosen[i];
    }
    result['awakening'] = awakening;
    result['synchro'] = mastery;
    result['sephiraRecipe'] = template['sephiraRecipe'];
    if (template['sephiraAcquisition'] is Map) {
      result['sephiraAcquisition'] = template['sephiraAcquisition'];
      result[Acquisition.field] = template['sephiraAcquisition'];
    }
    CharacterConfig.validate(result);
    return result;
  }

  static Map<String, dynamic> _passiveMastery(
      Map<String, dynamic> unit, Map<String, dynamic> preset) {
    final template = CharacterConfig.restore(
        preset['profile'] as Map<String, dynamic>, [], replacing: unit);
    final result = CharacterConfig.copy(unit);
    final awakening = [for (final tier in result['awakening'] as List)
      [for (final raw in tier as List) if (raw[0] != 'PassiveSkill') List<dynamic>.from(raw as List)]];
    final retained = {for (final tier in awakening) for (final g in tier) '${g[0]}:${g[1]}'};
    for (final tier in result['synchro'] as List) {
      for (final raw in tier as List) {
        final grant = List<dynamic>.from(raw as List);
        if (grant[0] != 'ActiveSkill' || !retained.add('${grant[0]}:${grant[1]}')) continue;
        final preferred = (template['awakening'] as List).indexWhere((t) =>
            (t as List).any((g) => g[0] == grant[0] && g[1] == grant[1]));
        final start = preferred < 0 ? 0 : preferred;
        final rank = [start, for (var r = start + 1; r < 4; r++) r,
          for (var r = 0; r < start; r++) r].where((r) => awakening[r].length < 8).firstOrNull;
        if (rank == null) throw StateError('${unit['en']} has no room for its retained active MR skills.');
        awakening[rank].add(grant);
      }
    }
    final rewards = [for (final tier in result['synchro'] as List)
      [for (final raw in tier as List)
        if (raw[0] != 'PassiveSkill' && raw[0] != 'ActiveSkill') List<dynamic>.from(raw as List)]];
    for (final rank in [1, 3, 5, 7, 9]) {
      rewards[rank].insert(0, List<dynamic>.from((template['synchro'][rank] as List)
          .singleWhere((g) => g[0] == 'PassiveSkill') as List));
    }
    // Retain command recipes and deliberate icon choices. Old inherited attack
    // icons get the element of the saved skill, rather than the donor weapon.
    for (final recipe in (result['skills'] as Map).values.cast<Map>()) {
      final fields = recipe['set'] as Map?;
      if (fields == null || fields.containsKey('SkillIcon.TagName') || fields.containsKey('SkillIcon')) continue;
      final source = (template['skills'] as Map).values.cast<Map>()
          .where((r) => r['from'] == recipe['from']).firstOrNull;
      final tag = source?['set']?['SkillIcon.TagName'];
      final element = fields['element'];
      if (tag is String) { fields['SkillIcon.TagName'] =
          ['Fire', 'Ice', 'Thunder', 'Water', 'Wind', 'Earth', 'Light', 'Dark'].contains(element)
              ? 'UI.Skill.Action.Icon.$element' : tag; }
    }
    result['awakening'] = awakening;
    result['synchro'] = rewards;
    result['sephiraPassiveText'] = CharacterConfig.copy(template['sephiraPassiveText'] as Map<String, dynamic>);
    result['sephiraRecipe'] = 6;
    CharacterConfig.validate(result);
    return result;
  }

  static void _replaceProtectedRewards(Map<String, dynamic> unit,
      Map<String, dynamic> template, Map<String, dynamic> preset) {
    final replacements = preset['rewardReplacements'] as List? ?? [];
    final sourceBase = CharacterConfig.skillBase(preset['profile']['id'] as int);
    final targetBase = CharacterConfig.skillBase(unit['id'] as int);
    final owned = unit['skills'] as Map;
    final inserted = <String, List<dynamic>>{};
    for (final field in ['awakening', 'synchro']) {
      for (final tier in unit[field] as List) {
        for (var i = 0; i < (tier as List).length; i++) {
          final grant = tier[i] as List;
          final recipe = grant[0] == 'ActiveSkill' ? owned[grant[1].toString()] as Map? : null;
          final source = recipe?['from'] ?? grant[1];
          final spec = replacements.where((r) => r['oldKind'] == grant[0] && r['oldSource'] == source).firstOrNull;
          if (spec == null) continue;
          final replacement = List<dynamic>.from(spec['newGrant'] as List);
          if (replacement[0] == 'ActiveSkill') {
            final identity = targetBase + (replacement[1] as int) - sourceBase;
            final key = '${replacement[0]}:${spec['source']}';
            if (inserted.containsKey(key)) {
              tier[i] = List<dynamic>.from(inserted[key]!);
              continue;
            }
            final value = CharacterConfig.copy(template['skills'][identity.toString()] as Map<String, dynamic>);
            final same = owned.entries.where((e) => (e.value as Map)['from'] == spec['source']).firstOrNull;
            int target;
            if (same != null) {
              target = int.parse(same.key.toString());
            } else {
              final occupied = {for (final k in owned.keys) for (final offset in [0, 1, 2]) int.parse(k.toString()) + offset};
              target = [identity, for (var n = 1; n < 32; n++) targetBase + n * 3]
                  .firstWhere((id) => [id, id + 1, id + 2].every((v) => !occupied.contains(v)));
              value['jp'] = '${value['jp']}_MR5_$target';
              owned[target.toString()] = value;
            }
            replacement[1] = target;
            inserted[key] = replacement;
          }
          tier[i] = replacement;
        }
      }
    }
    final learned = {for (final field in ['awakening', 'synchro'])
      for (final tier in unit[field] as List) for (final g in tier as List)
        if (g[0] == 'ActiveSkill') g[1]};
    owned.removeWhere((id, recipe) => !learned.contains(int.parse(id.toString())) &&
        replacements.any((r) => r['oldKind'] == 'ActiveSkill' && r['oldSource'] == (recipe as Map)['from']));
    unit['sephiraPassiveText'] = {
      ...?unit['sephiraPassiveText'] as Map?, ...?template['sephiraPassiveText'] as Map?,
    };
  }
}
