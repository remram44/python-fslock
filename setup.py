import io
import os
from setuptools import setup


# pip workaround
os.chdir(os.path.abspath(os.path.dirname(__file__)))


# Need to specify encoding for PY3, which has the worst unicode handling ever
with io.open('README.rst', encoding='utf-8') as fp:
    description = fp.read()
setup(name='fslock',
      version='1.1',
      packages=['fslock'],
      description="Shared and exclusive file locking using flock(2)",
      author="Remi Rampin",
      author_email='remirampin@gmail.com',
      maintainer="Remi Rampin",
      maintainer_email='remirampin@gmail.com',
      url='https://gitlab.com/remram44/python-fslock',
      project_urls={
          'Homepage': 'https://gitlab.com/remram44/python-fslock',
          'Say Thanks': 'https://saythanks.io/to/remram44',
          'Source': 'https://gitlab.com/remram44/python-fslock',
          'Tracker': 'https://gitlab.com/remram44/python-fslock/issues',
      },
      long_description=description,
      license='MIT',
      keywords=['lock', 'flock', 'file lock', 'locking', 'filesystem'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3 :: Only'])
