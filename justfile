default:
    @just --choose

active-env:
    @source venv/bin/activate

install:
    @pip install -e .

setup:
    @python setup.py install

help:
    @venv/bin/twitter-cli --help

timeline:
    @venv/bin/twitter-cli timeline --download-media

favorite:
    @venv/bin/twitter-cli favorites --download-media --destroy

list:
    @venv/bin/twitter-cli list --download-media

publish:
    rsync -avr --progress . gcp-vps:~/projects/twitter-cli/
