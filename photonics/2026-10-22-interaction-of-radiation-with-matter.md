# Interaction of Radiation with Matter

**Lecture:** [mod01lec02 — NPTEL IIT Delhi](https://www.youtube.com/watch?v=22JoBNhNR24)  
**Notes taken:** 2026-10-22

[![Watch on YouTube](https://img.youtube.com/vi/22JoBNhNR24/hqdefault.jpg)](https://www.youtube.com/watch?v=22JoBNhNR24)

> The lecture recaps the laser as a source of radiation made of an active medium, a pump, an amplifier and a feedback unit. It then sets out how radiation interacts with the atoms of the active medium. It covers discrete energy levels, emission and absorption spectra, and atomic population in thermal equilibrium (Boltzmann distribution). It ends by arguing that population inversion cannot occur in equilibrium and needs external pumping. The transcript is very noisy, so some details below are reconstructed from fragments.

## Key concepts

- **Matter as atoms with discrete energy levels** — The active medium is a collection of atoms. Their electronic states are characterised by discrete energy levels, and radiation interacts with matter through the electric field of the electromagnetic wave acting on the electrons. [1:54](https://www.youtube.com/watch?v=22JoBNhNR24&t=114s)
- **Spectral energy density (black body radiation)** — Energy per unit volume per unit frequency interval, rho(nu), for radiation between frequencies nu and nu+d(nu). It is built from the number of modes per unit volume, the occupation probability, and the photon energy h*nu. The black body spectrum is the plot of rho(nu) against nu. [5:35](https://www.youtube.com/watch?v=22JoBNhNR24&t=335s)
- **Pumping** — Supplying energy so that atoms are excited to a higher energy level. Sources mentioned include another light source, a flame, an electric discharge and chemical reactions. The photon (or other energy) must match the energy difference between the levels. [9:44](https://www.youtube.com/watch?v=22JoBNhNR24&t=584s)
- **Emission spectrum** — Excited atoms drop to lower levels and emit photons whose energy equals the level difference. Plotting intensity against frequency or wavelength shows distinct lines rather than a continuum, which directly shows that atomic energy levels are discrete. [13:12](https://www.youtube.com/watch?v=22JoBNhNR24&t=792s)
- **Hydrogen spectral series** — Transitions ending on n=1 form the Lyman series and those ending on n=2 form the Balmer series, which is in the visible. The energy levels are not equally spaced; the spacing gets smaller at higher levels. Each transition has a different energy and so a different wavelength. [15:19](https://www.youtube.com/watch?v=22JoBNhNR24&t=919s)
- **Absorption spectrum** — A broadband source is passed through the medium and the transmitted light is measured with a spectrometer as a function of frequency or wavelength. Transmission dips at frequencies corresponding to energy differences between levels. This is the absorption spectrum, and it shows the same discrete level structure. [18:03](https://www.youtube.com/watch?v=22JoBNhNR24&t=1083s)
- **Atomic population** — The number of atoms per unit volume in a given energy level. It is a key quantity because it determines how the medium responds to radiation. [21:31](https://www.youtube.com/watch?v=22JoBNhNR24&t=1291s)
- **Boltzmann distribution in thermal equilibrium** — Population of a level is proportional to exp(-E/kT) (with degeneracy g, taken as 1 for non-degenerate levels). The ratio of two populations is exp(-(E2-E1)/kT). So population always decreases as energy increases. [22:46](https://www.youtube.com/watch?v=22JoBNhNR24&t=1366s)
- **Thermal energy kT and eV conversions** — At room temperature (about 300 K), kT = 1.38e-23 J/K x 300 K, about 4.1e-21 J, or roughly 0.025 eV. Energy in eV = 1.24 / wavelength in micrometres, so a 0.62 micrometre photon is about 2 eV. That is vastly larger than kT, so upper-level populations at room temperature are tiny. [29:16](https://www.youtube.com/watch?v=22JoBNhNR24&t=1756s)
- **Population inversion needs external pumping** — In thermal equilibrium the upper level can never be more populated than the lower one. A situation with more atoms in the higher level can only be created by external pumping. The lecturer says this is a necessary condition for laser action, to be developed in later lectures. [35:58](https://www.youtube.com/watch?v=22JoBNhNR24&t=2158s)

## Walkthrough

### Recap and motivation [0:34](https://www.youtube.com/watch?v=22JoBNhNR24&t=34s)

- A laser is a source of radiation with an active medium (pumped), an amplifier and a feedback unit.
- The active medium is an atomic system, so we must study how radiation interacts with atoms.

### Matter, radiation and how to treat their interaction [1:54](https://www.youtube.com/watch?v=22JoBNhNR24&t=114s)

- Matter is a collection of atoms; electronic states have discrete energy levels.
- Radiation is an electromagnetic wave, and interaction occurs through its electric field acting on electrons.
- The rigorous treatment is quantum electrodynamics, but this course uses a simple classical approach, borrowing selected results from quantum theory.

### Black body radiation and spectral energy density [4:35](https://www.youtube.com/watch?v=22JoBNhNR24&t=275s)

- Spectral energy density rho(nu) is energy per unit volume per unit frequency.
- It equals the number of modes per unit volume times the occupation probability times the photon energy.
- The black body spectrum plots rho against frequency.

### Pumping and excitation mechanisms [9:44](https://www.youtube.com/watch?v=22JoBNhNR24&t=584s)

- Excitation can come from light, flames, electric discharge or chemical reactions.
- Pumping raises atoms to a higher level by supplying the energy difference.

### Emission spectra and discrete levels [13:12](https://www.youtube.com/watch?v=22JoBNhNR24&t=792s)

- Atoms de-excite and emit photons at energies given by level differences.
- Spectra show distinct lines with different intensities, which is evidence for discrete levels.
- Hydrogen: Lyman and Balmer series; level spacing shrinks at higher levels.
- Transition energies are of the order of electron volts.

### Absorption spectra [18:03](https://www.youtube.com/watch?v=22JoBNhNR24&t=1083s)

- A broadband source is passed through the medium and the transmitted light is analysed with a spectrometer.
- Dips in transmission at particular frequencies indicate absorption between levels.

### Atomic population and Boltzmann statistics [21:31](https://www.youtube.com/watch?v=22JoBNhNR24&t=1291s)

- Population is the number of atoms per unit volume in a level.
- In thermal equilibrium, population is proportional to exp(-E/kT), with degeneracy factor g.
- Room temperature: kT is about 0.025 eV; energy (eV) = 1.24 / wavelength (micrometres).
- For a transition of about 2 eV the equilibrium population of the upper level is extremely small.

### Population diagram and population inversion [33:52](https://www.youtube.com/watch?v=22JoBNhNR24&t=2032s)

- The population diagram shows that population decreases with increasing energy in thermal equilibrium.
- Population inversion is a necessary condition for laser action and is impossible in thermal equilibrium.
- It requires an external pumping mechanism, to be discussed in the next lecture.

## Review questions

- [ ] Why is a quantum treatment strictly needed for radiation-matter interaction, and how does this course simplify it?
- [ ] What do the discrete lines in emission and absorption spectra tell us about atoms?
- [ ] How is the Balmer series different from the Lyman series, and why does the level spacing in hydrogen get smaller at higher energies?
- [ ] Write the thermal-equilibrium population ratio of two levels and explain why the upper level is almost empty at room temperature for a 2 eV transition.
- [ ] How would you convert a wavelength of 0.62 micrometres to photon energy in eV?
- [ ] Why can population inversion not occur in thermal equilibrium, and what is needed to produce it?

## To look up

- Quantum electrodynamics treatment of radiation-matter interaction
- Precise derivation of black body spectral energy density (modes per unit volume and occupation probability)
- Degeneracy of energy levels (g factors), said to be discussed later
- Mechanisms of pumping and how population inversion is achieved, promised for subsequent lectures
