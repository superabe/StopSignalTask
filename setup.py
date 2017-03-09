from setuptools import setup, find_packages

setup(
    name="sst",
    version="1.0.0",
    author="Alex Zhang",
    author_email="superabee@gmail.com",
    description="Stop Signal Task Control",
    license="GPL3",
    url="https://github.com/superabe/stopsignaltask_arduino",

    packages=find_packages(),
    package_data={'sst.resources':['*']}, 
    entry_points={
        'console_scripts':['sst-gui=sst.sst_gui:main']
        },    
    platforms=['any'],
    )
