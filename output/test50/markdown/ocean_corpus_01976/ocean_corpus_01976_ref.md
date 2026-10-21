---
document_id: "zenodo-5a8710f6d99dbeaf"
title: "The Impact of Large-Scale Macroalgae Cultivation and Harvesting Strategies on the Marine Carbon Dioxide Removal Efficacy and Marine Biogeochemistry - Supplementary materials"
authors: ["Anugerahanti, Prima", "Palmieri, Julien", "Yool, Andrew"]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2026
document_type: "sop_manual_instrument"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: ["ocean_acidification_carbonate", "ocean_carbon_air_sea_flux", "marine_nutrient_cycles", "marine_organic_matter"]
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/20154696"
download_url: "https://zenodo.org/api/records/20154696/files/README.md/content"
doi_or_report_id: "10.5281/zenodo.20154696"
doi: "10.5281/zenodo.20154696"
pmcid: ""
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-28"
language: "en"
---

# MEDUSA-Macroalgae archive

This is the Zenodo archive for ancillary information associated with the manuscript of Anugerahanti et al. (2026). The full citation for the preprint manuscript is as follows:

Anugerahanti, P., Palmieri, J., Baker, C. A., Popova, E., and Yool, A.: The Impact of Large-Scale Macroalgae Cultivation and Harvesting Strategies on the Marine Carbon Dioxide Removal Efficacy and Marine Biogeochemistry, EGUsphere [preprint], https://doi.org/10.5194/egusphere-2025-5360, 2025.

The ORCID information for the authors of the manuscript are as follows:

- Prima Anugerahanti: https://orcid.org/0000-0002-5033-7934
- Julien Palmieri: https://orcid.org/0000-0002-0226-5243
- Chelsey Baker: https://orcid.org/0000-0002-0840-2333
- Ekaterina Popova: https://orcid.org/0000-0002-2012-708X
- Andrew Yool: https://orcid.org/0000-0002-9879-2776

---

This archive is comprised of the following:
1. A tarfile of the codebase of the macroalgae-adapted version of MEDUSA
2. A tarfile of the simulation output from the experiments described in the manuscript
3. (This `README.md` file)

---

## 1. MEDUSA-Macroalgae code

### 1.1 Codebase

The Fortran code of `MEDUSA-Macroalgae` used in the Anugerahanti et al. (2026) manuscript is contained in the tarfile attached in this zenodo archive (`medusa-MEDUSA-Macroalgae.tar`). This has been extracted from MEDUSA's gitlab:

https://gitlab.com/nocacuk/OCM/medusa

Where it is been tagged as a specific release:

https://gitlab.com/nocacuk/OCM/medusa/-/releases/MEDUSA-Macroalgae

The specific git branch used to develop this release is `28-rebase-macro-algae-in-medusa-nemo4-2-branch`. This codebases uses NEMOv4.2.

Most subroutines of the original MEDUSA codebase have been modified to include the new macroalgae components and the associated variables and diagnostics. Two new subroutines have been added, and these are where the majority of the calculations associated with the macroalgae are performed.

- `btd_magcroalgae.F90`: where fluxes are calculated
- `btd_macroupdate.F90`: where macroalgaes trends are updated.

### 1.2 Running MEDUSA-Macroalgae

The MEDUSA-Macroalgae simulations performed for the manuscript have been run within the Near-Present-Day (NPD) framework developed and used by the National Oceanography Centre (NOC). This is a "ready-to-run" framework that runs reanalysis-forced, ocean-only simulations of the NEMO4.2 model for the global domain in 1°-, 1/4°- and 1/12°-resolution configurations. For further information about NPD, see:

https://github.com/NOC-MSM/NOC_Near_Present_Day

The NPD code version used to run MEDUSA-Macroalgae is [V0.9.0](https://github.com/NOC-MSM/NOC_Near_Present_Day/releases/tag/v0.9.0)

To use the macroalgae version of MEDUSA within the NPD framework follow the instructions in the NPD gitlab at the link above, and modify the "setup" script, to extract MEDUSA's gitlab macroalgae branch, by replacing the MEDUSA branch used at the head of the script: replace

```
MEDUSA_Br=16-medusa-nemo4-2-1-3
```
with
```
MEDUSA_Br=28-rebase-macro-algae-in-medusa-nemo4-2-branch
```

Then continue with the NPD instructions. MEDUSA's namelists will need to be adapted to run MEDUSA with or without macroalgae, by setting `ln_msa_macroalgae` to `.true.` or `.false.` in the `namelist_medusa_cfg` namelist in your running directory. In this latter namelist, don't forget to adapt the macroalgae parameters to correspond to the experimental choices that you wish to use.

For additional assistance, please contact `Prima.Anugerahanti@noc.ac.uk` or `julien.palmieri@noc.ac.uk`.

## 2. MEDUSA-Macroalgae output

The tar file `MEDUSA-Macroalgae_Outputs.tar` contains annual average outputs from the final year of seven simulations — the control plus six experiments — described and discussed in the paper:

1. control
2. default
3. Fe-limited
4. harv200
5. harv800
6. high-mortality
7. no-sinking

Each experiment directory includes the annual average `ptrc` and `diad` files for year 2023 (the final simulated year). The relevant contents of these files are as follows:

- `ptrc` includes the 3D outputs of MEDUSA's tracers. All tracers are represented throughout the model domain, although in the case of particulate tracers (plankton and detritus) these are mostly zero below the depth of the euphotic zone. The full list of tracers is given below, in each case with the field name followed by its description.
```
CHN: "Chl-a concentration in non-diatom phytoplankton" ;
CHD: "Chl-a concentration in diatom phytoplankton" ;
PHN: "non-diatom phytoplankton" ;
PHD: "diatom phytoplankton" ;
ZMI: "micro zooplankton" ;
ZME: "meso zooplankton" ;
DIN: "dissolved inorganic nitrogen" ;
SIL: "dissolved silicic acid" ;
FER: "dissolved iron" ;
DET: "detrital nitrogen" ;
PDS: "biogenic silicon in diatom phytoplankton" ;
DTC: "detrital carbon" ;
DIC: "dissolved inorganic carbon" ;
ALK: "alkalinity" ;
OXY: "dissolved oxygen" ;
```

- `diad` includes a mixture of MEDUSA diagnostics (2D and 3D), macroalgae state variables and macroalgae diagnostics. There are 245 fields in total within each file, and the list below is a subset of this that includes only 1. macroalgae state variables, 2. macroalgae diagnostics, and 3. MEDUSA diagnostics used in the manuscript's analysis.

- Macroalgae state variables: macroalgae 01, 02, 03, 04, and 05 correspond to *Saccharina*, *Sargassum*, *Eucheuma*, *Macrocystis*, and *Porphyra*, respectively (see `namelist_medusa_ref`). For the simulations described in the manuscript, we only include macroalgae 01 to 04.

```
MACN1: "Macroalgae 01 N concentration" ;
MACN2: "Macroalgae 02 N concentration" ;
MACN3: "Macroalgae 03 N concentration" ;
MACN4: "Macroalgae 04 N concentration" ;
MACN5: "Macroalgae 05 N concentration" ;
MCHL1: "Macroalgae 01 CHL concentration" ;
MCHL2: "Macroalgae 02 CHL concentration" ;
MCHL3: "Macroalgae 03 CHL concentration" ;
MCHL4: "Macroalgae 04 CHL concentration" ;
MCHL5: "Macroalgae 05 CHL concentration" ;
```
- Macroalgae diagnostics
```
PPRMA1: "Macroalgae Production" ;
INT_MACN1: "Vertically integrated Macroalgae" ;
PPRMA2: "Macroalgae Production" ;
INT_MACN2: "Vertically integrated Macroalgae" ;
INT_MACN3: "Vertically integrated Macroalgae" ;
PPRMA3: "Macroalgae Production" ;
INT_MACN4: "Vertically integrated Macroalgae" ;
PPRMA4: "Macroalgae Production" ;
INT_MACN5: "Vertically integrated Macroalgae" ;
PPRMA5: "Macroalgae Production" ;
MORTM1: "Macroalgae 01 mortality" ;
MORTM2: "Macroalgae 02 mortality" ;
MORTM3: "Macroalgae 03 mortality" ;
MORTM4: "Macroalgae 04 mortality" ;
MORTM5: "Macroalgae 05 mortality" ;
MLOSS1: "Macroalgae 01 metab. loss" ;
MLOSS2: "Macroalgae 02 metab. loss" ;
MLOSS3: "Macroalgae 03 metab. loss" ;
MLOSS4: "Macroalgae 04 metab. loss" ;
MLOSS5: "Macroalgae 05 metab. loss" ;
HARVEST: "Harvest frequency" ;
TM_HARVEST: "Total integrated macroalgae" ;
```
- MEDUSA diagnostics
```
PRN: "Non-diatom primary production" ;
PRD: "Diatom primary production" ;
CO2FLUX: "Air-sea CO2 flux" ;
INT_PN: "Vertically integrated Pn" ;
INT_PD: "Vertically integrated Pd" ;
INT_ZMI: "Vertically integrated Zmi" ;
INT_ZME: "Vertically integrated Zme" ;
SFR_OXY: "Seafloor dissolved oxygen" ;
SFR_DIN: "Seafloor dissolved inorganic nitrogen" ;
SFR_DIC: "Seafloor dissolved inorganic carbon" ;
```
