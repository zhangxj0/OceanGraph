---
document_id: "zenodo-50fbcedabc5d98a5"
title: "Particulate organic carbon and particulate organic nitrogen concentrations and stable isotope composition of seawater sampled during the Antarctic Circumnavigation Expedition (ACE) during the Austral Summer of 2016/2017."
authors: ["Thomalla, Sandy", "Antoine, David", "Berliner, David", "Little, Hazel", "Moutier, William", "Olivier-Morgan, Alexandra", "Robinson, Charlotte", "Ryan-Keogh, Thomas", "Schuback, Nina"]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2020
document_type: "technical_report"
domain: "carbon_biogeochemistry"
subdomain: "marine_nutrient_cycles"
secondary_topics: ["ocean_acidification_carbonate", "primary_production_phytoplankton", "marine_organic_matter"]
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/3859515"
download_url: "https://zenodo.org/api/records/3859515/files/README.txt/content"
doi_or_report_id: "10.5281/zenodo.3859515"
doi: "10.5281/zenodo.3859515"
pmcid: ""
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-28"
language: "en"
---

﻿Particulate organic carbon and particulate organic nitrogen concentrations and stable isotope composition of seawater sampled during the Antarctic Circumnavigation Expedition (ACE) during the Austral Summer of 2016/2017.

***** Dataset abstract *****

This dataset contains particulate organic carbon and particulate organic nitrogen concentrations and stable isotope composition (delta 13C and delta 15N) sampled during the Antarctic Circumnavigation Expedition (ACE) Leg 1-3. Water samples were collected from the underway seawater supply every 3 hours, filtered onto pre-combusted glass fibre filters, acidified to remove inorganic compounds and analysed for both elements on the same filter using an elemental analyser. These samples provide an estimate of the organic carbon and organic nitrogen concentration and carbon and nitrogen stable isotope composition of living and detrital particles > 0.7 micrometres in size.

***** Original data collection *****

Samples for particulate organic carbon and particulate organic nitrogen and stable isotope composition were collected from the underway seawater supply every 3 hours. Up to 2 L of sweater was filtered onto pre-combusted 0.7 micrometre pore size 25-millimetre diameter glass fibre filters (Whatman) under low vacuum pressure. The filters were pre-combusted in a furnace at 450 degrees Celsius for 4 hours prior to the voyage and stored in foil envelopes (200 filters per envelope). After filtration, the filters were oven dried (40 degrees Celsius for 24 hours) on board and then exposed to an acidic environment via fuming with HCl (34 %, ca. 10.9 M) within a desiccator for 24 hours to remove carbonates. Samples were not re-dried after acidification. Next, each filter was ‘punched out’ to remove excess filter around the sample area and then individually packaged into individual tin capsules for solids (5x9 mm). Encapsulated samples were stored dry and separated in individual wells of 96 wellplates which were individually packaged within ziplock bags containing silica gel and stored within a desiccator until analysis post-voyage.

Ten sets of triplicate samples were collected, sampled throughout Legs 2 and 3 to assess uncertainties in particulate organic carbon and nitrogen concentrations due to sampling.

A total of 72 ‘dry blank’ samples were also collected, interspersed every roughly every 6 samples, to account for the addition of organic matter during sample manipulation and processing. These samples were collected and processed exactly as above, except that no seawater was filtered through the filters. Four adsorbed dissolved organic matter blanks were also collected across Leg 2 and 3 to account for the adsorption of dissolved matter onto the filter matrix during sample filtration (Gardner et al. 2003). For these samples the seawater was replaced by Milli-Q water (3 samples; ’MILLI Q1’, ‘MILLI Q2’, ‘MILLI Q3) and 0.7 micrometre seawater filtrate (1 sample, i.e. remaining seawater after passing through 0.7 micrometre filter once; ‘FSW’). These samples were then processed as above.

Elemental analysis of the samples was performed post-voyage at the Stable and Light Isotope Laboratory, Department of Archaeology, University of Cape Town. Samples were analysed on a Flash 2000 organic elemental analyser (Thermo Fisher Scientific) flash combustion system coupled to a Delta V Plus isotope ratio mass spectrometer (IRMS, Thermo Fisher Scientific) via a Conflo IV gas control unit (Thermo Scientific). Quantification and isotopic corrections were calculated using DL-Valine (Sigma Aldrich), Silica Gel 60 (Merck Millipore) and ammonium chloride (NH4Cl) standards run alongside the samples. The expected values of each standard were DL-Valine: -26.8 o/oo delta 13C, 12.14 o/oo delta 15N; Silica Gel 60: -20.05 o/oo delta 13C; 7.5 o/oo delta 15N; NH4Cl: -0.57 o/oo delta 15N. The accuracy and precision for standards runs was better than +/- 0.2 o/oo for standards Silica Gel 60 and DL-Valine for carbon and nitrogen and better than +/- 1 o/oo for the NH4Cl standard for nitrogen. The R^2 for standard curves for delta 13C and delta 15N were > 0.9. The NH4Cl standards were likely affected by some carry over from the actual ocean samples during the analyses and so some caution should be exercised interpreting delta 15N values < 0 o/oo.

Information on the underway seawater supply can be found in the ACE Cruise Report (Walton and Thomas 2018, DOI: 10.5281/zenodo.1443511).

***** Data processing *****

Following elemental analysis, the average concentration of carbon and nitrogen (micrograms) in the dry blanks was calculated and subtracted from the organic carbon and organic nitrogen (micrograms) concentration of each sample. The sample concentrations were then volume corrected (litres) to produce sample concentrations of micrograms per litre and then converted to micromolar by dividing by the atomic mass of carbon (12.0107) and nitrogen (14.0067) respectively. Triplicate samples have been averaged to be represented by one value for carbon and one value for nitrogen for the sampling timepoint and are indicated by the replicate flag where 1 = ‘1 replicate’ and 2 = ‘3 replicates’. No further processing was applied to the adsorption blanks carbon and nitrogen concentrations (micrograms). See the QAQC section for the recommended application of the adsorption blanks. No further processing was applied to the stable isotope composition data (delta 13C and delta 15N).

Latitude and longitude for each datapoint have been extracted from the ACE GPS one-minute resolution dataset for underway samples (Thomas and Pina Estany 2019; DOI: 10.5281/zenodo.3483166), matched by date and time. For the blanks in file ace_uw_poc_pon_blanks_20200512CURRSGCMR.csv, accurate date and time was not recorded, and so the date and time of the blank collection can be inferred from the labels of the seawater samples collected before and after each blank filter recorded in the columns ‘project_sample_number_before’ and ‘project_sample_number_after’.

***** Quality checking *****

Following elemental analysis, samples were flagged if the carbon or nitrogen detection voltage (mV) was outside the limit of detection with ‘EA Flag’ where 1 = ‘good’ and 2 = ‘outside limit of detection’.

The helium flag (He_Flag) indicates when helium gas dilution of carbon samples fell below 80 % where 1 = 80 % and 2 = 60 %.

The precision (+- 1 standard deviation from the mean) for each triplicate set varied from 1.4 % - 27.4 % for carbon concentrations and 1.5 % - 25.3 % for nitrogen concentrations.

The relationship between particulate organic carbon and total chlorophyll-a was calculated using the corresponding samples from the phytoplankton pigment data set (Antoine et al. 2020; DOI: 10.5281/zenodo.3816726) and compared to existing global relationships (Loisel & Morel 1998, Stramska & Stramski 2005, Sathyendranath et al. 2009) and Southern Ocean relationships (Thomalla et al. 2017). There is a noticeable offset of approximately 50 micrograms between the dataset carbon to chlorophyll relationship and global relationships, an amount which is roughly equal to the carbon measured in the adsorbed blanks (see file ace_uw_poc_pon_blanks_20200512CURRSGCMR.csv; blanks ‘MILLI Q1’, ‘MILLI Q2’, ‘MILLI Q3’, ‘FSW’). Careful consideration should be given by the user to the application of these blanks and correction for organic matter adsorbed on the filter. See IOCCG Protocol Series Draft from Chaves et al. 2019 on particulate organic carbon measurements for more advice.

***** Standards *****

Internationally recognised standards (NIST Standard Reference Materials) were used when analysing samples, and each standard was calibrated against International Atomic Energy Agency) standards. Stable isotope values of nitrogen are expressed relative to atmospheric nitrogen and carbon are expressed relative to Pee-Dee Belemnite.

***** Dataset contents *****

- README.txt, metatdata, text
- data_file_header.txt, metadata, text
- ace_uw_poc_pon_blanks_20200512CURRSGCMR.csv, data file, comma-separated values
- ace_uw_poc_pon_20200512CURRSGCMR.csv, data file, comma-separated values

**** Dataset contact *****

David Antoine, Curtin University, Australia. ORCID: 0000-0002-9082-2395. Email: david.antoine@curtin.edu.au
Charlotte Robinson, Curtin University, Australia. ORCID: 0000-0001-8519-5641. Email: charlotte.robinson@curtin.edu.au, charlotte.mary.robinson@gmail.com

***** Dataset license *****

This particulate organic carbon and particulate organic nitrogen concentration, and stable isotope composition of seawater dataset from ACE is made available under the Creative Commons Attribution 4.0 International License (CC BY 4.0) whose full text can be found at https://creativecommons.org/licenses/by/4.0/

***** Dataset citation *****

Please cite this dataset as:
Thomalla, S., Antoine, D., Berliner, D., Little, H., Moutier, W., Olivier, A., Robinson, C., Ryan-Keogh, T. and Schuback, N. (2020). Particulate organic carbon and particulate organic nitrogen concentrations and stable isotope composition of seawater sampled during the Antarctic Circumnavigation Expedition (ACE) during the Austral Summer of 2016/2017. (Version 1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.3859515
