from setuptools import find_packages, setup

setup(
    name='nuke_core_utilities',
    version='1.0.0',
    description="Reusable Python utilities for Foundry Nuke to simplify development, scripting, and pipeline integration.",

    author='Sumit S',
    author_email='sumitvjain@yahoo.com',
    

    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        "PyYAML>=6.0"
    ],
    python_requires=">=3.10",
    include_package_data=True,
)





# command for execute setup.py file
# python setup.py bdist_wheel

# command for install on custom location
# python -m pip install ^
#   --target G:\Python\ccavfx\pipeline\Nuke_Tools\python_packages ^
#   G:\Python\ccavfx\nuke-core-utilities\dist\nuke_core_utilities-0.2.1-py3-none-any.whl



# .toml file example
# [project]
# name = "nuke-core-utilities"
# version = "0.1.2"
# requires-python = ">=3.10"
# dependencies = [
#     "PyYAML>=6.0", "typing==3.7.4.3"
# ]
