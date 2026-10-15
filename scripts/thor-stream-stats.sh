#!/bin/bash
# Summarises Artemis Game Mode session logs (~/.local/share/armada/logs/steam-launch-*.log on the Thor)
# for A/B measurement. Prints one key=value per line per log: renderer, decoder hint use, Gamescope WSI
# messages, IDR waits, network drops, and the final "Global video stats" values.
# Usage: thor-stream-stats.sh <steam-launch.log> [<more logs>...]
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 <steam-launch.log> [...]" >&2
    exit 2
fi

count() { grep -a -c -F -- "$1" "$2" || true; }
# Last value of a stats line; the stats block is printed once per session, at quit.
last() { grep -a -F -- "$1" "$2" | tail -1 | sed 's/^[^:]*: //' || true; }

status=0
for log in "$@"; do
    if [ ! -r "$log" ]; then
        echo "$log: not readable" >&2
        status=1
        continue
    fi
    echo "== $log"
    echo "renderer=$(grep -a -o "Renderer '[^']*' chosen" "$log" | tail -1 | sed "s/Renderer '//; s/' chosen//" || true)"
    echo "video_stream=$(grep -a -o "Video stream is [^(]*" "$log" | tail -1 | sed 's/Video stream is //; s/ *$//' || true)"
    echo "decoder_hint_failed=$(count 'DECODER_HINT) failed to load' "$log")"
    echo "decoder_hint_used=$(count 'Using custom' "$log")"
    echo "gamescope_wsi_lines=$(count 'Gamescope WSI' "$log")"
    echo "wsi_forced_maintenance=$(count 'Forcing on VK_EXT_swapchain_maintenance1' "$log")"
    echo "idr_waits=$(count 'Waiting for IDR frame' "$log")"
    echo "network_dropped_events=$(count 'Network dropped' "$log")"
    echo "unrecoverable_frames=$(count 'Unrecoverable frame' "$log")"
    echo "quit_events=$(count 'Quit event received' "$log")"
    echo "incoming_fps=$(last 'Incoming frame rate from network' "$log")"
    echo "decoding_fps=$(last 'Decoding frame rate' "$log")"
    echo "rendering_fps=$(last 'Rendering frame rate' "$log")"
    echo "host_processing_latency_ms=$(last 'Host processing latency' "$log")"
    echo "dropped_by_network=$(last 'Frames dropped by your network connection' "$log")"
    echo "dropped_by_jitter=$(last 'Frames dropped due to network jitter' "$log")"
    echo "network_latency=$(last 'Average network latency' "$log")"
    echo "decoding_time=$(last 'Average decoding time' "$log")"
    echo "frame_queue_delay=$(last 'Average frame queue delay' "$log")"
    echo "rendering_time=$(last 'Average rendering time' "$log")"
done
exit "$status"
