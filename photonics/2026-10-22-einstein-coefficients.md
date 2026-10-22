# Einstein Coefficients: Emission and Absorption

**Lecture:** [mod01lec03 — NPTEL IIT Delhi](https://www.youtube.com/watch?v=049abZcKErY)  
**Notes taken:** 2026-10-22

[![Watch on YouTube](https://img.youtube.com/vi/049abZcKErY/hqdefault.jpg)](https://www.youtube.com/watch?v=049abZcKErY)

> The lecture continues the study of how radiation interacts with matter, using a two-level atomic system. It introduces absorption, spontaneous emission and stimulated emission through Einstein's rate equations. It uses thermal equilibrium, Boltzmann statistics and the blackbody (Planck) energy density to relate these processes. It ends with the spontaneous emission lifetime and a demonstration that measures it with a chopped laser beam and a detector. The audio transcript is badly garbled, so some details are inferred from context and flagged as uncertain.

## Key concepts

- **Two-level atomic system** — The simplest model is an atom or system with a ground level (1) and an excited level (2), with populations N1 and N2 per unit volume. Interaction with radiation means transitions between these levels: absorption (1 to 2) and emission (2 to 1). [0:35](https://www.youtube.com/watch?v=049abZcKErY&t=35s)
- **Absorption rate** — The rate of absorption is proportional to the number of atoms in the ground state (N1) and to the spectral energy density of the radiation at the transition frequency. In symbols: rate = B12 * N1 * rho(nu), where B12 is a constant of proportionality. [2:45](https://www.youtube.com/watch?v=049abZcKErY&t=165s)
- **Spontaneous emission (Einstein A coefficient)** — Einstein pointed out two types of emission. Spontaneous emission happens without any radiation present, and its rate is proportional only to the excited-state population N2. In symbols: rate = A21 * N2. [3:38](https://www.youtube.com/watch?v=049abZcKErY&t=218s)
- **Stimulated emission (Einstein B coefficient)** — An incident photon can induce an excited atom to emit. The rate is proportional to N2 and to the energy density: B21 * N2 * rho(nu). The emitted photon has the same energy, polarization, phase and direction as the stimulating photon. The output therefore adds coherently to the input, giving a larger amplitude and an intensity proportional to the square of the amplitude. [5:52](https://www.youtube.com/watch?v=049abZcKErY&t=352s)
- **Equilibrium rate balance** — At thermal equilibrium the upward rate equals the downward rate. Absorption rate = spontaneous plus stimulated emission rate, so B12 N1 rho = A21 N2 + B21 N2 rho. This equation links the Einstein coefficients to the populations. [8:17](https://www.youtube.com/watch?v=049abZcKErY&t=497s)
- **Boltzmann population ratio** — In thermal equilibrium the populations of the two levels follow Boltzmann statistics: N2/N1 is proportional to exp(-(E2-E1)/kT) = exp(-h nu/kT), with degeneracy factors included. The energy difference between the levels is h times the frequency. [10:20](https://www.youtube.com/watch?v=049abZcKErY&t=620s)
- **Blackbody comparison to relate the coefficients** — The two-level system in equilibrium behaves like a blackbody, absorbing and emitting at its particular frequency. The energy density from the rate equation is compared with Planck's blackbody energy density, which holds at all temperatures. This yields relations between the A and B coefficients. [11:47](https://www.youtube.com/watch?v=049abZcKErY&t=707s)
- **Ratio of spontaneous to stimulated emission** — The lecture works out the ratio of spontaneous to stimulated emission rates, which depends on exp(h nu/kT) - 1. It uses the conversion 1 eV corresponds to a wavelength of 1.24 micrometres, and compares the photon energy with the thermal energy at room temperature. At optical frequencies and room temperature, spontaneous emission dominates, and this is why it is difficult to make a laser. An exercise asks the student to work out a temperature from this ratio. [16:33](https://www.youtube.com/watch?v=049abZcKErY&t=993s)
- **Spontaneous emission lifetime** — Spontaneous emission lifetime is the time after which the number of atoms in the excited level drops to 1/e of its original value. It is related to the spontaneous emission rate A21 (lifetime = 1/A21). It can be measured by exciting the atoms with a pulse and watching the decay of the emitted light. [23:59](https://www.youtube.com/watch?v=049abZcKErY&t=1439s)

## Walkthrough

### Introduction and two-level system setup [0:00](https://www.youtube.com/watch?v=049abZcKErY&t=0s)

- The topic is the interaction of radiation with matter: emission, absorption and the Einstein coefficients.
- A two-level atomic system is the simplest model; emission and absorption occur between the ground and excited states.
- The medium contains N1 atoms per unit volume in the ground state and N2 in the excited state, in the presence of radiation of spectral energy density rho.

### Absorption and the two types of emission [2:45](https://www.youtube.com/watch?v=049abZcKErY&t=165s)

- Absorption rate is proportional to N1 and to the energy density of the radiation.
- Einstein recognised two emission processes, spontaneous and stimulated.
- Spontaneous emission rate is proportional only to N2 (coefficient A21).
- Stimulated emission is proportional to N2 and the energy density (coefficient B21).

### Properties of stimulated emission [5:10](https://www.youtube.com/watch?v=049abZcKErY&t=310s)

- The stimulated photon has the same energy, polarization and direction as the stimulating photon, a result from quantum theory.
- Amplifying a field this way gives higher output amplitude, with intensity proportional to the square of the amplitude.
- The emission occurs without changing the phase of the signal.

### Equilibrium and Boltzmann statistics [8:17](https://www.youtube.com/watch?v=049abZcKErY&t=497s)

- At equilibrium the rate of upward transitions equals the rate of downward transitions.
- Populations follow the Boltzmann distribution, with the energy difference between the levels equal to h nu.
- The rate equation is solved for the energy density.

### Matching to blackbody radiation [11:47](https://www.youtube.com/watch?v=049abZcKErY&t=707s)

- Recalling the previous class, the blackbody law gives the spectral energy density as a function of frequency and temperature.
- Comparing the two expressions, which must agree at all temperatures, gives relations among the Einstein coefficients.
- A two-level system acts like a blackbody at its transition frequency.

### Spontaneous versus stimulated emission at room temperature [16:33](https://www.youtube.com/watch?v=049abZcKErY&t=993s)

- The ratio of spontaneous to stimulated emission is derived, involving exp(h nu/kT) - 1.
- Numerical estimate: 1 eV corresponds to 1.24 micrometres, so the photon energy can be compared with the thermal energy.
- At room temperature spontaneous emission dominates at optical frequencies.
- An exercise is set to determine a temperature from this ratio.

### Introducing the lifetime parameter [20:24](https://www.youtube.com/watch?v=049abZcKErY&t=1224s)

- Einstein coefficients are of interest, but a measurable parameter is needed to obtain numerical values.
- The rate of spontaneous emission per unit time per unit volume is defined from the excited-state population.
- Population in the upper level decays exponentially, and the spontaneous emission lifetime is the time for it to fall to 1/e of its initial value.
- Lifetimes differ between atomic systems, ranging from short to long, and this is related to the rate of spontaneous emission.

### Demonstration: measuring spontaneous emission lifetime [28:36](https://www.youtube.com/watch?v=049abZcKErY&t=1716s)

- A simple set-up: a laser beam passes through a mechanical chopper, a rotating disc with opaque blades, spinning at high speed and giving square pulses of light.
- The pulsed beam excites the atomic system, which then emits light.
- The emitted light is collected by a photodetector, whose current is proportional to the number of photons arriving.
- The detector's signal is displayed on an oscilloscope via a resistor, showing the decay with time of the emission.
- The decay time of the signal gives the spontaneous emission lifetime of the system.
- The lecture mentions that the same idea applies to solids and semiconductors, and says the discussion continues in the next lecture.

## Review questions

- [ ] Write the rate expressions for absorption, spontaneous emission and stimulated emission in a two-level system. What does each one depend on?
- [ ] How does stimulated emission differ from spontaneous emission in terms of the emitted photon's energy, polarization, phase and direction?
- [ ] Why is the blackbody energy density used to relate the Einstein A and B coefficients? What condition is assumed?
- [ ] At room temperature and optical frequencies, which of spontaneous and stimulated emission dominates, and why? How does the ratio depend on h nu/kT?
- [ ] How is the spontaneous emission lifetime defined, and how does the chopper and photodetector experiment measure it?
- [ ] If N2/N1 follows the Boltzmann distribution, what happens to the population ratio as temperature rises?

## To look up

- The exact relations between A21, B21 and B12 (including the degeneracy factors) are not clearly recoverable from the transcript.
- The numerical exercise on determining a temperature from the spontaneous-to-stimulated emission ratio.
- How the lifetime relates to the A coefficient when several decay channels are present.
- Lifetime in solids and semiconductors, which was mentioned only briefly at the end.
- Population inversion and why it is needed, which follows from the discussion of the thermal equilibrium.
