This fixture contains one constant-white, independently decodable native Sofdec
opacity picture and its `VIDEO_HDRINFO` table. It contains no character image,
voice or music. `provenance.json` records the returned Cloud movie prefix and
checksums. The decoded picture is 1920×1080, with Y minimum/maximum both 255.

`cri_usm_movie.with_opaque_alpha()` repeats this I-frame at each color picture's
presentation time. It preserves the native codec/DC precision/alpha type,
rebuilds both channels' seek offsets and packet lengths, and leaves VP9 packets
unchanged. The selected MP4 is encoded at its original 1920×1080 resolution to
match this opacity picture and the game's battle texture.

This is a scoped compatibility test for Fina's private movie. It does not patch
the game's shared player, material, texture, or original resonance movies.
Local decoding and asset readback do not establish visible in-game playback.
