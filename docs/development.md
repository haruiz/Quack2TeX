# Development

Quack2Tex uses `uv` for local development and keeps ModiHub as a git submodule
under `deps/modihub`.

## Clone

Clone the repository with submodules:

```bash
git clone --recurse-submodules git@github.com:haruiz/Quack2TeX.git
cd Quack2TeX
```

If the repository is already cloned, initialize the submodule:

```bash
git submodule update --init --recursive
```

## Install

Install the editable development environment:

```bash
uv sync
```

Run the app from the environment:

```bash
uv run quack2tex
```

Copy the environment template if you want to launch the app with local provider
keys from a file:

```bash
cp .env.example .env
```

Leave values blank until you need that provider. The real `.env` file is ignored
and should not be committed.

## Audio Dependencies

Voice transcription uses OpenAI Whisper. Whisper shells out to `ffmpeg`, so the
`ffmpeg` command must be available.

On macOS:

```bash
brew install ffmpeg
```

Verify the command is visible to the same shell used to launch Quack2Tex:

```bash
which ffmpeg
ffmpeg -version
```

The app auto-detects common locations such as `/opt/homebrew/bin/ffmpeg` and
`/usr/local/bin/ffmpeg` before falling back to PATH entries. Pyenv shims are
checked last because desktop launches can find a shim that cannot execute the
real binary.

Users can override auto-detection in **Settings > Preferences > Voice** by
setting **FFmpeg Path**. Leave that field blank to use auto-detect.

## Settings UI

The Settings window has three top-level sections:

- **Menu Manager** for custom duck-menu actions.
- **Prompts Browser** for saved prompts and responses.
- **Preferences** for app configuration.

Preferences are grouped into nested tabs: General, Voice, Providers, Duck, and
Presets. Preset editing stays in the Preferences panel, but Save Preset and
Reset Presets live in a footer that is only visible on the Presets tab. This
keeps preset actions visually separate from Voice, Provider, and Duck settings.

The floating duck menu is hidden while the modal Settings window is open and is
restored after the dialog closes.

## History Titles

Saved model outputs are stored in the local database as prompts and responses.
The `prompt` table includes a nullable `title` column used by the Prompts
Browser and recent-history command palette entries.

When a user saves output to the database, Quack2Tex asks the selected model to
generate a short title from the output. If that LLM title call fails, saving
continues with a local fallback title derived from the output text.

`init_db()` includes an idempotent SQLite upgrade that adds `prompt.title` to
existing local databases without deleting history.

## ModiHub Submodule

The submodule is configured in `.gitmodules`:

```text
[submodule "deps/modihub"]
	path = deps/modihub
	url = git@github.com:OpenSciML/modihub.git
```

`pyproject.toml` points `uv` at that checkout:

```toml
[tool.uv.sources]
modihub = { path = "deps/modihub", editable = true }
```

This keeps Quack2Tex self-contained for development while preserving ModiHub's
provider-backed model listing and model factory.

To update ModiHub to the latest commit on its tracked branch:

```bash
git submodule update --remote deps/modihub
uv lock
```

Commit the updated `deps/modihub` gitlink together with `uv.lock`.

## Checks

Run focused Python checks after dependency or model-provider changes:

```bash
make check
```

For narrower checks, compile changed files directly:

```bash
uv run python -m py_compile \
  src/quack2tex/__init__.py \
  src/quack2tex/widgets/prompt_input/prompt_input.py \
  src/quack2tex/windows/main_window.py \
  src/quack2tex/windows/setting_window/menu_item_form.py \
  src/quack2tex/windows/setting_window/preferences_panel.py \
  src/quack2tex/windows/setting_window/prompt_browser.py \
  src/quack2tex/repository/prompt_repository.py
```

For whitespace issues in changed files:

```bash
git diff --check
```
