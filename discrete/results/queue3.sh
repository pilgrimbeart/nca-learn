#!/bin/bash
# held-out judging of the tuned circuits (discrete/NOTEBOOK.md D4)
cd /home/pilgrim/git/nca-learn
P=.venv/bin/python
for f in hold_drive_tuned hold_drive_screened hold12_tuned straight_tuned counter10_tuned; do
  $P -m discrete.judge discrete/results/$f.json > discrete/results/${f}_judged.log 2>&1
done
