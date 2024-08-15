import sys
import traceback
from functools import wraps

from quack2tex.utils import GuiUtils


def gui_exception(func):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            print(f"Exception in {func.__name__}: {ex}")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            GuiUtils.show_error_message(
                f"{str(traceback.format_exception_only( exc_type, exc_value )[0])}"
            )

    return wrapper
