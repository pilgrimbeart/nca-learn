#!/bin/bash
# tuning the learning circuit with poison (discrete/NOTEBOOK.md D6)
cd /home/pilgrim/git/nca-learn
.venv/bin/python -m discrete.tune learn_hold 12 --poison --only cq rq ct2 rsh2 rg4 rl rx rk ch rb rt2 > discrete/results/learn_hold_tune.log 2>&1
