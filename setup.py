import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="twitscan",
    version="0.0.1",
    author="Monkey Usage",
    author_email="monkeyusage@gmail.com",
    description="A wrapper package around tweepy. Scans user data, stores it in a database and analyses relationships",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/monkeyusage/twitscan",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
