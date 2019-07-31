import contextlib
import os

from . import FSLockExclusive, FSLockShared


@contextlib.contextmanager
def cache_get_or_set(path, create_function):
    """This function is a file cache safe for multiple processes (locking).

    It is used like so::

        # The path to be access or created
        cache_filename = '/tmp/cache/cachekey123'

        # This function is called to create the entry if it doesn't exist
        def create_entry():
            with open(cache_filename, 'w') as fp:
                fp.write('%d\n' % long_computation())

        with cache_get_or_set(cache_filename, create_entry):
            # In this with-block, the file or directory is locked with a shared
            # lock, so it won't be changed or removed
            with open(cache_filename) as fp:
                print(fp.read())
    """
    lock_path = path + '.lock'
    while True:
        with contextlib.ExitStack() as lock:
            try:
                lock.enter_context(FSLockShared(lock_path))
            except FileNotFoundError:
                pass
            else:
                if os.path.exists(path):
                    # Entry exists and we have it locked, return it
                    yield
                    return
                # Entry was removed while we waited -- we'll try creating

        with FSLockExclusive(lock_path) as lock:
            if os.path.exists(path):
                # Cache was created while we waited
                # We can't downgrade to a shared lock, so restart
                continue
            else:
                # Cache doesn't exist and we have it locked -- create
                create_function()

                # We can't downgrade to a shared lock, so restart
                continue
