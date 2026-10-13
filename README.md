# The Surplus

An 84-second unofficial animated adaptation of [Snowmoon, Chapter 5](https://vitalik.eth.limo/snowmoon/html/chapter-5.html) by Vitalik Buterin. Original vector animation and procedural sound, made with OpenAI assistance.

[Watch the film and download the production materials](https://himurot.github.io/snowmoon-the-surplus/)

## Source and license

Film and task-specific production materials: GNU GPL version 3. See [LICENSE](LICENSE), [credits](CREDITS.txt), and the original author’s [license notice](https://vitalik.eth.limo/snowmoon/). This is an unofficial adaptation; no endorsement is implied.

- `source/`: editable Python animation/character/audio code, shot list, captions, creative directions, tested dependencies, and build/verification scripts
- `downloads/The_Surplus_84s_source_core.zip`: corresponding source plus all 2,016 editable SVG frames and verification reports
- Three optional audio ZIPs: full-length 24-bit FLAC mix and stems
- `assets/`: final film, representative still, shot contact sheet, and favicon

Read [the production workflow](source/WORKFLOW.txt) and [detailed README](README.txt). To regenerate the film, extract the core source ZIP and follow its workflow. The editable code here is the same code included in the source ZIP. Python, NumPy, SciPy, Pillow, Inkscape, FFmpeg, and DejaVu Sans are required; allow several gigabytes for intermediate frames.

## Website

This is a buildless static site. `index.html` and `style.css` use same-origin relative asset paths compatible with the project URL. No JavaScript, analytics, backend, payment, or authentication service is used. `.nojekyll` disables Jekyll processing.

For local preview: `python3 -m http.server 8000`, then open http://localhost:8000/. GitHub Pages publishes the root of `main`.

## Verification limits

The release is 84 seconds, 1920×1080, 24 fps, with English captions in the image and synthesized stereo sound. Full-file decoding, frame sources, and caption boundaries were checked. Realtime synchronized playback and perceptual listening have not been interactively verified. Integrated loudness is approximately −31 LUFS. No competition eligibility claim is made.

Public MP4 container metadata was updated using stream copy; reviewed audio and video streams were retained. See the downloadable README and QA reports for details.
