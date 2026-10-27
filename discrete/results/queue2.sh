#!/bin/bash
cd /home/pilgrim/git/nca-learn
P=.venv/bin/python
$P -m discrete.tune straight 15 > discrete/results/straight_tune.log 2>&1
$P -m discrete.tune hold12 20 > discrete/results/hold12_tune.log 2>&1
$P -m discrete.tune counter10 15 > discrete/results/counter10_tune.log 2>&1
$P -m discrete.tune hold_drive 20 --start rt=1.56e8 ct=3.04e-10 rg1=3.65e8 rg2=8.04e7 rsh=2.79e7 rp=7.77e6 ch=1.26e-9 rf=1e9 > discrete/results/hold_drive_tune.log 2>&1
