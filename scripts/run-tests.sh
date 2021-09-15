#!/bin/bash
export PYTHONPATH=$(pwd)
pytest test/test.py $@
