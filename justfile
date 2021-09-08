
default:
    @just --choose

active-env:
    @pipenv shell

install:
    @pipenv install -e .
    # pipenv run pip install -e .

# setup:
#     @python setup.py install

cli *options:
    @pipenv run twitter-cli {{options}}
    @#@$(pipenv --venv)/bin/twitter-cli {{options}}  # works good, too.

help:
    @just cli --help

timeline:
    @just cli timeline --download-media

favorite:
    @just cli favorites --download-media --destroy

list:
    @just cli list --download-media

publish:
    rsync -avr --progress . gcp-vps:~/projects/twitter-cli/

cleanup:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
