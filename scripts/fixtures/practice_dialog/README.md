The supplied demo reference's unchanged event-only Cloud Cut shell, serialized by the pinned build-15 ffr-dt reader. Used to exercise native dialogue authoring against real property/bytecode wrappers. Source package: Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Cut_000. The original shell is never installed; the builder strips its battle bindings and authors private native talk-director calls. JSON SHA256: 70a49e0d47262666da54459ac6e887856de160b0b6b5e82afed6b563f0bdd699.

`talk-events.json` retains the complete supplied demo rows for the Mitra shop woman
(`DT_Town_010Gra_20_0920_8`), inn choice template (`0920_5`) and continuous-event
template (`0930_1`). The latter includes real quest flags/progress/request state
so tests prove those fields are cleared when it supplies the populated struct array.
The shop woman's original continuous-event list is empty, matching the reported failure.

`talk-properties.json.gz` retains those same three rows in the original table's
native UAssetAPI property wrappers, with the other forty rows omitted. Windows CI
uses the pinned engine's actual `Patch.ApplyObject` on all nineteen dialogue edits.
Its negative control must reproduce the empty-struct-array error before testing
the corrected populated donor and native map arguments. Uncompressed JSON SHA256:
`45ef324a676aeb0dd62c02a3777a1372d5b88e5c87e6da13f19d251221ae22ac`.
