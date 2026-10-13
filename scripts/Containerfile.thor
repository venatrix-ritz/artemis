# Containerfile for building Artemis natively for AYN Thor (Snapdragon 8 Gen 2 / ARM64 Fedora 44)
FROM fedora:44
RUN dnf5 install -y --setopt=install_weak_deps=False \
    gcc-c++ make git pkgconf-pkg-config \
    qt6-qtbase-devel qt6-qtdeclarative-devel qt6-qtsvg-devel qt6-qtmultimedia-devel \
    SDL2-devel SDL2_ttf-devel opus-devel openssl-devel libdrm-devel ffmpeg-free-devel \
    wayland-devel wayland-protocols-devel \
    libplacebo-devel vulkan-loader-devel vulkan-headers mesa-libEGL-devel && \
    dnf5 clean all
WORKDIR /src
