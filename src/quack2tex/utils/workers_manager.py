from PySide6.QtCore import QObject, QThreadPool, Signal
from .worker import Worker

class WorkerManager(QObject):
    """
    Manages multiple worker threads, enabling concurrent execution and signal handling.
    """

    # Define custom signals for worker events
    all_workers_finished = Signal()
    worker_finished = Signal()
    worker_error = Signal(tuple)
    worker_result = Signal(object)
    worker_progress = Signal(int)

    def __init__(self, max_workers=5):
        super().__init__()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(max_workers)

        # Store worker instances for management
        self.workers = []


    def create_worker(self, fn, *args, **kwargs):
        """
        Creates a Worker with the specified function, arguments, and keyword arguments.

        :param fn: The function to run on this worker thread
        :param args: Arguments to pass to the function
        :param kwargs: Keywords to pass to the function
        :return: Worker instance
        """
        worker = Worker(fn, *args, **kwargs)
        worker.signals.finished.connect(self.on_worker_finished)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.result.connect(self.on_worker_result)
        worker.signals.progress.connect(self.on_worker_progress)

        # Keep track of the worker
        self.workers.append(worker)
        return worker

    def start_worker(self, worker):
        """
        Starts a given worker by adding it to the thread pool.
        """
        self.threadpool.start(worker)

    def on_worker_finished(self):
        """
        Slot for handling a worker's finished signal.
        """
        self.worker_finished.emit()
        # Check if all workers are finished
        if all(not w.isRunning() for w in self.workers):
            self.all_workers_finished.emit()

    def on_worker_error(self, error):
        """
        Slot for handling a worker's error signal.

        :param error: Tuple containing (exctype, value, traceback)
        """
        self.worker_error.emit(error)

    def on_worker_result(self, result):
        """
        Slot for handling a worker's result signal.

        :param result: Result returned from the worker's processing
        """
        self.worker_result.emit(result)

    def on_worker_progress(self, progress):
        """
        Slot for handling a worker's progress signal.

        :param progress: Progress percentage (int)
        """
        self.worker_progress.emit(progress)

    def start_all_workers(self):
        """
        Starts all workers that have been created and added to the manager.
        """
        for worker in self.workers:
            self.start_worker(worker)

    def wait_for_completion(self):
        """
        Blocks until all workers in the pool have finished.
        """
        self.threadpool.waitForDone()
