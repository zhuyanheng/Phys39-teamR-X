# A4: Finite-Rod Model And Validity Checks

> **Status: scaffold only.** The four parts below are still to be written by
> each team member individually. Only the course-supplied parameters and the
> working checklist are filled in; every `TODO` must be replaced before the
> submission, and the numbers in the provisional tables must be recomputed
> from our measured geometry.

## Submission header

| Field | Value |
|---|---|
| Name | `TODO` |
| Assignment code | A4 |
| Date | 2026-10-28 |
| Repository | https://github.com/zhuyanheng/Phys39-teamR-X |
| Git commit hash | `TODO` (commit the finished file first, then paste the hash) |
| Moodle file | `A4_Lastname.pdf` |

## Provisional course-rod parameters

Replace with measured values at S16/S17. The literature `k` and the assumed
`h` range are for order-of-magnitude checks, not measurements.

| Quantity | Value | Note |
|---|---|---|
| Material | 6061-T6 aluminum | given |
| Diameter `d` | 12.7 mm | nominal, measure |
| Radius `R = d/2` | 6.35 mm | from `d` |
| Area `A = πR²` | 1.267×10⁻⁴ m² | from `d` |
| Perimeter `P = πd` | 3.990×10⁻² m | from `d` |
| `A/P` | 3.175×10⁻³ m | `= R/2` |
| `k` | ≈ 167 W/(m·K) | literature value for 6061-T6 |
| `h` | 5–10 W/(m²·K) | natural-convection range in air |
| Analysis length `L` | 0.30 m `TODO` | first thermistor hole to tip |
| Sensor positions | `TODO` | measured relative to `x = 0` |

Resulting estimates: `m = 3.07–4.34 m⁻¹`, `1/m = 0.23–0.33 m`,
`mL = 0.92–1.30`, `Θ_tip = 0.51–0.69`, `Bi⊥ = (0.95–1.9)×10⁻⁴`.

## Part 1 — Apply Fourier's law (Lienhard Problem 1.3)

Requirements: show how Fourier's law produces each result, carry units on
every quantity, and identify any physically unreasonable result.

- [ ] `TODO`: statement of each sub-part and the answer with units
- [ ] `TODO`: dimensional check of every expression
- [ ] `TODO`: one sentence identifying the unphysical result and why

## Part 2 — Build the stationary finite-rod model

Starting point: conservation of energy on a slice `δx`, Fourier's law, and
Newton's law of cooling.

Levels: `-kA (dT/dx)|_{x+δx} + kA (dT/dx)|_x + hP δx (T − T∞) = 0` (W).

- [ ] `TODO`: slice energy balance with a labelled sketch or figure reference
- [ ] `TODO`: take `δx → 0` to obtain `d²θ/dx² − m²θ = 0`, `m² = hP/(kA)`
- [ ] `TODO`: general solution `θ = C₁e^{mx} + C₂e^{−mx}` (or the cosh form)
- [ ] `TODO`: apply `θ(0) = θ₀` (Dirichlet, measured base temperature)
- [ ] `TODO`: apply `dθ/dx = 0` at `x = L` (Neumann, insulated tip)
- [ ] `TODO`: obtain `Θ(x) = cosh[m(L − x)]/cosh(mL)` and `Θ_tip = 1/cosh(mL)`
- [ ] `TODO`: state the physical meaning of each boundary condition

## Part 3 — Test the finite-length approximation

- [ ] `TODO`: Lienhard Problem 4.12 → semi-infinite limit `Θ∞ = e^{−mx}`
- [ ] `TODO`: Example 4.8 and Problem 4.20 → effect of the tip approximation
- [ ] `TODO`: `mL` for the course rod
- [ ] `TODO`: `ε_T(x_i) = |Θ_finite − Θ∞|/|Θ_finite|` at every sensor
- [ ] `TODO`: stated error criterion (course starting value: `ε_T < 5%`)
- [ ] `TODO`: conclusion on whether the rod may be treated as semi-infinite,
      naming the sensor positions and criterion the conclusion depends on

Provisional `ε_T(x)` under the assumed parameters above:

| `x` (m) | 0.05 | 0.10 | 0.15 | 0.20 | 0.25 |
|---|---|---|---|---|---|
| `ε_T` (`h` = 5) | 4.7% | 10% | 17% | 25% | 33% |
| `ε_T` (`h` = 7) | 4.3% | 9.8% | 17% | 25% | 34% |
| `ε_T` (`h` = 10) | 3.6% | 8.7% | 16% | 24% | 35% |

## Part 4 — Test the one-dimensional approximation

- [ ] `TODO`: `Bi⊥ = h(A/P)/k = hR/(2k)` with the `h` and `k` range used
- [ ] `TODO`: self-consistent form `Bi⊥ = (mR/2)² = (md/4)²` from the fitted `m`
- [ ] `TODO`: **separate** conclusion on whether each cross section is
      isothermal — do not merge with the Part 3 length conclusion
- [ ] `TODO`: application question — electronic heat sink in air versus
      spacecraft radiator: which admits Newton's law of cooling, why
      convection is absent in space, and the radiative law that replaces it

## Dimensional and completeness checks

- [ ] every displayed equation carries units on both sides
- [ ] `m` in m⁻¹, `1/m` in m, `Bi⊥` and `ε_T` dimensionless
- [ ] PDF page 1 shows name, A4, date, repository URL, and exact commit hash
