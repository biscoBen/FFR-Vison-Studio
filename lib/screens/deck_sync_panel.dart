import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../services/api.dart';
import '../state/app_state.dart';

class DeckSyncPanel extends StatefulWidget {
  const DeckSyncPanel({super.key, required this.canBuild});
  final bool canBuild;
  @override
  State<DeckSyncPanel> createState() => _DeckSyncPanelState();
}

class _DeckSyncPanelState extends State<DeckSyncPanel> {
  Api? _loaded;
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final app = context.read<AppState>();
    if (app.api != null && _loaded != app.api) {
      _loaded = app.api;
      // Personal details are read only from this installation's engine.
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (mounted) { try { await app.refreshDeckSync(); } catch (_) {} }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final sync = app.deckSync;
    final busy = app.building || app.deckWorking || app.sephiraWorking || app.api == null;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Band('Steam Deck snapshots', color: Guide.ink),
      Box(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Build on this PC, export a snapshot, then copy it to the Deck and run Install snapshot.sh. No GitHub setup or building on the Deck is needed.', style: Guide.text()),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          GuideButton('Build for Deck snapshot', key: const Key('deck-snapshot-build'),
              onPressed: busy || !widget.canBuild ? null : () => app.startBuild(install: false)),
          GuideButton('Export / import snapshots', key: const Key('deck-snapshots'),
              onPressed: busy ? null : () async {
                await app.save();
                if (app.dirty) return;
                await launchUrl(Uri.parse('${app.api!.base}/launch-preparation'));
              }),
        ]),
      ])),
      const SizedBox(height: 8),
      ExpansionTile(key: const Key('deck-private-advanced'),
        title: Text('Optional GitHub publishing', style: Guide.small()), children: [

      Box(child: Material(color: Colors.transparent, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SwitchListTile(
          key: const Key('deck-sync-enabled'), contentPadding: EdgeInsets.zero,
          title: Text('Enable personal publishing', style: Guide.text()),
          subtitle: Text('Off by default. Normal builds and installs never upload. Your destination and token stay on this PC.', style: Guide.small()),
          value: sync['enabled'] == true,
          onChanged: busy ? null : (value) async {
            if (value && (sync['repository'] == '' || sync['hasToken'] != true)) {
              await showDeckSyncSetup(context, app);
            } else {
              try { await app.configureDeckSync(enabled: value, repository: sync['repository']?.toString() ?? ''); }
              catch (e) { app.showNotice('$e'); }
            }
          },
        ),
        if ((sync['repository'] ?? '').toString().isNotEmpty)
          Text('Private destination: ${sync['repository']}', style: Guide.small()),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          GuideButton('Set up private sync', key: const Key('deck-sync-setup'),
              onPressed: busy ? null : () => showDeckSyncSetup(context, app)),
          GuideButton(app.deckWorking ? 'Publishing...' : 'Build & publish to Deck', key: const Key('deck-sync-publish'),
              onPressed: busy || !widget.canBuild || sync['enabled'] != true || sync['hasToken'] != true
                  ? null : () => app.startBuild(install: false, publishToDeck: true)),
        ]),
        const SizedBox(height: 8),
        Text('On the Deck, download Resonance-Deck-Sync.zip and run Update my mod.sh in Desktop Mode. It installs your finished mod and creates a shortcut; Studio and building are not needed.', style: Guide.small()),
        if (sync['message'] != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text('${sync['message']}', style: Guide.text())),
      ]))),
      ]),
    ]);
  }
}

Future<void> showDeckSyncSetup(BuildContext context, AppState app) => showDialog<void>(
  context: context, builder: (_) => _DeckSyncSetup(app: app),
);

class _DeckSyncSetup extends StatefulWidget {
  const _DeckSyncSetup({required this.app});
  final AppState app;
  @override
  State<_DeckSyncSetup> createState() => _DeckSyncSetupState();
}

class _DeckSyncSetupState extends State<_DeckSyncSetup> {
  late final repo = TextEditingController(text: widget.app.deckSync['repository']?.toString() ?? '');
  final token = TextEditingController();
  bool saving = false;
  String? error;

  @override
  void dispose() { repo.dispose(); token.clear(); token.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Set up private Steam Deck sync'),
    content: SizedBox(width: 580, child: SingleChildScrollView(child: Column(
      mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('1. Create a separate PRIVATE repository in your own GitHub account, such as Sephira-Deck-Mods. Initialize it with a README. The public program fork is never a valid destination.'),
        TextButton(onPressed: saving ? null : () => launchUrl(Uri.parse('https://github.com/new?name=Sephira-Deck-Mods&visibility=private')), child: const Text('Create my private repository')),
        const Text('2. Create a fine-grained personal access token for only that repository, with Contents: read and write. On the Deck use a separate token with Contents: read.'),
        TextButton(onPressed: saving ? null : () => launchUrl(Uri.parse('https://github.com/settings/personal-access-tokens/new')), child: const Text('Open GitHub token settings')),
        TextField(key: const Key('deck-sync-repository'), controller: repo, enabled: !saving, autocorrect: false,
            decoration: const InputDecoration(labelText: 'Private repository (owner/name)')),
        TextField(key: const Key('deck-sync-token'), controller: token, enabled: !saving, obscureText: true,
            autocorrect: false, enableSuggestions: false,
            decoration: InputDecoration(labelText: widget.app.deckSync['hasToken'] == true ? 'New token (leave blank to keep saved token)' : 'PC publishing token')),
        const SizedBox(height: 12),
        const Text('The token is saved in Windows Credential Manager, separate from Studio settings. Uploads contain the compiled mod and cycling runtime when enabled; they exclude your game, saves, raw Studio configuration and credentials.'),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ],
    ))),
    actions: [
      if (widget.app.deckSync['hasToken'] == true) TextButton(onPressed: saving ? null : () async {
        setState(() { saving = true; error = null; });
        try { await widget.app.forgetDeckToken(); if (context.mounted) { Navigator.pop(context); } }
        catch (e) { if (mounted) { setState(() { saving = false; error = '$e'; }); } }
      }, child: const Text('Forget token & disable')),
      TextButton(onPressed: saving ? null : () => Navigator.pop(context), child: const Text('Cancel')),
      FilledButton(key: const Key('deck-sync-save'), onPressed: saving ? null : () async {
        setState(() { saving = true; error = null; });
        try {
          await widget.app.configureDeckSync(enabled: true, repository: repo.text, token: token.text.trim());
          token.clear();
          if (context.mounted) { Navigator.pop(context); }
        } catch (e) { token.clear(); if (mounted) { setState(() { saving = false; error = '$e'; }); } }
      }, child: Text(saving ? 'Checking private repository...' : 'Verify & enable')),
    ],
  );
}
