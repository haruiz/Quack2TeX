import sys
import traceback

from PySide6.QtCore import QRunnable, QObject, Signal, QThreadPool


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    """

    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class WorkerThread(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(WorkerThread, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)
        self._cancelled = False

        # Add the callback to our kwargs
        if "progress_callback" in self.kwargs:
            self.kwargs["progress_callback"] = self.signals.progress

    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            print(exctype, value)
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            if not self._cancelled:
                self.signals.result.emit(result)  # Return the result of the processing
        finally:
            if not self._cancelled:
                self.signals.finished.emit()

    def start(self):
        """
        Start the thread
        """
        QThreadPool.globalInstance().start(self)

    def stop(self):
        """
        Cancel the thread
        """
        self._cancelled = True
