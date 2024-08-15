# Quack2Tex 🦆

Ever found yourself battling with equations while writing papers in LaTeX, wishing there was a way to just snap a picture and boom—LaTeX code? Well, I did too. After too many late nights and too much coffee, I finally decided to do something about it. The result? Quack2Tex.

**Quack2Tex** is a handy tool that facilitates turning images of math equations and charts into LaTeX code, quickly and easily!. But it doesn't stop there! It also has cool features like guessing the location from a photo, identifying recipes from food pictures, and explaining code from images. Rendered as a floating menu on your screen, Quack2Tex is always at your fingertips, making it easy to access anytime you need it.

## 🚀 Features

- **Image to LaTeX**: Convert pictures of equations or symbols into LaTeX code—no more manual typing!
- **Location Guessing**: Upload a photo, and Quack2Tex will try to figure out where it was taken.
- **Recipe Finder**: Snap a picture of your meal, and Quack2Tex will tell you what dish it is.
- **Code Explainer**: Got a screenshot of code? Quack2Tex can explain what it does.

[//]: # (![Quack2Tex in action]&#40;https://raw.githubusercontent.com/haruiz/Quack2TeX/main/images/quack2tex.gif&#41;)

[![Watch the video](https://img.youtube.com/vi/kkyJtEnfUgo/maxresdefault.jpg)](https://youtu.be/kkyJtEnfUgo)

## 🧠 Powered By

Under the hood, Quack2Tex  leverages state-of-the-art multimodal models like Gemini, GPT-4o, and Lava to analyze the content in the images. Whether you're converting handwritten notes into LaTeX or identifying the location of a stunning sunset photo, Quack2Tex has you covered.

## 🔧 Installation

To get started with Quack2Tex, follow these steps:

```bash
pip install quack2tex
```

## 📚 Usage

In the terminal, run the following command:

```bash
quack2tex --help # to see the available options
quack2tex --model <model_name> # to run the app

# Example
quack2tex --model "models/gemini-1.5-flash-latest" # fastest model!
quack2tex --model "gpt-4o"
quack2tex --model "llava:34b"
```

make you set the env variables `GOOGLE_API_KEY` and/or `OPENAI_API_KEY` for using google and openai models respectively. 
You can also use LLava models through the ollama api.
You can also run the app from python, see the `main.py` file for an example.

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

## 📧 Contact

Got questions? You can reach out to me at [henryruiz22@gmail.com](mailto:henryruiz22@gmail.com).
