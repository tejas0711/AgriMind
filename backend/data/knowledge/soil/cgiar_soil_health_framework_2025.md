---
title: "Soil Health Assessment and Management Framework"
issuing_organization: "CGIAR Sustainable Farming Science Program / ICRISAT"
doc_date: "2025"
url_or_file: "data/knowledge/soil/cgiar_soil_health_framework_2025.md"
license: "CC BY-NC 4.0"
applicable_crops: "all, dryland crops, legumes, sorghum, millets"
applicable_regions: "Global, Semi-Arid Tropics, India, Sub-Saharan Africa"
category: "soil"
---

# CGIAR Soil Health Assessment and Management Framework (2025)

Source: Desta, G., Agegnehu, G., Patil, M., Choudhari, P., Legesse, G., Desalegn, H., and
Botoman, L. (2025). *Soil Health Assessment and Management Framework.* CGIAR Sustainable
Farming Science Program Report, implemented by CGIAR researchers at ICRISAT. Licensed
CC BY-NC 4.0. Note: this is a working paper and has not been peer reviewed, per the authors'
own disclaimer — treat it as one authoritative reference among several, not a sole source of
truth.

## What is soil health?

Soil health is the capacity of soil to function as a living ecosystem that sustains plant,
animal, and human health, not just a soil's nutrient content for a single crop. It is broader
than "soil fertility," which tends to focus narrowly on nutrient supply for plant growth. Soil
health spans three overlapping domains: physical (structure, compaction, water movement),
chemical (pH, nutrient availability, salinity), and biological (microbial activity, organic
matter, soil fauna) — the biological domain is the one most often neglected in conventional soil
management.

## Why soil health matters

Healthy soil supports stronger root growth, better nutrient cycling, and improved water
retention, which together make farms more productive and more resilient to drought and flood.
It also improves water infiltration, reduces runoff, recharges groundwater, and filters
pollutants before they reach rivers and lakes. Soils are the largest terrestrial carbon sink, so
healthy soil management also contributes to climate mitigation. Economically, healthy soil
reduces input costs over time and protects the long-term value of land by preventing
degradation such as erosion and nutrient depletion.

## Four principles of soil health management

1. **Keep soil covered** — maintain residue or living plant cover on the soil surface at all
   times to protect against erosion, conserve moisture, suppress weeds, and feed soil
   microorganisms.
2. **Disturb less** — minimize tillage and avoid overuse of fertilizers and pesticides, which
   can damage soil structure and biology.
3. **Diversify** — use diverse crop rotations, cover crops, and (where feasible) integrated
   livestock to stimulate soil biology and nutrient cycling.
4. **Manage for specific context** — tailor decisions to local climate, soil type, topography,
   and the farmer's own resources rather than applying one-size-fits-all rules.

## Six core soil health functions

1. **Nutrient cycling** — storing, transforming, and releasing plant-available nutrients.
2. **Water regulation** — absorbing, storing, and supplying water to plants, and recharging
   groundwater; depends on good soil structure (stable aggregates and pores).
3. **Habitat for soil biodiversity** — physical habitat for earthworms, insects, bacteria, and
   fungi that drive the other functions.
4. **Stability and erosion resistance** — root systems and fungal networks bind soil particles
   into aggregates that resist erosion.
5. **Filtering and buffering** — clay and organic matter adsorb and help break down
   contaminants before they reach groundwater.
6. **Carbon sequestration** — pulling atmospheric CO2 into stable soil organic matter.

## Soil pH classification (Hazelton and Murphy, 2025)

This is a finer-grained pH scale than a simple acidic/neutral/alkaline split:

- 3.0–4.0: very strongly acidic
- 4.0–5.5: strongly acidic
- 5.5–6.0: moderately acidic
- 6.0–7.0: slightly acidic
- 7.0–8.0: slightly alkaline
- 8.0–9.0: moderately alkaline
- 9.0–10.0: strongly alkaline
- 10.0–11.0: very strongly alkaline

Most field crops and vegetables perform best in the slightly acidic to slightly alkaline range
(roughly 6.0–7.5).

## Electrical conductivity / salinity classification (Smith and Doran, 1996)

For a 1:2 soil-to-water extract, across all textures:

- 0–2 dS/m: non-saline
- 2.1–4 dS/m: slightly saline
- 4.1–8 dS/m: moderately saline
- 8.1–16 dS/m: strongly saline
- above 16.1 dS/m: very strongly saline

This is a more detailed grading than a single "safe vs. unsafe" cutoff, and is useful context
when explaining EC results even though AgriMind's deterministic engine currently only flags a
single high-EC threshold (2.0 dS/m) for triggering a salinity caution.

## A note on organic carbon and nitrogen scales — read before changing engine thresholds

This framework also publishes organic-carbon and total-nitrogen bands (Hazelton and Murphy,
2025; Janzen, 1987; Carter, 1992; Bruce and Rayment, 1982) that **measure different things**
than the Soil Health Card fertility thresholds already used in AgriMind's deterministic engine:

- The framework's organic-carbon bands (very low <0.40–0.59%, low 0.60–0.99%, moderate
  1.00–1.59%, high 1.60–1.99%, very high 2.00–2.99%) describe a broader *soil health / biological
  function* scale, not the narrower *crop fertility* scale (low <0.5%, medium 0.5–0.75%, high
  >0.75%) that Indian Soil Health Cards use and that AgriMind's `fertilizer_optimizer.py`
  currently implements. A sample at 0.45% organic carbon is "LOW" on the SHC fertility scale
  (verified against a real lab report) but would also read as "very low to low" on this broader
  scale — the two scales roughly agree at the low end here, but shouldn't be assumed to always
  agree, since they're built for different purposes.
- The framework's total-nitrogen bands (very low <0.05%, low 0.05–0.15%, medium 0.15–0.25%,
  high 0.25–0.50%, very high >0.5%) are measured as a **percentage of total soil nitrogen**
  (e.g. via Kjeldahl digestion), not **plant-available nitrogen in kg/ha** (via the alkaline
  permanganate method), which is what AgriMind's engine and most Indian Soil Health Cards
  actually report and threshold against. These two nitrogen measurements are not
  interchangeable and should never be substituted for one another in a threshold comparison.

AgriMind's engine thresholds were intentionally NOT changed to match this document's bands,
to avoid silently mixing incompatible measurement methods. This section exists so that both the
retrieval system and any future engineering work treat this framework as a *complementary*
reference on soil health concepts, pH, and salinity grading — not as a drop-in replacement for
the fertility-focused N/P/K/OC thresholds already validated against real lab reports.

## Soil health indicator selection — what makes a good indicator

A sound soil health indicator should be: proven and easy to measure, valid and reliable,
sensitive and specific to the condition being assessed, responsive to both state and change over
time, meaningful to the stakeholders using it (e.g. farmers and extension agents), cost-effective
to measure at scale, and appropriate to the spatial scale of the assessment (field, farm,
district, or national level). There is no single universal soil health indicator or "magic
number" — a sound assessment framework selects a minimum set of indicators that matches the
specific management goals and context of the land being assessed.
