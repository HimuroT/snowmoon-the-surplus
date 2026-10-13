THE SURPLUS — INDEPENDENT SOURCE AND AUDIO ARCHIVES
Public source edition, 13 October 2026.

Each ZIP is a normal standalone archive. These are not multipart archives.
The audio files are complete 84-second tracks, not time segments. No joining
or reconstruction of archive parts is required.

1. The_Surplus_84s_source_core.zip
   All source code, 2,016 editable SVG frames, caption/shot data, creative
   directions, dependencies, GPLv3 text, checks and a representative still.
   This archive alone is sufficient to regenerate the float32 master stems
   and the supplied video with the documented local tools.
2. The_Surplus_84s_audio_mix.zip
   Full-length 48 kHz stereo 24-bit FLAC mix.
3. The_Surplus_84s_audio_ambience.zip
   Full-length 48 kHz stereo 24-bit FLAC ambience stem.
4. The_Surplus_84s_audio_effects_music.zip
   Full-length 48 kHz stereo 24-bit FLAC effects and music stems.

To collect everything, extract the desired archives into the same parent
folder. All use the common root The_Surplus_84s/. Shared delivery notes, credits and license files
are identical. Each archive also remains useful on its own.

The_Surplus_84s/
  README.txt
  DELIVERY_README.txt
  CREDITS.txt
  source/
  svg/
  review/
  audio_delivery/  (optional full-length FLACs and conversion checks)

The FLACs losslessly encode a 24-bit integer conversion of the original
float32 masters. They are not bit-identical to the float32 WAVs. Measured
maximum absolute sample error is about 1.19e-7, approximately -138.49 dBFS.
Exact float32 audio is reproducible with:
  python3 source/synthesize_audio.py

The supplied source uses fixed seeds and documented dependency versions.
The complete rebuild command is in the source-core README.txt.
