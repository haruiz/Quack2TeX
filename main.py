
import numpy as np
from dotenv import load_dotenv, find_dotenv

import quack2tex

load_dotenv(find_dotenv())



@quack2tex.latify(model="models/gemini-1.5-flash-latest")
def sqrt(x: float):
    """
    Compute the square root of a number.
    :param x: The number.
    :return: The square root of the number.
    """
    x = x ** 0.5
    return x

@quack2tex.latify(model="models/gemini-1.5-flash-latest")
def riemman_sum(f, a, b, n):
    """
    Compute the Riemman sum of a function.
    :param f: The function.
    :param a: The lower bound.
    :param b: The upper bound.
    :param n: The number of subintervals.
    :return: The Riemman sum.
    """
    dx = (b - a) / n
    return sum(f(a + i * dx) * dx for i in range(n))

@quack2tex.latify(model="models/gemini-1.5-flash-latest")
def gaussian_function(x):
   """
   Compute the integral of a function.
   :param x: The number.
   :return: The integral of the number.
   """
   return np.exp(-x**2)

@quack2tex.latify(model="models/gemini-1.5-flash-latest")
def standard_deviation(data):
    """
    Compute the integral of a function.
    :param f: The function.
    :param a: The lower bound.
    :param b: The upper bound.
    :param n: The number of subintervals.
    :return: The integral.
    """
    return np.std(data)


if __name__ == "__main__":
    quack2tex.run_app()
