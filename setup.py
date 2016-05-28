from setuptools import setup

setup(
    name="sst",
    version="0.1.0",
    author="Alex Zhang",
    author_email="superabee@gmail.com",
    description="Stop Signal Task Control",
    license="GPL3",
    url="https://github.com/superabe/stopsignaltask_arduino",

    packages=['sst'],
    entry_points={
        'console_scripts':['sst-gui=sst.sst_gui:main']
        },    
    platforms=['any'],
    )
