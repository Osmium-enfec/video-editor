Packaging instructions and notes for including ffmpeg binaries.

- Place macOS ffmpeg binaries into this folder before building the app.
- For Apple Silicon (arm64) and Intel (x86_64) builds provide separate
  binaries named `ffmpeg-arm64` and `ffmpeg-x86_64` or simply `ffmpeg`.
- When building with PyInstaller these files will be bundled into
  `_MEIPASS/ffmpeg/` and the runtime will prefer them over system `ffmpeg`.
- Sources:
  - evermeet.cx provides single-file macOS builds: https://evermeet.cx/ffmpeg/
  - BtbN builds: https://github.com/BtbN/FFmpeg-Builds/releases

License: FFmpeg is licensed under LGPL/GPL; ensure compliance when redistributing.

Example commands (replace names/URLs as needed):

- Download single-file build (evermeet) and place into this folder:

```
mkdir -p third_party/ffmpeg/macos
curl -L https://evermeet.cx/ffmpeg/ffmpeg -o third_party/ffmpeg/macos/ffmpeg-arm64
chmod +x third_party/ffmpeg/macos/ffmpeg-arm64
```

- Download a BtbN release, extract ffmpeg and rename per-arch:

```
mkdir -p third_party/ffmpeg/macos
# download the appropriate archive for your arch (example: macos-arm64)
curl -L -o /tmp/ffmpeg.zip "https://github.com/BtbN/FFmpeg-Builds/releases/download/your-release/ffmpeg-your-asset.zip"
unzip /tmp/ffmpeg.zip -d /tmp/ffmpeg-extract
cp /tmp/ffmpeg-extract/bin/ffmpeg third_party/ffmpeg/macos/ffmpeg-arm64
chmod +x third_party/ffmpeg/macos/ffmpeg-arm64
```

Notes:
- Name the binaries with an arch suffix (e.g., `ffmpeg-arm64`, `ffmpeg-x86_64`) so the runtime can pick the correct one. A generic `ffmpeg` will also be accepted.
- Verify the binary works with `third_party/ffmpeg/macos/ffmpeg-arm64 -version`.
