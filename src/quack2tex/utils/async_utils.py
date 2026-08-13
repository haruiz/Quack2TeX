import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async ModiHub operation from Quack2TeX's synchronous PyQt call paths.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: T | None = None
    error: BaseException | None = None

    def runner() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(coro)
        except BaseException as ex:
            error = ex

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if error is not None:
        raise error
    return result
