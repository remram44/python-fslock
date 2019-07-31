"""File locking implementation using flock(2).
"""

import contextlib
import fcntl
import logging
import multiprocessing
import os
import signal


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def timeout_syscall(seconds):
    """Interrupt a system-call after a time (main thread only).

    Warning: this only works from the main thread! Trying to use this on
    another thread will cause the call to not timeout, and the main thread will
    receive an InterruptedError instead!

    Example::

        with timeout_syscall(5):
            try:
                socket.connect(...)
            except InterruptedError:
                raise ValueError("This host does not respond in time")
    """
    def timeout_handler(signum, frame):
        raise InterruptedError

    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


def _lock_process(pipe, filepath, exclusive, timeout=None):
    """Locking function, runs in a subprocess.

    We run the locking in a subprocess so that we are the main thread
    (required to use SIGALRM) and to avoid spurious unlocking on Linux (which
    can happen if a different file descriptor for the same file gets closed,
    even by another thread).
    """
    try:
        # Reset signal handlers
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        # Open the file
        mode = os.O_RDONLY | os.O_CREAT if exclusive else os.O_RDONLY
        try:
            fd = os.open(filepath, mode)
        except FileNotFoundError:
            pipe.send('NOTFOUND')
            return

        # Lock it
        op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if timeout is None:
            fcntl.flock(fd, op)
        elif timeout == 0:
            fcntl.flock(fd, op | fcntl.LOCK_NB)
        else:
            with timeout_syscall(timeout):
                try:
                    fcntl.flock(fd, op)
                except InterruptedError:
                    pipe.send('TIMEOUT')
                    return
        pipe.send('LOCKED')
    except Exception:
        pipe.send('ERROR')
        raise

    # Wait for unlock message then exit
    assert pipe.recv() == 'UNLOCK'

    # Exiting releases the lock


@contextlib.contextmanager
def _lock(filepath, exclusive, timeout=None):
    type_ = "exclusive" if exclusive else "shared"

    pipe, pipe2 = multiprocessing.Pipe()
    proc = multiprocessing.Process(
        target=_lock_process,
        args=(pipe2, filepath, exclusive, timeout),
    )
    try:
        proc.start()

        out = pipe.recv()
        if out == 'LOCKED':
            logger.info("Acquired %s lock: %r", type_, filepath)
        elif out == 'TIMEOUT':
            logger.debug("Timeout getting %s lock: %r", type_, filepath)
            raise TimeoutError
        elif out == 'NOTFOUND':
            raise FileNotFoundError
        else:
            logger.error("Error getting %s lock: %r", type_, filepath)
            raise OSError("Error getting %s lock: %r", type_, filepath)

        yield
    finally:
        logger.debug("Releasing %s lock: %r", type_, filepath)
        pipe.send('UNLOCK')
        proc.join(10)
        if proc.exitcode != 0:
            logger.critical("Failed (%r) to release %s lock: %r",
                            proc.exitcode, type_, filepath)
            raise SystemExit("Failed (%r) to release %s lock: %r" % (
                proc.exitcode, type_, filepath,
            ))
        logger.info("Released %s lock: %r", type_, filepath)


def FSLockExclusive(filepath, timeout=None):
    """Get an exclusive lock.

    The file is created if it doesn't exist.
    """
    return _lock(filepath, True, timeout=timeout)


def FSLockShared(filepath, timeout=None):
    """Get a shared lock.

    :raises FileNotFoundError: if the file doesn't exist.
    """
    return _lock(filepath, False, timeout=timeout)
