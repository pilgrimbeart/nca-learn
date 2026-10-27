#!/bin/bash
# the tuned circuits with unequal thrusters (discrete/NOTEBOOK.md D5)
cd /home/pilgrim/git/nca-learn
P=.venv/bin/python
for m in 1.03 1.25; do
  for f in hold_drive_tuned straight_tuned hold12_tuned; do
    $P -m discrete.judge discrete/results/$f.json --motors $m > discrete/results/${f}_motors${m}_judged.log 2>&1
  done
done
