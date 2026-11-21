import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000
rng = np.random.default_rng(7)

def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    return e

def kick(dur=0.45):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(2.2 * np.sin(ph) * env(n, .001, .18))

def snare(dur=0.25):
    n = int(SR * dur)
    no = rng.standard_normal(n)
    no = sosfilt(butter(2, [1200, 7000], 'band', fs=SR, output='sos'), no)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return (0.8 * no * env(n, .001, .09) + 0.5 * body) * 0.7

def hat(dur=0.05, op=False):
    n = int(SR * (0.2 if op else dur))
    no = sosfilt(butter(2, 7000, 'high', fs=SR, output='sos'), rng.standard_normal(n))
    return no * env(n, .0005, .08 if op else .015) * 0.35

def sub808(freq, dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return np.tanh(1.8 * np.sin(2 * np.pi * freq * t)) * env(n, .003, dur * .7) * 0.55

def impact(dur=1.2):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 40 + 60 * np.exp(-t * 12)
    s = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 3.2)
    no = sosfilt(butter(2, 3000, 'low', fs=SR, output='sos'), rng.standard_normal(n)) * np.exp(-t * 18) * .6
    return (s + no) * 0.9

def whoosh(dur=0.45):
    n = int(SR * dur); t = np.arange(n) / SR
    no = rng.standard_normal(n); out = np.zeros(n)
    for i in range(0, n, 480):
        fc = 300 + 5000 * (i / n)
        seg = no[i:i + 480]
        out[i:i + 480] = sosfilt(butter(2, [fc, fc * 1.6], 'band', fs=SR, output='sos'), seg)
    return out * np.sin(np.pi * t / dur) ** 2 * 0.9

def riser(dur=1.4):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 200 * (2 ** (t / dur * 3))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    no = sosfilt(butter(2, 2000, 'high', fs=SR, output='sos'), rng.standard_normal(n)) * .25
    return (tone + no) * (t / dur) ** 2

def stamp():
    n = int(SR * .12); t = np.arange(n) / SR
    no = sosfilt(butter(2, [400, 2500], 'band', fs=SR, output='sos'), rng.standard_normal(n))
    return (no * np.exp(-t * 45) + np.sin(2 * np.pi * 110 * t) * np.exp(-t * 30)) * .7

def chime():
    n = int(SR * .9); t = np.arange(n) / SR
    a = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 4) * (t < .45)
    b = np.sin(2 * np.pi * 1318.5 * t) * np.exp(-np.maximum(0, t - .18) * 4) * (t >= .18)
    return (a + b) * .35

def put(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if i >= len(buf): return
    L = g * (1 - max(0, pan)); Rg = g * (1 + min(0, pan))
    buf[i:j, 0] += x[:j - i] * L; buf[i:j, 1] += x[:j - i] * Rg

def build(dur, drop, transitions, slams, cta, out, style='trap'):
    n = int(SR * dur); mus = np.zeros((n, 2)); sfx = np.zeros((n, 2))
    if style != 'trap':
        return build_alt(dur, drop, transitions, slams, cta, out, style)
    bpm = 140; beat = 60 / bpm
    notes = [43.65, 43.65, 51.91, 38.89]  # F1 F1 G#1 Eb1
    t = 0.0; b = 0
    while t < dur - .2:
        bar = int(b // 4) % 4; inbar = b % 4
        pre = t < drop
        if not pre or t > drop - 1.6:
            if inbar in (0,) or (inbar == 2 and b % 8 == 6): put(mus, kick(), t, .9)
            if inbar in (1, 3) and not pre: put(mus, snare(), t, .7)
        if not pre:
            for h in range(4 if b % 8 == 7 else 2):
                put(mus, hat(), t + h * beat / (4 if b % 8 == 7 else 2), .9, pan=.25)
            if inbar == 0: put(mus, sub808(notes[bar], beat * 3.5), t, 1.0)
        else:
            if inbar == 0: put(mus, sub808(notes[bar], beat * 3.8) * .5, t, .7)
            put(mus, hat() * .5, t + beat / 2, .6, pan=-.2)
        t += beat; b += 1
    # pad
    tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * tt + i) for i, f in enumerate([174.6, 207.7, 261.6, 311.1])) * 0.03
    pad *= np.minimum(1, tt / 1.0)
    mus[:, 0] += pad; mus[:, 1] += np.roll(pad, 240)
    for tr in transitions:
        put(sfx, riser(1.2), tr - 1.2, .7); put(sfx, whoosh(), tr - .15, .9, pan=.3); put(sfx, impact(), tr, 1.0)
    for s in slams: put(sfx, stamp(), s, .8)
    put(sfx, chime(), cta + .3, .9)
    # dip music briefly before drop
    i0, i1 = int((drop - .35) * SR), int(drop * SR)
    mus[i0:i1] *= 0.15
    mix = mus * 0.8 + sfx
    fade = np.minimum(1, (dur - tt) / 0.6)[:, None]
    mix *= fade
    mix /= max(1e-9, np.abs(mix).max()) / 0.8
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))


def pluck(f, dur=.35):
    n = int(SR * dur); t = np.arange(n) / SR
    s = sum(np.sin(2*np.pi*f*h*t)/h for h in (1,2,3))*np.exp(-t*9)
    return s*.25

def build_alt(dur, drop, transitions, slams, cta, out, style):
    n = int(SR * dur); mus = np.zeros((n, 2)); sfx = np.zeros((n, 2))
    bpm = 124 if style == 'house' else 130; beat = 60 / bpm; step = beat / 4
    chords = [[220,261.6,329.6],[174.6,220,261.6],[196,246.9,293.7],[164.8,196,246.9]]
    funk = [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0]   # tamborzão-like kick
    clap = [0,0,0,0, 1,0,0,1, 0,0,0,0, 1,0,1,0]
    i = 0; t = 0.0
    while t < dur - .2:
        pre = t < drop; s16 = i % 16; bar = (i // 16) % 4
        if style == 'house':
            if s16 % 4 == 0 and (not pre or t > drop - 1.6): put(mus, kick(.35), t, .85)
            if s16 % 4 == 2 and not pre: put(mus, hat(op=True), t, .7, pan=.2)
            if s16 in (4, 12) and not pre: put(mus, snare(), t, .5)
            if s16 in (0, 3, 6, 10): 
                for f in chords[bar]: put(mus, pluck(f), t, .6 if pre else .9, pan=-.15)
        else:
            if funk[s16] and (not pre or t > drop - 1.6): put(mus, kick(.3), t, .9)
            if clap[s16] and not pre: put(mus, snare(.18), t, .65)
            if s16 % 2 == 1 and not pre: put(mus, hat(), t, .6, pan=-.25)
            if s16 in (0, 8) : 
                for f in chords[bar]: put(mus, pluck(f*.5, .5), t, .5 if pre else .7)
            if s16 == 0 and not pre: put(mus, sub808(chords[bar][0]/4, beat*3), t, .9)
        t += step; i += 1
    for tr in transitions:
        put(sfx, riser(1.2), tr - 1.2, .7); put(sfx, whoosh(), tr - .15, .9, pan=-.3); put(sfx, impact(), tr, 1.0)
    for s in slams: put(sfx, stamp(), s, .8)
    put(sfx, chime(), cta + .3, .9)
    i0, i1 = int((drop - .35) * SR), int(drop * SR); mus[i0:i1] *= 0.15
    tt = np.arange(n) / SR
    mix = mus * 0.8 + sfx; mix *= np.minimum(1, (dur - tt) / 0.6)[:, None]
    mix /= max(1e-9, np.abs(mix).max()) / 0.8
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))

if __name__ == '__main__':
    cfg = {
        '1': dict(drop=5.6, transitions=[5.6, 9.2], slams=[0, .55, 1.1, 6.0, 9.65], cta=9.4),
        '2': dict(drop=5.8, transitions=[5.8, 9.2], slams=[0, 3.6, 6.2, 6.6, 9.65], cta=9.4),
        '3': dict(drop=5.6, transitions=[5.6, 9.2], slams=[0, 4.0, 6.0, 9.65], cta=9.4, style='house'),
        '4': dict(drop=5.6, transitions=[5.6, 9.2], slams=[0, 3.9, 6.0, 9.65], cta=9.4, style='funk'),
    }
    v = sys.argv[1]
    build(12.0, out=f'mix{v}.wav', **cfg[v])
