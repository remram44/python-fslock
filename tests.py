import contextlib
import logging
import math
import subprocess
import threading
import time
import unittest

import fslock


logging.basicConfig(level=logging.DEBUG)


class TestLocks(unittest.TestCase):
    def test_sharedlock_nonexistent(self):
        stack = contextlib.ExitStack()
        with self.assertRaises(FileNotFoundError):
            stack.enter_context(fslock.FSLockShared('/tmp/nonex_shared'))

    def test_exclusivelock_nonexistent(self):
        stack = contextlib.ExitStack()
        with self.assertRaises(FileNotFoundError):
            stack.enter_context(
                fslock.FSLockExclusive('/tmp/nonex_exclusive_folder/file')
            )

        with fslock.FSLockExclusive('/tmp/nonex_exclusive'):
            pass

    def test_shared(self):
        stack = contextlib.ExitStack()
        with stack:
            # Create a file
            with open('/tmp/shared', 'w'):
                pass

            # Get shared lock
            stack.enter_context(fslock.FSLockShared('/tmp/shared'))

            # Get another shared lock
            with fslock.FSLockShared('/tmp/shared'):
                pass

            # Check that it's locked using the shell
            res = subprocess.call([
                'flock', '--exclusive', '--nonblock',
                '--conflict-exit-code', '43',
                '/tmp/shared',
                '-c', 'true',
            ])
            self.assertEqual(res, 43)

            # Try to get an exclusive lock
            def try_exclusive():
                with fslock.FSLockExclusive('/tmp/shared'):
                    try_exclusive.got_it = True

            try_exclusive.got_it = False
            t = threading.Thread(target=try_exclusive)
            t.setDaemon(True)
            t.start()
            time.sleep(1)
            self.assertFalse(try_exclusive.got_it)

            # Get a shared lock with timeout
            stack.enter_context(fslock.FSLockShared('/tmp/shared', timeout=2))

            # Try to get an exclusive lock with timeout
            start = time.perf_counter()
            with self.assertRaises(TimeoutError):
                stack.enter_context(
                    fslock.FSLockExclusive('/tmp/shared', timeout=2)
                )
            self.assertTrue(math.fabs(time.perf_counter() - start - 2) < 0.05)

    def test_exclusive(self):
        with fslock.FSLockExclusive('/tmp/exclusive'):
            # Check that it's locked using the shell
            res = subprocess.call([
                'flock', '--shared', '--nonblock',
                '--conflict-exit-code', '43',
                '/tmp/exclusive',
                '-c', 'true',
            ])
            self.assertEqual(res, 43)

            # Try to get a shared lock
            def try_shared():
                with fslock.FSLockShared('/tmp/exclusive'):
                    try_shared.got_it = True

            try_shared.got_it = False
            t = threading.Thread(target=try_shared)
            t.setDaemon(True)
            t.start()
            time.sleep(1)
            self.assertFalse(try_shared.got_it)

            # Try to get an exclusive lock
            def try_exclusive():
                with fslock.FSLockExclusive('/tmp/exclusive'):
                    try_exclusive.got_it = True

            try_exclusive.got_it = False
            t = threading.Thread(target=try_exclusive)
            t.setDaemon(True)
            t.start()
            time.sleep(1)
            self.assertFalse(try_exclusive.got_it)

            stack = contextlib.ExitStack()

        with fslock.FSLockExclusive('/tmp/exclusive2', timeout=2):
            # Try to get a shared lock with timeout
            start = time.perf_counter()
            with self.assertRaises(TimeoutError):
                stack.enter_context(
                    fslock.FSLockShared('/tmp/exclusive2', timeout=2)
                )
            self.assertTrue(math.fabs(time.perf_counter() - start - 2) < 0.05)

            # Try to get an exclusive lock with timeout
            start = time.perf_counter()
            with self.assertRaises(TimeoutError):
                stack.enter_context(
                    fslock.FSLockExclusive('/tmp/exclusive2', timeout=2)
                )
            self.assertTrue(math.fabs(time.perf_counter() - start - 2) < 0.05)


if __name__ == '__main__':
    unittest.main()
