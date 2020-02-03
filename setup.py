from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='twitter-cli',
    version='0.2',
    author='Will Han',
    author_email='xingheng.hax@qq.com',
    license='MIT',
    keywords='twitter cli media downloader',
    url='https://github.com/xingheng/twitter-cli',
    description='twitter crawler',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['twitter_cli'],
    include_package_data=True,
    install_requires=[
        'coloredlogs>=10.0',
        'configparser>=4.0.2',
        'peewee>=3.11.2',
        'python-twitter>=3.5',
        'click>=7.0',
    ],
    entry_points='''
        [console_scripts]
        twitter-cli=twitter_cli.main:cli
    ''',
    classifiers=[
        'Development Status :: 1 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Unix Shell',
        'Topic :: System :: Shells',
        'Topic :: Terminals',
        'Topic :: Text Processing :: Linguistic',
      ],
)
