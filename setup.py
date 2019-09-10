import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kitools",
    version="0.0.2",
    author="Patrick Stout, Ryan Hafen, Sergey Feldman",
    author_email="pstout@prevagroup.com, rhafen@gmail.com, sergey@data-cowboys.com",
    license="Apache2",
    description="ki tools package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ki-tools/kitools-py",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=(
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers"
    ),
    install_requires=[
        "synapseclient>=1.9.2,<2.0.0",
        "beautifultable>=0.7.0,<1.0.0"
    ]
)
