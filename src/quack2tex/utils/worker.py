import sys
import traceback
from quack2tex.pyqt import Signal, Slot, QObject, QRunnable
from typing import Callable,  Any


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    These signals are emitted for communication with the main thread:

    - finished: Emitted when the worker finishes processing (no data).
    - error: Emitted when an exception occurs, with a tuple (exctype, value, traceback).
    - result: Emitted with the result of the processing (can be any object).
    - progress: Emitted with progress updates (usually an integer percentage).
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(object)


class Worker(QRunnable):
    """
    A worker thread that runs a given function asynchronously.

    :param fn: The function to be executed in the worker thread.
    :param args: Arguments to pass to the callback function.
    :param kwargs: Keyword arguments to pass to the callback function.
    """

    def __init__(self, fn: Callable, *args: Any, **kwargs: Any):
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Set the progress callback if provided in kwargs
        progress_callback = kwargs.pop("progress_callback", None)
        if progress_callback:
            self.kwargs["progress_callback"] = self.signals.progress

    @Slot()
    def run(self) -> None:
        """
        Runs the provided function with the given arguments and handles exceptions.
        Emits signals for progress, result, or error as appropriate.
        """
        try:
            # Execute the function with arguments and handle progress callback
            if "progress_callback" in self.kwargs:
                progress_callback = self.kwargs.pop("progress_callback")
                result = self.fn(progress_callback, *self.args, **self.kwargs)
            else:
                result = self.fn(*self.args, **self.kwargs)

        except Exception:
            # Print traceback and emit error signal with exception details
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Emit the result signal with the function's result
            self.signals.result.emit(result)
        finally:
            # Emit finished signal to signal completion
            self.signals.finished.emit()
