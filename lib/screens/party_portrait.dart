import 'package:flutter/material.dart';

/// Classic FFBE forms matched to the original party, independent of replacement
/// battle models. These small portraits work without downloading sprite packs.
const partyPortraitForms = <int, String>{
  1001: '100000107', // Rain
  1002: '100000207', // Lasswell
  1003: '100000307', // Fina
  1004: '100000507', // Lid
  1005: '100000407', // Nichol
  1006: '100000317', // Dark Fina
  1007: '100000707', // Jake
  1008: '100000607', // Sakura
};

class PartyPortrait extends StatelessWidget {
  const PartyPortrait({
    super.key,
    required this.characterId,
    required this.width,
    required this.height,
  });
  final int characterId;
  final double width;
  final double height;

  @override
  Widget build(BuildContext context) => Image.asset(
    'assets/party_portraits/${partyPortraitForms[characterId]}.png',
    width: width,
    height: height,
    fit: BoxFit.contain,
    filterQuality: FilterQuality.none,
  );
}
