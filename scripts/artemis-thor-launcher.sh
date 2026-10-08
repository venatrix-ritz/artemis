#!/bin/bash
# Artemis Game Mode launcher for AYN Thor (Armada OS). Installed as ~/.local/share/artemis/bin/artemis;
# the real binary sits next to it as artemis.bin (see scripts/deploy-thor-steam.py).

HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

export LD_LIBRARY_PATH="${HERE}/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="${HERE}/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Hardware decode on the Thor's Qualcomm Iris decoder (/dev/video0, driver iris_driver).
# Observed 2026-10-07: without these Artemis's automatic decoder search never tries a v4l2m2m decoder and logs
# "Unable to find working decoder" (HEVC 0x100, 0x200, AV1) with the "no functioning hardware accelerated
# video decoder" warning; with the hint, hevc_v4l2m2m opens on Iris Decoder. The Iris decoder rejected
# av1_v4l2m2m and HEVC Main10 in the same test, so only H.264 and HEVC are hinted. If a hinted decoder fails
# to load, Artemis logs an error and falls back to its normal search.
export H264_DECODER_HINT="${H264_DECODER_HINT:-h264_v4l2m2m}"
export HEVC_DECODER_HINT="${HEVC_DECODER_HINT:-hevc_v4l2m2m}"

# In Steam Game Mode, Gamescope manages nested X11 clients (borderless fullscreen)
if [ -z "$DISPLAY" ]; then
    if [ -S "/tmp/.X11-unix/X1" ]; then
        export DISPLAY=:1
    elif [ -S "/tmp/.X11-unix/X0" ]; then
        export DISPLAY=:0
    fi
fi

# Ensure Qt and SDL use Gamescope's managed X11 display instead of raw Wayland CSD
unset QT_QPA_PLATFORM
unset WAYLAND_DISPLAY
unset GAMESCOPE_WAYLAND_DISPLAY
# SDL video driver for Gamescope nested X11
export SDL_VIDEODRIVER=x11

exec "${HERE}/bin/artemis.bin" "$@"
