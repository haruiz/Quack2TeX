# Quack2Tex 🦆

Ever found yourself switching between screenshots, notes, prompts, and model chats just to turn a quick idea into something useful? **Quack2Tex** started as a fast way to capture equations and convert them into LaTeX, and has grown into a small desktop assistant for multimodal work.

Quack2Tex lives as a customizable floating duck menu on your screen. It can work with screenshots, images, clipboard text, typed prompts, uploaded files, and voice input to run reusable AI actions such as image-to-LaTeX, chart interpretation, code explanation, location guessing, recipe identification, and custom prompts. It also keeps useful outputs in local history, stores provider credentials securely in your OS keychain, persists app preferences in a local database, supports configurable duck themes and quick actions, and includes a Pomodoro timer for focused writing or study sessions. With macOS and Windows packaging support, Quack2Tex is designed to feel like a lightweight desktop tool you can keep nearby while working.

## 🚀 Features

- **2026-08-12** – Quack2Tex adds secure preferences, Pomodoro, and installer packaging! 🎉

  This update expands Quack2Tex with desktop-app polish, safer configuration, and release tooling:
  * **Secure Credential Storage**: Provider API keys are now stored through the operating system keychain using `keyring`.
  * **Database-Backed Preferences**: Themes, presets, Pomodoro settings, duck images, and app preferences now persist in the local database.
  * **Pomodoro Timer**: A configurable Pomodoro action is available from the floating menu, with adjustable durations and audio-gated phase transitions.
  * **Duck Gallery and UI Polish**: The floating menu, duck assets, loading states, settings panels, and output dialogs received visual and interaction updates.
  * **ModiHub Submodule Setup**: ModiHub is now managed as a `deps/modihub` submodule with matching source and development documentation updates.
  * **Installer Packaging**: PyInstaller, macOS DMG, Windows Inno Setup, Makefile targets, and GitHub Actions packaging workflow were added.

- **2025-05-01** – Quack2Tex v1.0.9 is out! 🎉  

  This update introduces several powerful new features and improvements:
  * **Voice Input Support**: You can now interact with Quack2Tex using voice, in addition to screen, clipboard, and text input.
  * **Database Persistence**: Prompts and responses now can be saved to a local database for future reference.
  * **Generated History Titles**: Saved model outputs are summarized into concise history titles so recent items are easier to scan.
  * **Grouped Settings**: Preferences are organized into General, Voice, Providers, Duck, and Presets sections. Preset save/reset actions are shown only on the Presets section.
  * **Quick Action**: Hold the mouse button on the rubber duck icon to quickly trigger actions. These can be customized from the **Settings** menu.
  > **Important:**
  > This release includes a major update to the database schema.
  > To ensure the new features work correctly, you must **delete the old database file** before running the app.
  **Database location:** `~/.quack2tex/quack2tex.db`
  **To delete it, run:**
  ```bash
  rm ~/.quack2tex/quack2tex.db
  ```

- **2024-10-18**: Quack2Tex v1.0.0 is out! 🎉   
  - Added functionality for users to customize the rubber-duck menu. A new "Settings" option allows users to create and manage custom actions.
  - Action Grouping: Users can now group actions in the settings menu for better organization and streamlined access.
  - Multi-Model Selection: Users can now choose which model or combination of models to use for generating outputs, enhancing flexibility and multimodel inference.
  - New Input Mode: A "Clipboard" input mode has been introduced, enabling users to use clipboard content as input for selected actions.

- **2024-9-10**: Quack2Tex was released! 🎉 

  - **Image to LaTeX**: Convert pictures of equations or symbols into LaTeX code—no more manual typing!
  - **Location Guessing**: Upload a photo, and Quack2Tex will try to figure out where it was taken.
  - **Recipe Finder**: Snap a picture of your meal, and Quack2Tex will tell you what dish it is.
  - **Code Explainer**: Got a screenshot of code? Quack2Tex can explain what it does.

[//]: # (![Quack2Tex in action]&#40;https://raw.githubusercontent.com/haruiz/Quack2TeX/main/images/quack2tex.gif&#41;)

See the video below for a demo of Quack2Tex in action:

[![Watch the video](https://img.youtube.com/vi/kkyJtEnfUgo/maxresdefault.jpg)](https://youtu.be/kkyJtEnfUgo)

## 🧠 Powered By

Under the hood, Quack2Tex  leverages state-of-the-art multimodal models like Gemini, GPT-4o, and Lava to analyze the content in the images. Whether you're converting handwritten notes into LaTeX or identifying the location of a stunning sunset photo, Quack2Tex has you covered.

## 🔧 Installation

To get started with Quack2Tex, follow these steps:

```bash
pip install quack2tex
```

### Install from Source

For local development, clone the repository with its `modihub` submodule:

```bash
git clone --recurse-submodules git@github.com:haruiz/Quack2TeX.git
cd Quack2TeX
uv sync
uv run quack2tex
```

If you already cloned the repository without submodules, initialize them before
running `uv sync`:

```bash
git submodule update --init --recursive
uv sync
```

Quack2Tex keeps `modihub` in `deps/modihub` so the app can use ModiHub's
provider-backed model discovery while keeping the dependency source inside this
repository checkout. The local source is configured in `pyproject.toml`:

```toml
[tool.uv.sources]
modihub = { path = "deps/modihub", editable = true }
```

## 📚 Usage

You can run **Quack2Tex** in multiple ways depending on your preference.

### 🔐 Recommended: Save API Keys in Settings

Open **Settings > Preferences > Providers** and save your provider API keys.
Quack2Tex stores these keys in your operating
system's secure credential store, such as macOS Keychain, Windows Credential
Manager, or the Linux Secret Service/KWallet backend when available.

Environment variables still take precedence, so command-line keys and exported
variables can override stored settings for a single session.

Quack2Tex stores non-secret preferences in `~/.quack2tex/quack2tex.db`.

### ⚙️ Settings Layout

The Settings dialog is modal. The floating duck menu is hidden while Settings is
open and restored when the dialog closes.

Top-level Settings sections:

- **Menu Manager**: Create and organize custom duck-menu actions.
- **Prompts Browser**: Review saved prompts and model responses. Saved prompts
  display generated titles based on model output when available.
- **Preferences**: Configure app preferences in grouped tabs:
  - **General**: Theme and Pomodoro timing.
  - **Voice**: FFmpeg path for voice transcription.
  - **Providers**: API keys.
  - **Duck**: Main duck image.
  - **Presets**: Quick preset definitions. The Save Preset and Reset Presets
    buttons appear in a footer only when this tab is active.

### 🏁 Quick Start

Launch the app and add provider keys in **Settings > Preferences > Providers**.
Keys are stored in your operating system keychain.

### 🌱 Optional: Using Environment Variables

For CLI or development workflows, you can still set API keys as environment
variables before launch:

```bash
export GEMINI_API_KEY=<your_gemini_api_key>
export OPENAI_API_KEY=<your_openai_api_key>
export ANTHROPIC_API_KEY=<your_anthropic_api_key>
export GROQ_API_KEY=<your_groq_api_key>

quack2tex
```

### 🛠️ Help & Options

To explore all available options:

```bash
quack2tex --help
```

### 🧠 Optional: Using LLava Models via Ollama

Quack2Tex also supports LLava models via the [Ollama API](https://ollama.com). Be sure to have Ollama running and properly configured.

### 🎙️ Voice Input Requirements

Voice input uses OpenAI Whisper locally. Whisper requires the `ffmpeg` command to
be available.

On macOS, install it with Homebrew:

```bash
brew install ffmpeg
```

Quack2Tex auto-detects common `ffmpeg` locations such as
`/opt/homebrew/bin/ffmpeg` and `/usr/local/bin/ffmpeg`. If auto-detection picks
the wrong command, open **Settings > Preferences > Voice** and set **FFmpeg
Path** explicitly. Leave the field blank to return to auto-detect.

The warning `FP16 is not supported on CPU; using FP32 instead` is expected on
CPU-only machines and does not prevent transcription.

### 🕘 History

Use the save button in the output viewer to store model output in the local
database. Quack2Tex asks the selected model to create a short title from the
saved output and stores that title with the prompt. If title generation fails,
the app falls back to a local title based on the output text and still saves the
history item.

In **Settings > Prompts Browser**, prompt-level items use the generated title.
Response-level items show the model name. You can delete either an entire prompt
history item or a single model response from the context menu.

### 🐍 Running from Python

You can also run the app programmatically. Check out the `main.py` file for an example:

```python
from dotenv import load_dotenv, find_dotenv
import quack2tex
# Load environment variables
load_dotenv(find_dotenv())
# Run the app
quack2tex.run_app()
```

Let me know if you'd like to include examples, expected outputs, or Docker support!

## 📝 Roadmap

- [x] Support clipboard copy to be used in the prompt
- [x] Support gemini, gpt-4o, and lava models
- [x] Allow user add custom actions to the rubber-duck menu
- [x] Persist images and results in a database
- [ ] Create window, mac, and linux executables

## 🤝 Contributing

Want to help make Quack2Tex better? Feel free to contribute by following these steps:

1. Fork the repo.
2. Clone your fork with submodules: `git clone --recurse-submodules <your-fork-url>`.
3. Create a new branch.
4. Run `uv sync`.
5. Make your changes.
6. Commit and push your changes.
7. Open a Pull Request.

See [docs/development.md](docs/development.md) for local setup and submodule
maintenance notes.

Installer packaging notes live in [docs/packaging.md](docs/packaging.md).

## 📦 Create a macOS Installer

Build the unsigned macOS app bundle and DMG from a macOS checkout:

```bash
brew install create-dmg
git submodule update --init --recursive
uv sync
make check
make mac-dmg
```

The installer is written to `dist/Quack2Tex.dmg`. After installing, add API keys
from **Settings > Preferences > Providers**.

If Qt resources changed, run `make res` before `make mac-dmg`.

Before opening a pull request, run:

```bash
make check
```

## 🛠️ Troubleshooting

If you run into any problems, check out the [Issues](https://github.com/haruiz/Quack2TeX/issues) section on GitHub.

## 📄 License

Quack2Tex is open-source and available under the MIT License—see the [LICENSE](LICENSE) file for more details.

## Actions

| Action                          | Description                                                                               |
|---------------------------------|-------------------------------------------------------------------------------------------|
| `move the duck`                 | Move the duck to a different location on the screen pressing command/ctrl and dragging it. |
| `expand or execute action menu` | Double click on the icon                                                                  |
## 📧 Contact

Got questions? You can reach out to me at [henryruiz22@gmail.com](mailto:henryruiz22@gmail.com).
