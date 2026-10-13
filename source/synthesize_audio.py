#!/usr/bin/env python3
# Modified 2026-10-13: public source packaging and documentation; image/audio generation unchanged.
"""SPDX-License-Identifier: GPL-3.0-only

The Surplus: original deterministic 84-second Snowmoon soundtrack.

Numpy, scipy, and the standard library only. No recordings, external samples,
voices, downloads, or external synthesis packages. All stems sum at unity.
The refined proof's original synthesis is preserved below as a self-contained
reference generator, with small hooks to retain its raw note/foley components.
The final eight shoe events reuse those procedural components, without the old
excerpt's 78-second cut fade. All outputs are local to this production's audio/.

Run: python source/synthesize_audio.py
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy import signal, optimize
from scipy.io import wavfile

RATE = 48_000
DURATION = 84.0
N = int(RATE * DURATION)
RNG = np.random.default_rng(66782026)
OUT = Path(__file__).resolve().parents[1] / 'audio'
OUT.mkdir(parents=True, exist_ok=True)


def band_noise(n, low, high):
    raw = RNG.normal(size=n)
    sos = signal.butter(3, [low, high], fs=RATE, btype='bandpass', output='sos')
    y = signal.sosfiltfilt(sos, raw)
    return y / max(np.sqrt(np.mean(y*y)), 1e-12)


def ease(x):
    x = np.clip(x, 0.0, 1.0)
    return x*x*(3.0-2.0*x)


def pan_mono(x, p):
    angle = (np.asarray(p)+1) * np.pi / 4
    return np.column_stack((x*np.cos(angle), x*np.sin(angle)))


def add_at(stem, x, start):
    i = int(round(start * RATE))
    a, b = max(i, 0), min(i+len(x), len(stem))
    if b > a:
        stem[a:b] += x[a-i:b-i]


def stats(x):
    peak = float(np.max(np.abs(x)))
    # Overlapped ten-second chunks avoid a 4x full-film temporary array.
    # The overlap exceeds scipy's polyphase FIR support by a wide margin.
    reconstructed_peak = 0.0
    block = 10*RATE
    for a in range(0, len(x), block):
        b = min(a+block, len(x))
        lo, hi = max(0, a-64), min(len(x), b+64)
        up = signal.resample_poly(x[lo:hi], 4, 1, axis=0)
        valid = up[(a-lo)*4:(b-lo)*4]
        reconstructed_peak = max(reconstructed_peak, float(np.max(np.abs(valid))))
    rms = float(np.sqrt(np.einsum('ij,ij->', x.astype(np.float64), x.astype(np.float64))/x.size))
    return {
        'duration_seconds': len(x)/RATE,
        'frames': len(x), 'sample_rate_hz': RATE, 'channels': 2,
        'peak_dbfs': round(20*np.log10(max(peak, 1e-12)), 3),
        'estimated_true_peak_4x_dbfs': round(20*np.log10(max(reconstructed_peak, 1e-12)), 3),
        'rms_dbfs': round(20*np.log10(max(rms, 1e-12)), 3),
    }


def build_proof_reference():
    """Recreate the approved proof's synthesis stream without touching its files."""
    global RNG
    RNG = np.random.default_rng(66782026)
    DURATION = 12.0
    N = int(RATE * DURATION)
    T = np.arange(N, dtype=np.float64) / RATE
    # A non-tonal exterior air bed. Independent air in both ears surrounds a
    # low-level center texture. Slow asymmetrical envelopes avoid synthetic looping.
    ambience = np.zeros((N, 2))
    shared_air = band_noise(N, 140, 1750)
    low_air = band_noise(N, 55, 240)
    gust = 0.65 + 0.28*np.exp(-((T-2.6)/2.2)**2) + 0.18*np.exp(-((T-8.7)/1.5)**2)
    gust *= 1 + 0.035*np.sin(2*np.pi*0.37*T + 1.4)
    for channel, phase in enumerate([0.0, 1.7]):
        wide_air = band_noise(N, 400, 5400)
        airy_gust = 0.72 + 0.2*np.sin(2*np.pi*0.075*T+phase)**2
        ambience[:, channel] = (
            0.0061*shared_air*gust +
            0.0036*wide_air*airy_gust +
            0.0034*low_air*(0.8+0.1*np.sin(2*np.pi*0.14*T))
        )

    # Extremely distant rotor: stochastic, band-limited turbulent energy, gently
    # fluttering rather than a persistent periodic pitched/electrical drone.
    rotor = band_noise(N, 95, 640)
    rotor_phase = 2*np.pi*(17.5*T + 0.035*T*T + 0.07*np.sin(2*np.pi*0.16*T))
    rotor *= (0.56 + 0.29*np.sin(rotor_phase) + 0.15*np.sin(2*rotor_phase+0.7))
    rotor *= 0.0022 * (0.45+0.55*np.exp(-((T-2.2)/2.5)**2)) * (1-ease((T-5.0)/2.0))
    ambience += pan_mono(rotor, -0.52+0.22*T/DURATION)

    # A broad unpitched distant street wash passes gently at 6.3 seconds.
    street = band_noise(N, 180, 1250) * 0.0024*np.exp(-((T-6.3)/2.7)**2)
    ambience += pan_mono(street, 0.6-0.75*T/DURATION)
    # Tiny edit-safe boundaries; the ambience otherwise continues through the scene.
    ambience_unedged = ambience.copy()
    ambience *= (ease(T/0.055)*(1-ease((T-(DURATION-0.07))/0.07)))[:, None]

    music = np.zeros((N, 2))
    wood_notes = []
    # Three distinct plucked, wood-like resonances are already in decay at the
    # excerpt's opening. No new note is struck after the scene starts.
    for frequency, start, level, position in [
        (164.813778, -1.12, 0.034, -0.22),
        (246.941651, -0.63, 0.024, 0.17),
        (369.994423, -0.28, 0.016, -0.05),
    ]:
        age = T-start
        note = np.zeros(N)
        partial_phases = []
        # Gentle inharmonicity and faster high-partial loss produce a short, rounded
        # pluck tail rather than an organ or sine-wave hum.
        for harmonic in range(1, 7):
            inharmonic = 1 + 0.0008*(harmonic-1)**2
            decay = (1.18+0.18*(164.8/frequency)) / harmonic**0.55
            phase = RNG.uniform(-np.pi, np.pi)
            partial_phases.append(float(phase))
            note += (1/harmonic**1.9)*np.exp(-age/decay)*np.sin(
                2*np.pi*frequency*harmonic*inharmonic*age + phase)
        wood_notes.append((frequency, start, level, position, partial_phases))
        note *= level
        music += pan_mono(note, position)
    # The admission begins at film t=70s, excerpt t=4s. Exact digital silence from
    # t=4 onward, with a smooth 1.45-second preceding fade and no reverb crossing it.
    music *= (1-ease((T-2.55)/1.45))[:, None]
    music[T >= 4.0] = 0.0
    # In the preceding complete film this would connect to the existing note tail.
    # A 4ms clip-boundary ramp avoids a discontinuity in a standalone WAV.
    music *= ease(T/0.004)[:, None]

    # Foley: clothes settling during shoulder release, then quiet weighty shoe
    # contacts and very fine grit. Everything is generated from noise and resonators.
    effects = np.zeros((N, 2))
    cloth_len = int(0.70*RATE)
    ct = np.arange(cloth_len)/RATE
    cloth_env = (
        0.7*np.exp(-((ct-0.16)/0.095)**2) +
        0.46*np.exp(-((ct-0.32)/0.085)**2) +
        0.22*np.exp(-((ct-0.43)/0.065)**2)
    )
    cloth = (0.008*band_noise(cloth_len, 480, 4300) +
             0.003*band_noise(cloth_len, 120, 680)) * cloth_env
    cloth *= ease(ct/0.035)*(1-ease((ct-0.52)/0.18))
    add_at(effects, pan_mono(cloth, -0.08), 8.59)

    # Keep the original cue and synthesis stream as a mastering reference, so the
    # revision does not change a single sample of the ambience or music stems.
    cloth_reference = cloth.copy()
    legacy_effects = effects.copy()
    legacy_foot_times = [10.20, 10.71, 11.23, 11.76]
    foot_times = [10.20, 10.72, 11.24, 11.76]
    zei_foot_times = [10.34, 10.86, 11.38, 11.90]
    bai_positions = [-0.34, -0.26, -0.33, -0.25]
    zei_positions = [0.29, 0.35, 0.28, 0.34]
    bai_shoes = []
    zei_shoes = []
    bai_foley = np.zeros((N, 2))
    zei_foley = np.zeros((N, 2))
    for step, (start, position, strength) in enumerate(zip(
            foot_times, [-0.13, 0.15, -0.12, 0.12], [0.90, 1.0, 0.87, 0.92])):
        length = int(0.31*RATE)
        ft = np.arange(length)/RATE
        # Sole landing has no sharp click. A short non-tonal low thud and
        # independently randomized grit follow an eased 7ms contact.
        impact = band_noise(length, 60, 330)
        impact *= ease(ft/0.007)*np.exp(-ft/0.033)
        crunch = band_noise(length, 700, 5600)
        crunch_env = ease(ft/0.015)*np.exp(-ft/0.048)
        # Irregular grain-scale pressure impulses, all beneath the main contact.
        irregular = np.zeros(length)
        for offset, amp in zip(RNG.uniform(0.025, 0.145, 9), RNG.uniform(0.15, 0.7, 9)):
            irregular += amp*np.exp(-((ft-offset)/RNG.uniform(0.002, 0.008))**2)
        crunch *= crunch_env*(0.6+0.3*irregular)
        shoe = 0.085*impact + 0.035*crunch
        shoe += 0.008*band_noise(length, 300, 2200)*np.exp(-((ft-0.115)/0.065)**2)
        shoe *= strength * (1-ease((ft-0.24)/0.07))
        bai_shoes.append(shoe.copy())
        add_at(legacy_effects, pan_mono(shoe, position), legacy_foot_times[step])
        add_at(bai_foley, pan_mono(shoe, bai_positions[step]), start)

    # Zei follows Bai with a naturally staggered gait rather than an even rapid
    # pulse: 140ms between partners, then 380ms before Bai's next contact. His sole
    # has a softer, lower-frequency body and a little longer pressure release.
    # Independent, deterministic noise and varied strengths keep each contact
    # distinct, without a hard click, exaggerated crunch, or repeated sound sample.
    for start, position, strength in zip(
            zei_foot_times, zei_positions, [0.62, 0.69, 0.61, 0.65]):
        length = int(0.36*RATE)
        ft = np.arange(length)/RATE
        impact = band_noise(length, 46, 240)
        impact *= ease(ft/0.009)*np.exp(-ft/0.044)
        crunch = band_noise(length, 440, 3500)
        irregular = np.zeros(length)
        for offset, amp in zip(RNG.uniform(0.03, 0.17, 7), RNG.uniform(0.13, 0.58, 7)):
            irregular += amp*np.exp(-((ft-offset)/RNG.uniform(0.003, 0.01))**2)
        crunch *= ease(ft/0.020)*np.exp(-ft/0.060)*(0.64+0.26*irregular)
        shoe = 0.070*impact + 0.018*crunch
        shoe += 0.005*band_noise(length, 220, 1550)*np.exp(-((ft-0.135)/0.070)**2)
        shoe *= strength * (1-ease((ft-0.27)/0.09))
        zei_shoes.append(shoe.copy())
        add_at(zei_foley, pan_mono(shoe, position), start)
    effects += bai_foley + zei_foley
    # Final contact naturally finishes beyond the cut; a very short fade prevents
    # an edit click at the excerpt boundary.
    end_fade = (1-ease((T-11.97)/0.03))[:, None]
    effects *= end_fade
    legacy_effects *= end_fade
    bai_foley *= end_fade
    zei_foley *= end_fade

    stems = {'ambience': ambience, 'effects': effects, 'music': music}
    mix = sum(stems.values())
    # Preserve the exact first-version common mastering gain. The reference is
    # synthesized locally and deterministically; no backup or external asset is
    # required to regenerate this revision. Bed, music, and the 8.8s cloth cue stay
    # sample-identical, while only walking foley changes.
    target_peak = 10**(-9.0/20)
    reference_mix = ambience + legacy_effects + music
    gain = min(2.4, target_peak/max(np.max(np.abs(reference_mix)), 1e-12))
    for name in stems:
        stems[name] *= gain
    mix = sum(stems.values())
    assert len(mix) == 576000 and mix.shape == (576000, 2)
    assert np.isfinite(mix).all()
    assert np.max(np.abs(mix)) < 10**(-3/20)
    assert np.all(stems['music'][4*RATE:] == 0.0)


    return {
        'gain': gain, 'stems': stems, 'mix': mix,
        'ambience_unedged': ambience_unedged,
        'wood_notes': wood_notes, 'cloth': cloth_reference,
        'bai_shoes': bai_shoes, 'zei_shoes': zei_shoes,
        'bai_positions': bai_positions, 'zei_positions': zei_positions,
    }


def synthesize_shoe(character, strength):
    """Fresh noise per contact, using the refined proof's two sole recipes."""
    if character == 'Bai':
        length = int(0.31*RATE)
        ft = np.arange(length)/RATE
        impact = band_noise(length, 60, 330)
        impact *= ease(ft/0.007)*np.exp(-ft/0.033)
        crunch = band_noise(length, 700, 5600)
        irregular = np.zeros(length)
        for offset, amp in zip(RNG.uniform(0.025, 0.145, 9), RNG.uniform(0.15, 0.7, 9)):
            irregular += amp*np.exp(-((ft-offset)/RNG.uniform(0.002, 0.008))**2)
        crunch *= ease(ft/0.015)*np.exp(-ft/0.048)*(0.6+0.3*irregular)
        shoe = 0.085*impact + 0.035*crunch
        shoe += 0.008*band_noise(length, 300, 2200)*np.exp(-((ft-0.115)/0.065)**2)
        shoe *= strength*(1-ease((ft-0.24)/0.07))
        # A conservative event gain, not a nonlinear clip or limiter.
        shoe *= min(1.0, 0.130/max(np.max(np.abs(shoe)), 1e-12))
    else:
        length = int(0.36*RATE)
        ft = np.arange(length)/RATE
        impact = band_noise(length, 46, 240)
        impact *= ease(ft/0.009)*np.exp(-ft/0.044)
        crunch = band_noise(length, 440, 3500)
        irregular = np.zeros(length)
        for offset, amp in zip(RNG.uniform(0.03, 0.17, 7), RNG.uniform(0.13, 0.58, 7)):
            irregular += amp*np.exp(-((ft-offset)/RNG.uniform(0.003, 0.01))**2)
        crunch *= ease(ft/0.020)*np.exp(-ft/0.060)*(0.64+0.26*irregular)
        shoe = 0.070*impact + 0.018*crunch
        shoe += 0.005*band_noise(length, 220, 1550)*np.exp(-((ft-0.135)/0.070)**2)
        shoe *= strength*(1-ease((ft-0.27)/0.09))
        shoe *= min(1.0, 0.078/max(np.max(np.abs(shoe)), 1e-12))
    return shoe


def wood_note(frequency, level, phases, duration=9.0):
    age = np.arange(int(duration*RATE))/RATE
    note = np.zeros(len(age))
    for harmonic, phase in enumerate(phases, 1):
        inharmonic = 1 + 0.0008*(harmonic-1)**2
        decay = (1.18+0.18*(164.8/frequency)) / harmonic**0.55
        note += (1/harmonic**1.9)*np.exp(-age/decay)*np.sin(
            2*np.pi*frequency*harmonic*inharmonic*age+phase)
    # Rounded onset and an inaudible smooth tail. There is no reverb send.
    note *= level*ease(age/0.016)*(1-ease((age-(duration-0.8))/0.8))
    return note


def first_contact(t):
    return 0.20+0.14*(1-float(ease((t-23.0)/5.0)))


def main():
    global RNG
    proof = build_proof_reference()
    gain = proof['gain']
    RNG = np.random.default_rng(8420261013)
    T = np.arange(N, dtype=np.float64)/RATE
    ambience = np.zeros((N, 2))
    shared_air = band_noise(N, 140, 1750)
    low_air = band_noise(N, 55, 240)
    gust = (0.68 + 0.15*np.sin(2*np.pi*0.031*T+0.8)**2
            + 0.13*np.exp(-((T-39.5)/7.0)**2)
            + 0.10*np.exp(-((T-60.8)/5.2)**2))
    gust *= 1+0.035*np.sin(2*np.pi*0.37*T+1.4)
    for channel, phase in enumerate([0.0, 1.7]):
        wide_air = band_noise(N, 400, 5400)
        airy_gust = 0.72+0.2*np.sin(2*np.pi*0.075*T+phase)**2
        ambience[:, channel] = (0.0061*shared_air*gust
            + 0.0036*wide_air*airy_gust
            + 0.0034*low_air*(0.8+0.1*np.sin(2*np.pi*0.14*T)))
    del shared_air, low_air, wide_air, gust

    # A distant rotor is most noticeable in the 41–49-second interval.
    # Turbulent filtered noise with flutter remains unpitched and restrained.
    rotor = band_noise(N, 95, 640)
    rotor_phase = 2*np.pi*(17.5*T+0.002*T*T+0.07*np.sin(2*np.pi*0.16*T))
    rotor *= 0.56+0.29*np.sin(rotor_phase)+0.15*np.sin(2*rotor_phase+0.7)
    rotor_window = ease((T-41.0)/1.9)*(1-ease((T-46.4)/2.6))
    rotor *= 0.0054*rotor_window
    rotor_pan = -0.46+0.70*np.clip((T-41.0)/8.0, 0, 1)
    ambience += pan_mono(rotor, rotor_pan)
    del rotor, rotor_phase, rotor_window, rotor_pan
    street = band_noise(N, 180, 1250)
    street *= (0.0012*np.exp(-((T-16.0)/5.2)**2)
               + 0.0018*np.exp(-((T-38.0)/4.9)**2)
               + 0.0013*np.exp(-((T-57.0)/5.6)**2)
               + 0.0016*np.exp(-((T-80.0)/3.2)**2))
    ambience += pan_mono(street, 0.36*np.sin(2*np.pi*T/47.0+0.8))
    del street

    # Connect the approved atmosphere seamlessly to the longer film. A half-
    # second S-curve at each edge retains the exact proof ambience 66.5–77.5s.
    a, b = 66*RATE, 78*RATE
    local_t = np.arange(b-a)/RATE
    reference_window = ease(local_t/0.5)*(1-ease((local_t-11.5)/0.5))
    ambience[a:b] = (ambience[a:b]*(1-reference_window[:, None])
                    + proof['ambience_unedged']*reference_window[:, None])
    ambience *= (ease(T/0.055)*(1-ease((T-82.8)/1.2)))[:, None]

    music = np.zeros((N, 2))
    music_events = []
    # Start dry. The first phrase is only two answering notes.
    notes = [
        (23.05, 164.813778, 0.0130, -0.22, 'first answering note'),
        (24.45, 246.941651, 0.0100,  0.17, 'second answering note'),
        (49.10, 164.813778, 0.0140, -0.22, 'sparse overlapping motif'),
        (50.24, 246.941651, 0.0105,  0.17, 'sparse overlapping motif'),
        (51.51, 369.994423, 0.0075, -0.05, 'sparse overlapping motif'),
        (79.70, 164.813778, 0.0100, -0.17, 'soft resolution lead-in'),
        (80.40, 246.941651, 0.0075,  0.15, 'soft resolution'),
        (81.28, 329.627557, 0.0050, -0.03, 'soft resolution'),
    ]
    for start, frequency, level, position, label in notes:
        phases = RNG.uniform(-np.pi, np.pi, 6)
        note = wood_note(frequency, level, phases)
        add_at(music, pan_mono(note, position), start)
        music_events.append({'onset_seconds': start, 'frequency_hz': frequency,
                             'pan': position, 'cue': label})
    # Identical partial phases and decay recipes extend the approved opening
    # tails backwards to their original attacks in the full timeline.
    for frequency, proof_start, level, position, phases in proof['wood_notes']:
        start = 66.0+proof_start
        note = wood_note(frequency, level, phases)
        add_at(music, pan_mono(note, position), start)
        music_events.append({'onset_seconds': round(start, 6),
                             'frequency_hz': frequency, 'pan': position,
                             'cue': 'approved proof motif before the admission'})
    music[:70*RATE] *= (1-ease((T[:70*RATE]-68.55)/1.45))[:, None]
    silence_a, silence_b = 70*RATE, int(round(79.7*RATE))
    music[silence_a:silence_b] = 0.0
    music *= (1-ease((T-82.45)/1.55))[:, None]

    effects = np.zeros((N, 2))
    opening_bai = [round(0.20+0.52*k, 8) for k in range(63)]
    opening_zei = []
    for k in range(63):
        # This is both alternating-side equations interleaved. For k even,
        # side=0; for k odd, side=1. Their side equation is an integer.
        rhs = 0.52*k
        t = optimize.brentq(lambda t: t-first_contact(t)-rhs,
                            rhs+0.199999, rhs+0.340001, xtol=1e-13)
        opening_zei.append(float(t))
        side = k % 2
        phase = (t-first_contact(t))/1.04+side*0.5
        assert abs(phase-round(phase)) < 1e-10
    opening_pans = {'Bai': [], 'Zei': []}
    for character, times in [('Bai', opening_bai), ('Zei', opening_zei)]:
        for k, start in enumerate(times):
            strength = (0.86 if character == 'Bai' else 0.64)
            strength *= 1+0.075*np.sin(0.91*k+0.4)+RNG.uniform(-0.025, 0.025)
            center = -0.30 if character == 'Bai' else 0.315
            position = center+0.037*(-1)**k+float(RNG.uniform(-0.012, 0.012))
            opening_pans[character].append(round(position, 5))
            shoe = synthesize_shoe(character, strength)
            add_at(effects, pan_mono(shoe, position), start)
    effects[:33*RATE] *= (1-ease((T[:33*RATE]-32.3)/0.7))[:, None]
    effects[33*RATE:] = 0.0

    # Retain the approved common gain everywhere. If coincident early steps
    # need extra headroom, reduce only that isolated 0–33s foley section.
    target = 10**(-9.5/20)
    bed = ambience[:33*RATE]+music[:33*RATE]
    opening = effects[:33*RATE]
    opening_gain = 1.0
    if np.max(np.abs((bed+opening)*gain)) > target:
        lo, hi = 0.0, 1.0
        for _ in range(32):
            trial = (lo+hi)/2
            if np.max(np.abs((bed+opening*trial)*gain)) <= target:
                lo = trial
            else:
                hi = trial
        opening_gain = lo
        opening *= opening_gain

    # Cloth's main envelope crest is 74.80s, on the shoulder release.
    # The precursor begins at 74.64s, five hundredths after the proof's cue.
    cloth_start = 74.64
    add_at(effects, pan_mono(proof['cloth'], -0.08), cloth_start)
    final_bai = [76.20, 76.72, 77.24, 77.76]
    final_zei = [76.34, 76.86, 77.38, 77.90]
    for start, position, shoe in zip(final_bai, proof['bai_positions'], proof['bai_shoes']):
        add_at(effects, pan_mono(shoe, position), start)
    for start, position, shoe in zip(final_zei, proof['zei_positions'], proof['zei_shoes']):
        add_at(effects, pan_mono(shoe, position), start)

    stems = {'ambience': ambience*gain, 'effects': effects*gain, 'music': music*gain}
    del ambience, effects, music, bed, opening
    mix = sum(stems.values())
    assert mix.shape == (4_032_000, 2) and np.isfinite(mix).all()
    assert np.max(np.abs(mix)) < 10**(-3/20)
    assert np.all(stems['music'][silence_a:silence_b] == 0.0)
    assert np.all(stems['music'][:23*RATE] == 0.0)
    assert np.all(stems['effects'][33*RATE:int(cloth_start*RATE)] == 0.0)
    music_match = float(np.max(np.abs(stems['music'][int(66.01*RATE):70*RATE]
                     - proof['stems']['music'][int(0.01*RATE):4*RATE])))
    ambience_match = float(np.max(np.abs(stems['ambience'][int(66.5*RATE):int(77.5*RATE)]
                        - proof['stems']['ambience'][int(0.5*RATE):int(11.5*RATE)])))
    effects_match = float(np.max(np.abs(stems['effects'][round(76.2*RATE):round(77.97*RATE)]
                       - proof['stems']['effects'][round(10.2*RATE):round(11.97*RATE)])))
    assert music_match < 1e-10 and ambience_match < 1e-12 and effects_match < 1e-12

    report = {
        'title': 'The Surplus — complete Snowmoon soundtrack',
        'license': 'GPL-3.0-only',
        'provenance': 'Original deterministic local procedural synthesis. No voices, recordings, external samples, downloads, or paid tools.',
        'format': '48 kHz, stereo, 32-bit IEEE float WAV',
        'duration_seconds': DURATION, 'frames': N,
        'seeds': {'approved_proof': 66782026, 'full_film': 8420261013},
        'master_gain_db': round(float(20*np.log10(gain)), 6),
        'opening_foley_additional_gain_db': round(float(20*np.log10(opening_gain)), 6),
        'mastering': 'Approved proof common gain retained. Early-footstep section alone trimmed if required for -9.5 dBFS sample headroom. No compression or limiting.',
        'music_start_dry_until_seconds': 23.05,
        'music_absolute_silence_seconds': [70.0, 79.7],
        'music_silence_frame_range_start_inclusive_end_exclusive': [silence_a, silence_b],
        'music_silence_verified_zero_samples': int(np.count_nonzero(stems['music'][silence_a:silence_b]) == 0),
        'music_events': sorted(music_events, key=lambda e: e['onset_seconds']),
        'music_end_fade_seconds': [82.45, 84.0],
        'ambience_end_fade_seconds': [82.8, 84.0],
        'notable_distant_rotor_seconds': [41.0, 49.0],
        'rotor_note': 'The approved near-inaudible residual rotor texture at 66–73s is also retained inside the original wind bed.',
        'cloth_shoulder_release_seconds': 74.8,
        'cloth_waveform_start_seconds': cloth_start,
        'cloth_crest_approximate_seconds': 74.8,
        'footfall_onsets_by_character_seconds': {
            'Bai': {'opening': opening_bai, 'final': final_bai},
            'Zei': {'opening': [round(t, 9) for t in opening_zei], 'final': final_zei},
        },
        'footfall_counts_by_character': {'Bai': 67, 'Zei': 67},
        'opening_footfall_fade_seconds': [32.3, 33.0],
        'zei_gait': 'first_contact(t)=0.20+0.14*(1-smoothstep(23,28,t)); (t-first_contact(t))/1.04+side*0.5 is integer, side alternating 0/1. Contacts quantized to nearest 48 kHz frame.',
        'footfall_pan_by_character': {
            'Bai': {'opening': opening_pans['Bai'], 'final': proof['bai_positions']},
            'Zei': {'opening': opening_pans['Zei'], 'final': proof['zei_positions']},
        },
        'proof_continuity_max_absolute_sample_difference': {
            'music_66.01_to_70': music_match,
            'ambience_66.5_to_77.5': ambience_match,
            'effects_76.2_to_77.97': effects_match,
        },
        'proof_extensions': 'Half-second ambience crossfades at 66 and 78. No old 78-second shoe cutoff; final Zei release completes at 78.26s. Cloth crest moved 0.05s later to the 74.8s release.',
        'files': {},
    }
    converted_stems = {}
    for name, data in {'mix': mix, **stems}.items():
        filename = f'the_surplus_84s_{name}.wav'
        converted = data.astype(np.float32)
        wavfile.write(OUT/filename, RATE, converted)
        read_rate, readback = wavfile.read(OUT/filename)
        assert read_rate == RATE and readback.shape == (N, 2)
        assert np.isfinite(readback).all()
        file_stats = stats(readback)
        assert file_stats['estimated_true_peak_4x_dbfs'] < -3.0
        file_stats['sha256'] = hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
        report['files'][filename] = file_stats
        if name == 'music':
            assert np.all(readback[silence_a:silence_b] == 0.0)
        converted_stems[name] = converted
    unity_error = float(np.max(np.abs(converted_stems['mix'].astype(np.float64)
                      - sum(converted_stems[k].astype(np.float64) for k in stems))))
    report['float32_unity_stem_sum_max_absolute_error'] = unity_error
    assert unity_error < 1e-7
    report['verification'] = {
        'all_files_exactly_4032000_stereo_frames': True,
        'all_files_48000_hz': True,
        'music_gap_is_exact_digital_zero': True,
        'all_estimated_true_peaks_below_minus_3_dbfs': True,
        'all_outputs_finite': True,
    }
    (OUT/'audio_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in [
        'title', 'master_gain_db', 'opening_foley_additional_gain_db',
        'proof_continuity_max_absolute_sample_difference', 'files', 'verification'
    ]}, indent=2))


if __name__ == '__main__':
    main()
