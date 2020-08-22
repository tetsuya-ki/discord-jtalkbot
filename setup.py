import setuptools


with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='jtalkbot-mshibata',
    version='0.1.0',
    author='Masaaki Shibata',
    author_email='mshibata@emptypage.jp',
    description='A discord bot talking Japanese.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://bitbucket.org/emptypage/jtalkbot/',
    packages=setuptools.find_packages(),
    package_data={
        'jtalkbot': ['jtalkbot-config.sample.json']
    },
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords='discord',
    install_requires=['discord.py'],
    entry_points={
        'console_scripts': [
            'jtalkbot=jtalkbot:main'
        ]
    }
)
