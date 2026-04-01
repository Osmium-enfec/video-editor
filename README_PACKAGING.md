# Packaging and distribution (macOS)

This repository includes helper scripts to produce a standalone macOS application using PyInstaller and an optional Cython compilation step to make source extraction harder.

Quick steps (recommended on macOS machine):

1. Create and activate a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. (Optional) Compile selected modules with Cython to produce binary extensions:

```bash
./scripts/build_mac.sh --cython
```

3. Build the standalone app with PyInstaller:

```bash
./scripts/build_mac.sh
```

The produced executable will be in `dist/VideoEditor`.

Notes and caveats:
- PyInstaller bundles bytecode and dependencies into a single executable, but determined users can still extract resources. Cython helps by compiling selected `.py` modules to extension modules, which is a practical deterrent but not a foolproof protection.
- PyInstaller can produce an application bundle in `dist/` (check `dist/VideoEditor` after building). For a cleaner macOS distribution create a signed `.app` and a compressed DMG.

Code signing and notarization (high level):
- Obtain an Apple Developer ID and install the signing certificate in your keychain.
- Sign your `.app` with the `Developer ID Application` identity using:

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: Your Name (TEAMID)" /path/to/YourApp.app
```

- Create a DMG with `hdiutil`:

```bash
hdiutil create -srcfolder /path/to/folder-containing-app -volname "VideoEditor" -format UDZO -ov VideoEditor.dmg
```

- Notarize with `xcrun notarytool` (recommended) or the older `altool`:

```bash
xcrun notarytool submit VideoEditor.dmg --keychain-profile "AC_PASSWORD_PROFILE" --wait
xcrun stapler staple VideoEditor.dmg
```

Automated helper script:
- See `scripts/create_dmg.sh` which optionally codesigns the `.app` (if you pass a signing identity) and produces a compressed DMG.

Local and CI builds for multiple platforms

Local macOS per-architecture builds:
- Use `./scripts/build_mac_arch.sh arm64` to build an Apple Silicon DMG locally.
- Use `./scripts/build_mac_arch.sh x86_64` on an Apple Silicon machine with Rosetta installed (or on an Intel mac) to build an Intel DMG.

Windows .exe and cross-arch CI builds:
- Building a Windows `.exe` must be performed on Windows (or on a Windows runner). To automate this, a GitHub Actions workflow is included at `.github/workflows/build.yml` which builds:
	- Windows `.exe` on `windows-latest`.
	- macOS Intel DMG on an Intel macOS runner.
	- macOS Apple Silicon DMG on an Apple Silicon macOS runner.

To run CI builds, push a tag (for example `v1.0.0`) or trigger the workflow manually from the Actions tab. Artifacts will be uploaded for download.

Notes:
- CI runner availability may vary; if the Intel macOS runner is not available in your account you can run the Intel build locally under Rosetta or use a self-hosted Intel mac.
- Code signing and notarization steps are left manual in the workflow; add secrets and signing steps if you want automated signing.
