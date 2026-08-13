import multiprocessing

from dotenv import find_dotenv, load_dotenv

import quack2tex


def main() -> None:
    multiprocessing.freeze_support()
    load_dotenv(find_dotenv())
    quack2tex.run_app()


if __name__ == "__main__":
    main()
