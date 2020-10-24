from setuptools import setup

with open("./README.md","r")as f:
    long_description = f.read()

setup(name='qsys',
        version=open("./VERSION","r").read(),
        description='Python QSYS QRC Wrapper',
        author='Gage Helton',
        author_email='gagehelton@gmail.com',
        url='https://github.com/mghelton/qsys',
        packages=['.'],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        long_description=long_description,
        long_description_content_type="text/markdown")
