Packaging instructions and notes for including ffmpeg binaries for Windows.

- Place Windows ffmpeg executables into this folder before building the app.
- Prefer architecture-specific filenames: `ffmpeg-x86_64.exe` and `ffmpeg-arm64.exe`.
- The `scripts/create_windows_package.sh` helper copies any `ffmpeg*.exe`
  files into the final `dist/` folder so the packaged EXE can find them.
- Sources for Windows builds:
  - Gyan.dev: https://www.gyan.dev/ffmpeg/builds/
  - BtbN FFmpeg-Builds: https://github.com/BtbN/FFmpeg-Builds/releases

License: FFmpeg is licensed under LGPL/GPL; ensure compliance when redistributing.

Example commands (replace release URLs as needed):

- Download and extract a Gyan.dev build, then copy the ffmpeg.exe into this folder:

```
mkdir -p third_party/ffmpeg/windows
curl -L -o /tmp/ffmpeg.zip "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
unzip /tmp/ffmpeg.zip -d /tmp/ffmpeg-extract
cp /tmp/ffmpeg-extract/ffmpeg-*-essentials_build/bin/ffmpeg.exe third_party/ffmpeg/windows/ffmpeg-x86_64.exe
```

- Or download a BtbN release and copy `ffmpeg.exe`:

```
mkdir -p third_party/ffmpeg/windows
curl -L -o /tmp/ffmpeg.zip "https://github.com/BtbN/FFmpeg-Builds/releases/download/your-release/ffmpeg-your-asset.zip"
unzip /tmp/ffmpeg.zip -d /tmp/ffmpeg-extract
cp /tmp/ffmpeg-extract/bin/ffmpeg.exe third_party/ffmpeg/windows/ffmpeg-x86_64.exe
```

Notes:
- Use arch-specific filenames where possible (`ffmpeg-x86_64.exe`, `ffmpeg-arm64.exe`).
- Verify with `third_party/ffmpeg/windows/ffmpeg-x86_64.exe -version`.
