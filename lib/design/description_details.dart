import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'theme.dart';
import 'widgets.dart';

/// Open complete descriptions on a click; a parent drag cancels the tap.
class DescriptionDetails extends StatelessWidget {
  const DescriptionDetails({
    super.key,
    required this.description,
    required this.child,
    this.title = '',
  });

  final String title;
  final String description;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (description.trim().isEmpty) return child;
    return InkWell(
      onTap: () => showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          backgroundColor: Guide.paper,
          shape: Border.fromBorderSide(Guide.frame),
          title: Text(
            title.isEmpty ? 'Full description' : title,
            style: Guide.h2(),
          ),
          content: SizedBox(
            width: 560,
            child: ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: math.min(
                  420,
                  MediaQuery.sizeOf(dialogContext).height * 0.65,
                ),
              ),
              child: SingleChildScrollView(
                child: SelectableText(description, style: Guide.text()),
              ),
            ),
          ),
          actions: [
            GuideButton('Close', onPressed: () => Navigator.pop(dialogContext)),
          ],
        ),
      ),
      child: child,
    );
  }
}
