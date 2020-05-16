#!/bin/bash

export PYTHONPATH=$PYTHONPATH:../quickparse

poetry run pytest tests
