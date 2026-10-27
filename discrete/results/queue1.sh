#!/bin/bash
cd /home/pilgrim/git/nca-learn
P=.venv/bin/python
$P -m discrete.tune hold_drive 25 --start rt=2.36e8 ct=3.03e-10 rg1=1.69e8 rg2=3.23e7 rsh=1.19e8 rp=4.91e6 ch=5.1e-10 rf=3.06e7 > discrete/results/hold_drive_tune.log 2>&1
$P -m discrete.tune bare 25 --start rt=1.5e8 rf=3e8 ce=5e-10 > discrete/results/bare_tune.log 2>&1
$P -m discrete.tune straight 15 > discrete/results/straight_tune.log 2>&1
$P -m discrete.tune reflex_scan 15 > discrete/results/reflex_scan_tune.log 2>&1
