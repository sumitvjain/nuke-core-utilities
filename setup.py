from setuptools import find_packages, setup

setup(
    name='nuke_core_utilities',
    version='0.1.1',
    description="Reusable Python utilities for Foundry Nuke to simplify development, scripting, and pipeline integration.",

    author='Sumit S',
    author_email='sumitvjain@yahoo.com',

    package_dir={'': 'src'},
    packages=find_packages(where='src'),

)