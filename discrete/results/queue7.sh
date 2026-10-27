#!/bin/bash
# with ngspice's error control tightened (discrete/NOTEBOOK.md D7): every circuit judged held out again, then each
# re-tuned from its current values (the earlier values kept in results/coarse_default_tol/)
cd /home/pilgrim/git/nca-learn
P=.venv/bin/python
R=discrete/results
for f in hold_drive_screened hold12_tuned straight_tuned counter10_tuned; do
  $P -m discrete.judge $R/$f.json > $R/${f}_judged.log 2>&1
done
$P -m discrete.judge $R/hold_drive_tuned.json > $R/hold_drive_tuned_judged.log 2>&1
start() { $P -c "import json; print(' '.join(f'{k}={v:.4g}' for k, v in json.load(open('$1'))['best'].items()))"; }
$P -m discrete.tune learn_hold 10 --poison --seeds 16 --lam 8 --only cq rq ct2 rsh2 rb ch rt rp \
  > $R/learn_hold_tune.log 2>&1
for c in hold_drive hold12 straight counter10; do
  $P -m discrete.tune $c 10 --seeds 12 --lam 8 --start $(start $R/coarse_default_tol/${c}_tuned.json) > $R/${c}_tune.log 2>&1
done
