import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'theme.dart';

/// Keep compact rows readable while exposing their complete text on hover.
class DescriptionTooltip extends StatelessWidget {
  const DescriptionTooltip({
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
    final fullText = [if (title.isNotEmpty) title, description].join('\n\n');
    final viewport = MediaQuery.sizeOf(context);
    final width = math.min(560.0, viewport.width - 32);
    return Semantics(
      tooltip: fullText,
      child: Tooltip(
        richMessage: TextSpan(
          children: [
            WidgetSpan(
              child: SizedBox(
                width: width - 24,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: math.min(420, viewport.height * 0.65),
                  ),
                  child: SingleChildScrollView(
                    child: Text(fullText, style: Guide.text(Guide.paper)),
                  ),
                ),
              ),
            ),
          ],
        ),
        excludeFromSemantics: true,
        ignorePointer: false,
        enableTapToDismiss: false,
        // A tall popup may not fit beside a row near the window's centre.
        // Above placement clamps it to the top instead of spilling below.
        preferBelow: false,
        waitDuration: const Duration(milliseconds: 350),
        showDuration: const Duration(seconds: 30),
        constraints: BoxConstraints(maxWidth: width),
        padding: const EdgeInsets.all(12),
        textStyle: Guide.text(Guide.paper),
        decoration: BoxDecoration(color: Guide.ink),
        child: child,
      ),
    );
  }
}
