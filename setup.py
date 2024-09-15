import io
import os
from setuptools import setup


os.chdir(os.path.abspath(os.path.dirname(__file__)))


with io.open('README.rst', encoding='utf-8') as fp:
    description = fp.read()
setup(name='fslock',
      version='2.1.1',
      packages=['fslock'],
      description="Shared and exclusive file locking using flock(2)",
      author="Remi Rampin",
      author_email='remi@rampin.org',
      maintainer="Remi Rampin",
      maintainer_email='remi@rampin.org',
      url='https://github.com/remram44/python-fslock',
      project_urls={
          'Source': 'https://github.com/remram44/python-fslock',
          'Tracker': 'https://github.com/remram44/python-fslock/issues',
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
