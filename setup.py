import io
import os
import sys
from shutil import rmtree

from setuptools import Command, setup

NAME = 'foamio'
DESCRIPTION = 'OpenFOAM routines.'
URL = 'https://github.com/StasF1/foam2py'
EMAIL = 'stanislau.stasheuski@gmail.com'
AUTHOR = 'Stanislau Stasheuski'
REQUIRES_PYTHON = '>=3.6'
VERSION = '0.2.0'

REQUIRED = [
    'matplotlib',
    'numpy',
    'pandas',
]
EXTRAS = {
    'pyvista': '0.36',
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

about = {'__version__': VERSION}


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system(f'git tag v{about["__version__"]}')
        os.system('git push --tags')

        sys.exit()


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    py_modules=['foamio'],
    entry_points={
        'console_scripts': ['foamio = foamio._cli:main'],
    },
    scripts=[],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        f'Programming Language :: Python :: {REQUIRES_PYTHON.replace(">=", "")}'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)
