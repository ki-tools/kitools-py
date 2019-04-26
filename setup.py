import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kitools",
    version="0.0b13",
    author="Patrick Stout",
    author_email="pstout@prevagroup.com",
    license="Apache2",
    description="ki tools package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ki-tools/kitools-py",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=(
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ),
    install_requires=[
        'synapseclient==1.9.2',
        'beautifultable==0.7.0'
    ]
)
