import contextlib
import os
import shutil

from . import FSLockExclusive, FSLockShared


@contextlib.contextmanager
def cache_get_or_set(cache_dir, key, create_function):
    """This function is a file cache safe for multiple processes (locking).

    It is used like so::

        # This function is called to create the entry if it doesn't exist
        def create_it(tmp_path):
            # In this function, the path is locked with an exclusive lock
            # `tmp_path` will be renamed to the cache path on success
            with open(tmp_path, 'w') as fp:
                fp.write('%d\n' % long_computation())

        with cache_get_or_set('/tmp/cache', 'key123', create_it) as entry_path:
            # In this with-block, the path is locked with a shared lock, so it
            # won't be changed or removed
            with open(entry_path) as fp:
                print(fp.read())
    """
    entry_path = os.path.join(cache_dir, key + '.cache')
    lock_path = os.path.join(cache_dir, key + '.lock')
    temp_path = os.path.join(cache_dir, key + '.temp')
    while True:
        with contextlib.ExitStack() as lock:
            try:
                lock.enter_context(FSLockShared(lock_path))
            except FileNotFoundError:
                pass
            else:
                if os.path.exists(entry_path):
                    # Entry exists and we have it locked, return it
                    yield entry_path
                    return
                # Entry was removed while we waited -- we'll try creating

        with FSLockExclusive(lock_path):
            if os.path.exists(entry_path):
                # Cache was created while we waited
                # We can't downgrade to a shared lock, so restart
                continue
            else:
                # Remove temporary file
                if os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
                elif os.path.isfile(temp_path):
                    os.remove(temp_path)

                try:
                    # Cache doesn't exist and we have it locked -- create
                    create_function(temp_path)
                except:
                    # Creation failed, clean up before unlocking!
                    if os.path.isdir(temp_path):
                        shutil.rmtree(temp_path)
                    elif os.path.isfile(temp_path):
                        os.remove(temp_path)
                    raise
                else:
                    # Rename it to destination
                    os.rename(temp_path, entry_path)

                # We can't downgrade to a shared lock, so restart
                continue
