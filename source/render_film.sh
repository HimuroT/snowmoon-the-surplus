#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p review
python3 source/animate_film.py --workers 6
python3 source/synthesize_audio.py
ffmpeg -y -hide_banner -loglevel warning -framerate 24 -i frames/%05d.png -i audio/the_surplus_84s_mix.wav -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -ac 2 -t 84 -movflags +faststart -metadata title='The Surplus | A Snowmoon Short Film' -metadata comment='Unofficial Snowmoon Chapter 5 adaptation. Original vector animation and synthesized sound. GNU GPL version 3. No voiced dialogue.' The_Surplus_84s.mp4
ffmpeg -y -hide_banner -loglevel error -ss 71.500 -i The_Surplus_84s.mp4 -frames:v 1 -update 1 The_Surplus_84s_still.png
ffprobe -v error -show_streams -show_format -of json The_Surplus_84s.mp4 > review/probe.json
ffmpeg -hide_banner -loglevel error -i The_Surplus_84s.mp4 -f null -
ffmpeg -y -hide_banner -loglevel error -i The_Surplus_84s.mp4 -map 0:v:0 -f framemd5 review/frame_hashes.txt
ffmpeg -y -hide_banner -loglevel error -i The_Surplus_84s.mp4 -map 0:a:0 -c:a pcm_f32le review/decoded_mix_for_qa.wav
python3 source/verify_and_package.py
