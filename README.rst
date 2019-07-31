File locks
==========

This library provides a safe wrapper around ``flock(2)``. It avoids problems when using locks in multi-threaded applications, while still exposing exclusive and shared locks.

It also contains a caching utility, ``fslock.cache.cache_get_or_set()``, which can be use to safely cache files that are expensive to produce on disk.
