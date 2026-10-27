#!/bin/bash
# tuning the 49-part learning circuit with poison (discrete/NOTEBOOK.md D6)
cd /home/pilgrim/git/nca-learn
.venv/bin/python -m discrete.tune learn_hold 8 --poison --lam 8 --only cq rq ct2 rsh2 rb ch rt rp > discrete/results/learn_hold_tune.log 2>&1
