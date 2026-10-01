import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';
import 'add_unit_dialog.dart';
import 'remove_unit_dialog.dart';

Future<void> chooseNativeVision(
  BuildContext context,
  Map<String, dynamic> vision,
) async {
  final app = context.read<AppState>();
  final edited = app.units.any((u) => u['key'] == vision['key']);
  final choice = await showDialog<String>(
    context: context,
    builder: (c) => AlertDialog(
      backgroundColor: Guide.paper,
      shape: Border.fromBorderSide(Guide.frame),
      title: Text(vision['en'].toString(), style: Guide.h2()),
      content: Text(
        'Change this game vision\'s model, edit its current configuration, or revert all its edits to the original. Changing the model keeps its current configuration.',
        style: Guide.text(),
      ),
      actions: [
        GuideButton('Cancel', onPressed: () => Navigator.pop(c)),
        GuideButton('Edit vision', onPressed: () => Navigator.pop(c, 'edit')),
        GuideButton('Change model', onPressed: () => Navigator.pop(c, 'model')),
        GuideButton(
          'Revert to original',
          danger: true,
          onPressed: app.building || !edited
              ? null
              : () => Navigator.pop(c, 'revert'),
        ),
      ],
    ),
  );
  if (!context.mounted || choice == null) {
    return;
  }
  if (choice == 'model') {
    await showChangeModel(context, vision['id'] as int);
    return;
  }
  if (choice == 'revert') {
    await confirmRemove(context, app, vision);
    return;
  }
  try {
    await app.editNativeVision(vision['id'] as int);
  } catch (e) {
    app.showNotice('Could not open this vision: $e');
  }
}

Future<void> showChangeModel(BuildContext context, int id) => showDialog<void>(
  context: context,
  builder: (_) => AddUnitDialog(replaceVisionId: id),
);
