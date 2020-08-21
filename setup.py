import setuptools

with open('README') as f:
    long_description = f.read()

setuptools.setup(
    name="jtalkbot-mshibata",
    version="0.0.1",
    author="Masaaki Shibata",
    author_email="mshibata@emptypage.jp",
    description="A discord bot talking Japanese",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/emptypage/discordbot/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
