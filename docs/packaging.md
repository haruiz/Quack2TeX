# Packaging

Quack2Tex uses PyInstaller as the cross-platform packaging base.

## Layout

```text
packaging/
  pyinstaller/
    entrypoint.py
    quack2tex.spec
  macos/
    build-dmg.sh
  windows/
    installer.iss
```

The ModiHub submodule must be initialized before packaging:

```bash
git submodule update --init --recursive
uv sync
```

The Makefile targets do this through `package-deps`.

## macOS

Build macOS artifacts from macOS. The output is unsigned, so the resulting app
or DMG is suitable for local testing and manual distribution, not notarized
public distribution.

Install the one external DMG builder dependency:

```bash
brew install create-dmg
```

From the repository root, initialize dependencies and run the source check:

```bash
git submodule update --init --recursive
uv sync
make check
```

If PyQt resource files changed, rebuild the generated resource module before
packaging:

```bash
make res
```

Create the macOS `.app` bundle:

```bash
make mac-app
```

This writes `dist/Quack2Tex.app`.

Create the draggable installer DMG:

```bash
make mac-dmg
```

`make mac-dmg` runs `make mac-app` first, then calls
`packaging/macos/build-dmg.sh`. The final installer is
`dist/Quack2Tex.dmg`.

After installing the app, provider API keys should be added from
**Settings > Preferences > Providers**. The app stores them in the operating
system keychain. No `.env` file is needed for normal installed-app use.

If `make mac-dmg` fails, check the two common causes first:

- `dist/Quack2Tex.app` is missing: run `make mac-app`.
- `create-dmg` is missing: run `brew install create-dmg`.

## Windows

Build the PyInstaller folder bundle:

```bash
make windows-exe
```

Build the installer with Inno Setup:

```powershell
ISCC packaging/windows/installer.iss
```

or:

```bash
make windows-installer
```

Build Windows artifacts on Windows. PyInstaller does not reliably cross-compile
Windows installers from macOS.

## GitHub Actions

The workflow in `.github/workflows/build-installers.yml` builds unsigned macOS
and Windows artifacts when a `v*` tag is pushed or when it is run manually. It
uses recursive submodule checkout:

```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    submodules: recursive
```

Because `deps/modihub` is a submodule, this checkout setting is required for CI
packaging.

## Runtime Assets

The installer bundles Python code, PyQt resources, and the ModiHub package from
`deps/modihub`.

Quack2Tex uses only ModiHub's client/model-listing layer. ModiHub's evaluation
dependencies are optional through `modihub[eval]` and are not installed for the
Quack2Tex app bundle.

Whisper model weights are not bundled by default. They are downloaded by Whisper
when the selected model is first used, unless they already exist in the user's
Whisper cache.

`ffmpeg` is also not bundled by default. Voice transcription requires a runnable
`ffmpeg` command on `PATH`.

On Apple Silicon, make sure the Python runtime and OpenSSL libraries are both
arm64. The PyInstaller spec explicitly prefers `/opt/homebrew/opt/openssl@3`
when it exists, because Intel Homebrew libraries under `/usr/local` cannot be
loaded by an arm64 app bundle.

Qt WebEngine needs the bundled `QtWebEngineProcess` helper. The PyInstaller
runtime hook sets `QTWEBENGINEPROCESS_PATH` to the helper copied under
`PyQt6/Qt6/lib/QtWebEngineCore.framework` so the frozen app can find it after
being moved into a `.app` bundle.
