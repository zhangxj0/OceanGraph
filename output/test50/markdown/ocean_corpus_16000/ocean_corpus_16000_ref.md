---
document_id: "zenodo-899c6428c745ed18"
title: "Oceanic carbon-13 and nitrogen-15 isotopes simulated by CSIRO Mk3L-COAL version 1.0"
authors: ["Buchanan, Pearse"]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2019
document_type: "data_product_method_qc"
domain: "carbon_biogeochemistry"
subdomain: "marine_nutrient_cycles"
secondary_topics: ["ocean_acidification_carbonate", "primary_production_phytoplankton", "marine_organic_matter"]
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/4922156"
download_url: "https://zenodo.org/api/records/4922156/files/Mk3L-COALv1-0_ocean_c13_n15_readme.txt/content"
doi_or_report_id: "10.5281/zenodo.4922156"
doi: "10.5281/zenodo.4922156"
pmcid: ""
license_status: "CC-BY-NC-SA"
license_url: "https://creativecommons.org/licenses/by-nc-sa/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

Oceanic carbon-13 and nitrogen-15 isotopes simulated by CSIRO Mk3L-COAL v1.0

The isotopes of carbon (delta13C) and nitrogen (delta15N) are commonly used proxies for understanding the ocean.
When used in tandem, they provide powerful insight into physical and biogeochemical processes. Here, we detail
the implementation of delta13C and delta15N in the ocean component of an Earth system model. We evaluate our
simulated delta13C and delta15N against contemporary measurements, place the model's performance alongside other
isotope enabled models, and document the response of delta13C and delta15N to changes in ecosystem functioning.
The model combines the Commonwealth Scientific and Industrial Research Organisation Mark 3L (CSIRO Mk3L) climate
system model with the Carbon of the Ocean, Atmosphere and Land (COAL) biogeochemical model. The oceanic component
of CSIRO Mk3L-COAL has a resolution of 1.6° latitude x 2.8° longitude and resolves multi-millennial timescales
, running at a rate of ~400 years per day. We show that this coarse resolution, computationally efficient model
adequately reproduces water column and coretop delta13C and delta15N measurements, making it a useful tool for
palaeoceanographic research. Changes to ecosystem function involve varying phytoplankton stoichiometry, varying
CaCO3 production based on calcite saturation state, and varying N2 fixation via iron limitation. We find that
large changes in CaCO3 production have little effect on delta13C and delta15N, while changes in N2 fixation and
phytoplankton stoichiometry have substantial and complex effects. Interpretations of palaeoceanographic records
are therefore open to multiple lines of interpretation where multiple processes imprint on the isotopic signature,
such as in the tropics where denitrification, N2 fixation and nutrient utilisation influence delta15N. Hence,
there is significant scope for isotope enabled models to provide more robust interpretations of the proxy records.

These simulations were run by Dr Pearse J Buchanan of the ARC Centre of Excellence for Climate Systems Sciences, as part of his PhD in quantitative marine science.

This dataset includes the following variables:

name title I J K
martin_exp Exponent (b) of the canonical Martin curve controlling remineralisation 1:128 1:112 ...
NO3toP nitrate:phosphorus ratio required to remineralise Particulate Organic Matter 1:128 1:112 ...
O2toP oxygen:phosphorus ratio required to remineralise Particulate Organic Matter 1:128 1:112 ...
NtoP nitrogen:phosphorus ratio of Particulate Organic Matter 1:128 1:112 ...
CtoP Carbon:phosphorus ratio of Particulate Organic Matter 1:128 1:112 ...
epcalc100 Downward Flux of Calcite 1:128 1:112 ...
expc Downward flux of Particulate Organic Carbon 1:128 1:112 ...
d15n_sed Depth-averaged annual delta15N isotopic composition of organic matter deposited in the sediments 1:128 1:112 ...
sedden Depth-integrated annual sedimentary denitrification rate in the ocean 1:128 1:112 ...
wcden Depth-integrated annual water column denitrification rate in the ocean 1:128 1:112 ...
n2fix Depth-integrated annual dinitrogen fixation rate in the ocean 1:128 1:112 ...
ndep Annual rate of nitrogen deposition to the ocean surface 1:128 1:112 ...
fsfe Surface Downward Net Flux of Iron 1:128 1:112 ...
aou Apparent Oxygen Utilization 1:128 1:112 1:21
no3_15 Dissolved Nitrate-15 Concentration 1:128 1:112 1:21
no3 Dissolved Nitrate Concentration 1:128 1:112 1:21
dfe Dissolved Iron Concentration 1:128 1:112 1:21
talk Total Alkalinity 1:128 1:112 1:21
po4 Dissolved Phosphate Concentration 1:128 1:112 1:21
dissic_13 Dissolved Inorganic Carbon-13 Concentration 1:128 1:112 1:21
dissic Dissolved Inorganic Carbon Conconcentration 1:128 1:112 1:21
o2 Dissolved Oxygen Concentration 1:128 1:112 1:21
so Sea Water Salinity 1:128 1:112 1:21
thetao Water Potential Temperature 1:128 1:112 1:21

The data is available online on the NCI TDS server:

https://dapds00.nci.org.au/thredds/catalogs/ks32/ARCCSS/Mk3L_COAL/Mk3L_COAL.html

and for NCI users in the ks32 project.

File organisation:

/g/data/ks32/ARCCSS_Data/Mk3L-COALv1-0_ocean_c13_n15/v1-0/.... contains the CF - ACDD compliant netcdf output

filenames:
CSIRO_Mk3L_COAL_V1-0_default.nc | Default version of model used for majority of data analysis
(variable stoichiometry, fixed CaCO3 production and high Fe limitation of N2 fixers (Kfe=0.5))
CSIRO_Mk3L_COAL_V1-0_redfield.nc | Version using static stoichiometry according to Redfield
CSIRO_Mk3L_COAL_V1-0_varyCaCO3-etahigh.nc | Version using variable CaCO3 production according to Calcite Saturation State (eta=1.09)
CSIRO_Mk3L_COAL_V1-0_varyCaCO3-etalow.nc | Version using variable CaCO3 production according to Calcite Saturation State (eta=0.53)
CSIRO_Mk3L_COAL_V1-0_varyCaCO3-etamed.nc | Version using variable CaCO3 production according to Calcite Saturation State (eta=0.81)
CSIRO_Mk3L_COAL_V1-0_varyN2Fix_FeLimlow.nc | Version using low Fe limitation of N2 fixers (Kfe=0.1)
CSIRO_Mk3L_COAL_V1-0_varyN2Fix_FeLimmed.nc | Version using moderate limitation of N2 fixers (Kfe=0.3)


Contact: pearse.buchanan@liverpool.ac.uk or pearseb@princeton.edu for any question on the dataset content and provenance
paola.petrelli@utas.edu.au for questions or issues with file accessibility

Citation:
Buchanan, Pearse, 2019: Oceanic carbon-13 and nitrogen-15 isotopes simulated by CSIRO Mk3L-COAL v1.0. NCI National Research Data Collection , doi: 10.25914/5c6643f64446

Associated paper:
Buchanan, PJ, Matear, RJ, Chase, Z , Phipps, SJ and Bindoff, NL 2019 , 'Ocean carbon and nitrogen isotopes in CSIRO Mk3L-COAL version 1.0: a tool for palaeoceanographic research' , Geoscientific Model Development, vol. 12, no. 4 , pp. 1491-1523 , doi: 10.5194/gmd-12-1491-2019.
