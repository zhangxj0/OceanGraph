---
document_id: "zenodo-6bb40ec64216e998"
title: "GLOBESINK monthly POC flux and particle size climatology"
authors: ["Briggs, Nathan", "Henson, Stephanie", "Flohr, Anita", "Hilder, Hans"]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2026
document_type: "data_product_method_qc"
domain: "carbon_biogeochemistry"
subdomain: "ocean_carbon_air_sea_flux"
secondary_topics: ["marine_nutrient_cycles", "marine_organic_matter"]
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/19558504"
download_url: "https://zenodo.org/api/records/19558504/files/README.md/content"
doi_or_report_id: "10.5281/zenodo.19558504"
doi: "10.5281/zenodo.19558504"
pmcid: ""
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-28"
language: "en"
---

# GLOBESINK: Global Climatology of Particle Backscattering, Size, and Carbon Flux from BGC-Argo

**DOI:** [https://doi.org/10.5281/zenodo.19558504](https://doi.org/10.5281/zenodo.19558504)
**Version:** 1.0

---

## Overview

GLOBESINK is a global, gridded monthly climatology of particle optical backscattering, particulate organic carbon (POC), particle size, and sinking POC flux derived from observations collected by the Biogeochemical Argo (BGC-Argo) profiling float network.

This dataset provides both directly observed quantities and derived products, including uncertainty estimates associated with empirical conversions from optical backscattering to carbon and flux metrics.

---

## Data Sources and Attribution

This dataset is derived from observations collected by the international **Argo** and **Biogeochemical Argo (BGC-Argo)** programs.

- Argo data were collected and made freely available by the International Argo Program and the national programs that contribute to it ([https://argo.ucsd.edu](https://argo.ucsd.edu), [https://biogeochemical-argo.org](https://biogeochemical-argo.org)).
- This dataset is a **value-added research product** derived from those observations, but it is not an official Argo product and has not been reviewed or endorsed by the Argo program.

---

## Dataset Contents

This Zenodo record contains:

### NetCDF data products

- **GLOBESINK_monthly_climatologies.nc**
Raw monthly climatology derived directly from observations.

- Contains gaps where no data are available.

- **GLOBESINK_monthly_climatologies_smoothed_interpolated.nc**
Gap-filled and spatially smoothed version of the climatology.

- Missing regions are interpolated except in the Arctic and regions of persistent sea ice around Antarctica.

---

### Supporting tables

- **GLOBESINK_netcdf_variable_summary.xlsx**
Summary of all primary climatological variables included in the NetCDF files, including:

- Variable names
- Units
- Descriptions

- **GLOBESINK_BBP700_visual_QC_exclusions.xlsx**
Records of data excluded during manual/visual quality control.

- **GLOBESINK_BBP700_deep_offsets.xlsx**
Additive corrections applied to backscattering measurements to align deep values of nearby sensors.

---

### Documentation

- **README** (this file)

---

## Data Description

### Spatial and Temporal Coverage

- **Latitude resolution:** 4°
- **Longitude resolution:** 8°
- **Depth range:** 0–2000 m
- **Vertical resolution:** variable (10–300 m)
- **Temporal resolution:** monthly climatology (12 months)

---

### Variables Included

The dataset includes:

#### Optical Backscattering (bbp)

Size-fractionated estimates representing particle populations across size classes from ~1–800 µm.

#### Particulate Organic Carbon (POC)

Derived from backscattering using empirical relationships.

#### Sinking POC Flux

Estimated using parameterized relationships linking particle size and concentration to sinking velocity.

#### Particle Size Metrics

- Area-weighted mean particle diameter of particles <800 µm
- Number concentrations in size classes:
- 200–400 µm
- 400–800 µm
- ≥ 800 µm

#### Environmental Variables

Directly from BGC-Argo variables:

- Temperature
- Salinity
- Nitrate
- pH
- Oxygen
- Chlorophyll-a

---

## Uncertainty Estimates

Derived variables include two types of uncertainty:

### Precision uncertainty

- Arises from stochastic sampling of rare, large particles
- Reported as **upper and lower 95% confidence intervals**

### Systematic uncertainty

- Propagated from uncertainty in empirical parameter values used in conversions
- Multiple uncertainty sources are added quadratically

Naming convention:

```text _precision_upper _precision_lower _systematic_uncertainty_upper _systematic_uncertainty_lower
```

All uncertainty fields are **additive** and share the same dimensions as their parent variable.

---

## Flux Metadata Parameters

Scalar parameters used in flux and POC calculations are included in the NetCDF files as scalar variables. These include:

- Conversion coefficients
- Sinking speed parameters
- Empirical exponents
- Upper and lower bounds for sensitivity analysis

Each parameter includes:

- Units
- Description
- Bound type (where applicable)

---

## Data Processing Summary

- Optical backscattering measurements from BGC-Argo floats are partitioned into particle size classes.
- Empirical relationships are applied to estimate:
- POC concentration
- Particle size
- Sinking flux
- Uncertainty is quantified from:
- Parameter bounds (systematic uncertainty)
- Sampling variability (precision uncertainty)
- Two products are generated:
- A raw climatology (data gaps preserved)
- A smoothed/interpolated climatology (gap-filled except in ice-covered regions)

---

## Validation

Sinking POC flux estimates were evaluated against an independent global dataset (Mouw et al., 2016, [https://doi.org/10.1594/PANGAEA.855600](https://doi.org/10.1594/PANGAEA.855600)):

- Mean relative bias: ~**1.25**
- Coefficient of determination: **r² = 0.58 (log scale)**

---

## File Format

All gridded data are provided in NetCDF format following CF conventions where possible.

### Dimensions

- `depth`
- `lat`
- `lon`
- `month`

### Missing Values

Missing data are encoded using a `_FillValue`.

---

## Usage Notes

- Derived quantities depend on empirical relationships and should be interpreted accordingly.
- Particle size estimates are not independently validated.
- Interpolated fields should be used with caution in regions of sparse observations.
- Gap-filled data are not provided in regions of persistent sea ice.

---

## Citation

Please cite both the dataset and the associated publication:

**Dataset:**

> GLOBESINK dataset (v1.0). Zenodo. [https://doi.org/10.5281/zenodo.19558504](https://doi.org/10.5281/zenodo.19558504)

**Associated publication:**

> [To be added upon publication]

---

## Authors

Nathan Briggs, Stephanie Henson, Anita Flohr, Hans Hilder

---

## Funding and Acknowledgements

This work was supported by the UK Natural Environment Research Council (NERC) GLOBESINK project (NE/X008657/1), the European Union Horizon 2020 project TechOceans (Grant Agreement No. 101000858), the NERC National Capability Single Centre Science Programme AtlantiS (NE/Y005589/1), and the European Union under grant agreement no. 101083922 (OceanICU) and UK Research and Innovation (UKRI) under the UK government’s Horizon Europe funding guarantee (grant number 10054454, 10063673, 10064020, 10059241, 10079684, 10059012, 10048179).

We acknowledge the Argo and BGC-Argo programs for providing the observational data that underpin this dataset ([https://www.seanoe.org/data/00311/42182/](https://www.seanoe.org/data/00311/42182/)).

---

## Contact

For questions or feedback:

Nathan Briggs
National Oceanography Centre, Southampton, UK
natbrig@noc.ac.uk

---

## License

Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## Notes

This dataset represents a research-derived synthesis product and is subject to revision in future versions.
