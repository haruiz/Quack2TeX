# Quack2Tex 🦆

Ever found yourself battling with equations while writing papers in LaTeX, wishing there was a way to just snap a picture and boom—LaTeX code? Well, I did too. After too many late nights and too much coffee, I finally decided to do something about it. The result? Quack2Tex.

**Quack2Tex** is a handy tool that facilitates turning images of math equations and charts into LaTeX code, quickly and easily!. But it doesn't stop there! It also has cool features like guessing the location from a photo, identifying recipes from food pictures, and explaining code from images. Rendered as a floating menu on your screen, Quack2Tex is always at your fingertips, making it easy to access anytime you need it.

## 🚀 Features

Certainly! Here's the revised version without emoticons:

---

- **2025-05-01** – Quack2Tex v1.0.9 is out! 🎉  

  This update introduces several powerful new features and improvements:
  * **Voice Input Support**: You can now interact with Quack2Tex using voice, in addition to screen, clipboard, and text input.
  * **Database Persistence**: Prompts and responses now can be saved to a local database for future reference.
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

## 📚 Usage

You can run **Quack2Tex** in multiple ways depending on your preference.

### 🏁 Quick Start (via terminal)

Run the app with your API keys as command-line options:

```bash
quack2tex --gemini-api-key <your_gemini_api_key> \
          --openai-api-key <your_openai_api_key> \
          --anthropic-api-key <your_anthropic_api_key> \
          --groq-api-key <your_groq_api_key>
```

### 🌱 Alternative: Using Environment Variables

You can set the API keys as environment variables:

```bash
export GEMINI_API_KEY=<your_gemini_api_key>
export OPENAI_API_KEY=<your_openai_api_key>
export ANTHROPIC_API_KEY=<your_anthropic_api_key>
export GROQ_API_KEY=<your_groq_api_key>

quack2tex
```

### 📄 `.env` File Support

You can also create a `.env` file in the root directory with the following contents:

```env
GEMINI_API_KEY=<your_gemini_api_key>
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
GROQ_API_KEY=<your_groq_api_key>
```

The app will automatically load these variables using `python-dotenv`.

### 🛠️ Help & Options

To explore all available options:

```bash
quack2tex --help
```

### 🧠 Optional: Using LLava Models via Ollama

Quack2Tex also supports LLava models via the [Ollama API](https://ollama.com). Be sure to have Ollama running and properly configured.

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
2. Create a new branch.
3. Make your changes.
4. Commit and push your changes.
5. Open a Pull Request.

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
