"""The discrete circuits tried (discrete/NOTEBOOK.md): each a function of a seed's parts (rng, for tolerances) and its
own values, returning a Netlist (discrete/life.py) on nodes vdd, s0, s1 (the eyes), m0, m1 (the motors) and ground."""

from __future__ import annotations

from discrete.life import SUPPLY, Netlist


def put_osc(n: Netlist, a, g, b, rt, ct, rg1, rg2, rsh):
    """A relaxation oscillator: a programmable-unijunction switch built of a PNP and an NPN. The timing capacitor (at
    a) charges through rt until it passes the gate (g, held by the divider rg1, rg2) by a diode drop; then the pair
    latches and dumps it into the NPN's base (b, shunted by rsh), and lets go once too little current is left to hold
    it (the timing current alone can't). Each discharge lifts b briefly: the oscillator's pulse."""
    n.R("vdd", a, rt)
    n.C(a, "0", ct)
    n.R("vdd", g, rg1)
    n.R(g, "0", rg2)
    n.Q("PNP", b, g, a)             # emitter at the capacitor, base at the gate, collector into the NPN's base
    n.Q("NPN", g, b, "0")           # collector pulls the gate down
    n.R(b, "0", rsh)


def hold_drive(rng=None, rt=100e6, ct=470e-12, rg1=150e6, rg2=75e6, rsh=30e6, rp=10e6, ch=1e-9, rh=0.0,
               rf=100e6):
    """Hold and drive, the policy's best kind (14 parts; 15 with a leak rh on the hold). Both eyes feed one emitter
    follower, whose emitter charges a hold capacitor (h) at each pulse, to a diode drop below the supply; it leaks
    back through rf to the oscillator's timing node, so it rests at that node's mean, below the motors' threshold. The oscillator always
    pulls motor A's pull-up low at each pulse (one thruster: a scanning turn); motor B's pull-up comes from h, so it
    fires too only while h is above the motor's threshold (both thrusters: straight ahead), and h, through rf, speeds
    the oscillator up meanwhile."""
    n = Netlist(rng)
    n.eye = ["e", "e"]
    n.Q("NPN", "vdd", "e", "h")
    n.C("h", "0", ch)
    if rh:
        n.R("h", "0", rh)
    put_osc(n, "a", "g", "b", rt, ct, rg1, rg2, rsh)
    n.R("h", "a", rf)
    n.Q("NPN", "m0", "b", "0")
    n.R("vdd", "m0", rp)
    n.Q("NPN", "m1", "b", "0")
    n.R("h", "m1", rp)
    return n


BOUNDS = {"r": (1e6, 1e9), "c": (47e-12, 30e-9)}   # where a tuner may take a value: 1 MOhm to 1 GOhm (no current
                                                    # wasted below, none common above), 47 pF to 30 nF




def straight(rng=None, rt=100e6, ct=470e-12, rg1=150e6, rg2=75e6, rsh=30e6, rp=10e6):
    """Blind straight, the baseline (9 parts): the oscillator pulls one pull-up low at each pulse, and both motors read
    that node (a wire), so both thrusters fire together: straight ahead at a steady rate, the eyes unwired."""
    n = Netlist(rng)
    n.motor = ["m", "m"]
    put_osc(n, "a", "g", "b", rt, ct, rg1, rg2, rsh)
    n.Q("NPN", "m", "b", "0")
    n.R("vdd", "m", rp)
    return n


def reflex_scan(rng=None, rt=100e6, ct=470e-12, rg1=150e6, rg2=75e6, rsh=30e6, rp=10e6, re=10e6, rb=300e6):
    """Reflex and scan (11 parts): the oscillator fires motor A (scanning); both eyes feed motor B's node directly,
    with a leak, so each pulse fires motor B, and through rb the pulse also turns on motor A's NPN, firing it too."""
    n = Netlist(rng)
    n.eye = ["m1", "m1"]
    put_osc(n, "a", "g", "b", rt, ct, rg1, rg2, rsh)
    n.Q("NPN", "m0", "b", "0")
    n.R("vdd", "m0", rp)
    n.R("m1", "0", re)
    n.R("m1", "b", rb)
    return n


def hold12(rng=None, rt=1.56e8, ct=3.04e-10, rg1=3.65e8, rg2=8.04e7, rsh=2.79e7, rp=7.77e6, ch=1.26e-9, rb=7.77e6):
    """Hold and drive pared to 12 parts (the ladder's third rung, discrete/NOTEBOOK.md D4): both eyes charge the hold
    capacitor directly (no follower), and the hold has no leak of its own: motor B's pull-up comes from it, so each of
    motor B's firings (its NPN pulling the pull-up low at a beat) takes a little of its charge, and the hold drains by
    driving. The oscillator and motor A as in hold_drive."""
    n = Netlist(rng)
    n.eye = ["h", "h"]
    put_osc(n, "a", "g", "b", rt, ct, rg1, rg2, rsh)
    n.Q("NPN", "m0", "b", "0")
    n.R("vdd", "m0", rp)
    n.C("h", "0", ch)
    n.Q("NPN", "m1", "b", "0")
    n.R("h", "m1", rb)
    return n


def counter10(rng=None, rt=1.76e8, ct=7.75e-10, rg1=1.22e8, rg2=3.83e7, rp=6.16e6, rb=6.16e6):
    """Counter-turning, 10 parts (the ladder's last rung): the oscillator without its base shunt (the two motor NPNs'
    bases take its current) fires motor A, scanning; motor B's pull-up comes straight from the eyes, so each pulse fires
    motor B, whose turn cancels motor A's while a block is in view; motor B's NPN also pulls it low at each beat."""
    n = Netlist(rng)
    n.eye = ["e", "e"]
    n.R("vdd", "a", rt)
    n.C("a", "0", ct)
    n.R("vdd", "g", rg1)
    n.R("g", "0", rg2)
    n.Q("PNP", "b", "g", "a")
    n.Q("NPN", "g", "b", "0")
    n.Q("NPN", "m0", "b", "0")
    n.R("vdd", "m0", rp)
    n.Q("NPN", "m1", "b", "0")
    n.R("e", "m1", rb)
    return n


CIRCUITS = {k: (globals()[k], SUPPLY) for k in ("hold_drive", "hold12", "counter10", "straight", "reflex_scan")}


def toggle_latch(n: Netlist, w, rl=200e6, rx=200e6, rs=1e9, ct=200e-12):
    """A latch of two NPNs, collectors c0 and c1, each base fed from the other's collector (rx): one on, its collector
    low, the other's high. A falling edge at w turns off whichever is on: its steering junction (j, resting at its own
    collector through rs) is low, so the edge passes its diode into its base; the other's rests high and blocks it.
    The edge holds the base down for about rs x ct, while the other side takes over. (Speed-up capacitors across rx
    made it flip at any disturbance of a collector.)"""
    for c, b, other, j in (("c0", "b0", "c1", "j0"), ("c1", "b1", "c0", "j1")):
        n.Q("NPN", c, b, "0")
        n.R("vdd", c, rl)
        n.R(other, b, rx)
        n.R(c, j, rs)
        n.D(b, j)
        n.C(w, j, ct)


def learn_hold(rng=None, rt=2.17e8, ct=3.05e-10, rg1=2.11e8, rg2=4.32e7, rsh=4.99e7, rp=9.77e6, ch=4.63e-10,
               rb=1.28e7, rr=0.0, rl=5e8, rx=1e9, cs=200e-12, rk=1e8, cq=3e-9, rq=1e9, rq1=1e9, rw1=1e9,
               rw=1e8, darlington=True, roam=True, rt2=1e9, ct2=5e-9, rg3=3e8, rg4=1e8, rsh2=4e8, rbe=5e7, rbg=2e8, rz1=0.0,
               rz2=1e8, sink="0"):
    """Hold and drive with one bit learned (discrete/NOTEBOOK.md D6): hold12 (the oscillator, motor A scanning, motor
    B's pull-up from the hold, which drains by driving), with
    - a roam: a second, slow oscillator (put_osc, a few seconds a beat) whose discharge pulls its gate (g2) low, which
      turns on a PNP from the supply into the hold (its base held off by the divider rbe, rbg from the supply to g2): a
      phantom pulse, so both thrusters drive for a while; and while the hold is above about 2 V (the divider rz1,
      rz2 into an NPN's base), that NPN empties the slow oscillator's timing capacitor, so a roam comes only after a
      few seconds with nothing seen (a free-running roam, every 2 s whatever is seen, was half as good as policies;
      rz1 0: none). (rr, a resistor from the
      supply into the hold instead, has no hysteresis: too weak, it never starts a roam; strong enough to, it drives
      without pause, blind, into poison.)
    - each eye's node (s0, s1) charging the hold through a diode, and shorted to ground by a shunt NPN while the
      toggle latch (toggle_latch) feeds that shunt's base (rk from collector c0 or c1): only the eye the latch leaves
      free can start an approach. (Eyes on the latch's own collectors flipped it at every pulse of the shorted eye: its
      nanoamp base couldn't take the eye's microamp before the cross-coupling did.)
    - doubt on the taste node q (cq, recovering through rq towards the supply over a second or so, and lifted by food):
      each poison pulls it down by about 0.8 V, so the second in quick succession takes it below the threshold
      transistor's base; it lets go, the second transistor turns on, and w falls: the latch flips, and the other
      colour is followed.
    sink: where the shunts' emitters go (learn_avoid uses the current they sink)."""
    n = hold12(rng, rt, ct, rg1, rg2, rsh, rp, ch, rb)
    n.eye = ["s0", "s1"]
    for s, c in (("s0", "c0"), ("s1", "c1")):
        n.D(s, "h")
        n.Q("NPN", s, s + "b", sink)
        if darlington:                                  # (a second NPN feeding the shunt's base: a hundredth of
            n.Q("NPN", s, s + "d", s + "b")             # the latch's current can then sink an eye)
            n.R(c, s + "d", rk)
        else:
            n.R(c, s + "b", rk)
    if rr:
        n.R("vdd", "h", rr)
    if roam:
        put_osc(n, "a2", "g2", "b2", rt2, ct2, rg3, rg4, rsh2)
        n.R("vdd", "rbase", rbe)
        n.R("rbase", "g2", rbg)
        n.Q("PNP", "h", "rbase", "vdd")
        if rz1:
            n.R("h", "zb", rz1)
            n.R("zb", "0", rz2)
            n.Q("NPN", "a2", "zb", "0")
    n.taste = "q"
    n.C("q", "0", cq)
    n.R("vdd", "q", rq)
    n.R("q", "qb", rq1)
    n.Q("NPN", "w1", "qb", "0")
    n.R("vdd", "w1", rw1)
    n.Q("NPN", "w", "w1", "0")
    n.R("vdd", "w", rw)
    toggle_latch(n, "w", rl, rx, ct=cs)
    return n


CIRCUITS["learn_hold"] = (learn_hold, SUPPLY)


def learn_avoid(rng=None, cu=1e-8, ru=1e9, rd=1e6, **kw):
    """One bit learned, giving up on an empty patch and turning from poison ahead (46 parts; discrete/NOTEBOOK.md D8,
    D9): learn_hold without its roam oscillator, and
    - giving up: each eye's node lifts a slow node u through a follower (only the eye the latch leaves free reaches
      it: the other is shunted), and u sags through ru; u is a PNP's base, the PNP's emitter at the supply, so once it
      has been a few seconds since the free eye saw anything, u has sagged until the PNP's own base current balances
      ru's leak, and the PNP feeds the hold from the supply: both thrusters drive straight until the next sighting
      lifts u (a creature that has eaten its patch clear of food leaves it, instead of circling among the poison);
    - avoiding: the shunts' emitters go to k (rd to ground), so the silenced eye's current, sunk by its shunt, turns
      on an NPN that empties the hold: poison ahead cuts motor B, and the creature turns off its line instead of
      driving through it (it had only declined to approach poison, never avoided it).
    (Pruned from 48 parts: a divider on the PNP's base, from the supply to u, wasn't needed.)"""
    n = learn_hold(rng, roam=False, sink="k", **kw)
    for s in ("s0", "s1"):
        n.Q("NPN", "vdd", s, "u")
    n.C("u", "0", cu)
    n.R("u", "0", ru)
    n.Q("PNP", "h", "u", "vdd")
    n.R("k", "0", rd)
    n.Q("NPN", "h", "k", "0")
    return n


CIRCUITS["learn_avoid"] = (learn_avoid, SUPPLY)
