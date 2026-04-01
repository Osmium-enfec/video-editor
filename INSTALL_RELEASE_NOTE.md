Release bundle (macOS Intel)

Files to include when sending to end users:

- `VideoEditorIntel.dmg` — disk image containing the signed app bundle.
- If not bundled into the DMG, include an Intel `ffmpeg` binary named `ffmpeg-x86_64` (or `ffmpeg`) in the same archive.
- `third_party/ffmpeg/macos/README.md` — notes and license reminder for ffmpeg.

Build steps (on an Intel mac):

1. Place an Intel ffmpeg binary into `third_party/ffmpeg/macos/` and name it `ffmpeg-x86_64`.
2. Build the app with PyInstaller (uses `VideoEditorIntel.spec`):

```
pyinstaller VideoEditorIntel.spec
```

3. Create the DMG:

```
./scripts/create_dmg.sh dist/VideoEditorIntel.app "VideoEditor" VideoEditorIntel.dmg
```

Installation steps for recipients:

1. Open `VideoEditorIntel.dmg` and drag `VideoEditorIntel.app` to the `Applications` folder.
2. Launch `VideoEditorIntel.app`. On first run the app will check for `ffmpeg`.
   - If `ffmpeg` was bundled into the DMG, the app will use the bundled binary.
   - Otherwise it will offer to download/install `ffmpeg` (user consent required).

License and redistribution:

- FFmpeg is licensed under LGPL/GPL. If you redistribute ffmpeg with this app,
  ensure you comply with FFmpeg's licensing terms and include any required
  notices/source offering as appropriate.
