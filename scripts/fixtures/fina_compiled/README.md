# Cooked movie timing fixture

The 3,073-byte CompiledData export from the full-game Cloud movie master
`Sequencer/Battle/Skill/440110/440111/SEQ_Battle_440111_Master`, captured in the
returned full-game reference. Its SHA-256 is
`8bb3c2d3538db74709bebad68b4d5f1ab6132934dada1e32b66baa7f70250a3b`.
The source uasset/uexp hashes are pinned in `_ffr_fina_cinematic.py`.

The shipping cached Mana template/evaluation tree retains movie endpoints at
363200 ticks (offsets 110, 962, 2719, 2724) and root/subsequence endpoints at
480000 ticks (offsets 264, 430, 440, 580, 590, 730, 740, 936, 3030).
Tests shorten these with their typed ranges, preserving all other native bytes,
including binding identifiers and actor/director locators. Unknown revisions
are rejected. This small fixture is test-only and is not installed in Studio.
