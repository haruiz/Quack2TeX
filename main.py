from dotenv import load_dotenv, find_dotenv
import quack2tex

load_dotenv(find_dotenv())

if __name__ == "__main__":
   quack2tex.run_app(model_name="models/gemini-1.5-flash-latest")