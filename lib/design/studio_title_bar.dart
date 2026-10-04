import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';

import '../version.dart';

/// An explicit icon/background pair avoids native white-on-white captions.
/// window_manager preserves dragging, maximize/restore and the close listener.
class StudioWindowFrame extends StatelessWidget {
  const StudioWindowFrame({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    return Column(children: [
      SizedBox(
        height: kWindowCaptionHeight,
        child: WindowCaption(
          brightness: brightness,
          backgroundColor: brightness == Brightness.dark
              ? const Color(0xff1c1c1c) : const Color(0xfff3f3f3),
          title: Text(isTestBuild ? 'Sephira Studio Test' : 'FFR Vision Studio'),
        ),
      ),
      Expanded(child: child),
    ]);
  }
}
