import 'package:flutter/material.dart';

import '../design/widgets.dart';

/// Original vision IDs matched to their classic FFBE counterparts. The bundled
/// PNGs come from the checksum-verified Studio icon pack; no row downloads occur.
const nativePortraitForms = <int, String>{
  13017: '100007006', // Amelia
  13024: '100001102', // Tronn
  13027: '100006906', // Victoria
  13033: '100006606', // Camille
  13045: '100001002', // Leah
  13051: '100008607', // Ayaka
  13060: '100004306', // Charlotte
  13062: '100006107', // Wilhelm
  13080: '100005917', // Aileen
  13100: '201000106', // Warrior of Light
  13101: '202000106', // Firion
  13102: '203000107', // Onion Knight
  13103: '204000106', // Cecil
  13105: '205000106', // Bartz
  13108: '206000106', // Terra
  13110: '207000117', // Cloud
  13113: '207001007', // Sephiroth
  13116: '208000107', // Squall
  13118: '209000106', // Zidane
  13120: '210000107', // Tidus
  13123: '211000105', // Shantotto
  13124: '212000106', // Vaan
  13125: '213000117', // Lightning
  13127: '214000106', // Y’shtola
  13128: '215000107', // Noctis
  13130: '216000127', // Clive
};

class NativePortrait extends StatelessWidget {
  const NativePortrait({
    super.key,
    required this.visionId,
    required this.fallbackUrl,
    required this.width,
    required this.height,
  });
  final int visionId;
  final String fallbackUrl;
  final double width;
  final double height;

  @override
  Widget build(BuildContext context) {
    final form = nativePortraitForms[visionId];
    Widget fallback() => PixelImage(fallbackUrl, width: width, height: height);
    if (form == null) return fallback();
    return Image.asset(
      'assets/native_portraits/$form.png',
      width: width,
      height: height,
      fit: BoxFit.contain,
      filterQuality: FilterQuality.none,
      errorBuilder: (_, _, _) => fallback(),
    );
  }
}
