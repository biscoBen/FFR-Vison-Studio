# Crystal Fina boss fixtures

`rows.json.gz` contains the exact native donor rows used by the private boss, extracted from the supplied
demo skill-routing reference (2026-10-16). It includes early boss/unit and AI/asset/design rows, and the
original skill/presentation/hit-effect rows for Crystal Fina's preset. `ai.json.gz` is the original Belmodar
AI UAsset JSON from the same reference. No generated boss data is used as its native source fixture.

Python tests apply the recipe without modifying the donors and interpret the actual authored Kismet with
its byte offsets. The Windows cached-engine contract checks those offsets with UAssetAPI's real GetSize.
These fixtures are for regression checks, not packaged game content or a gameplay pass.
