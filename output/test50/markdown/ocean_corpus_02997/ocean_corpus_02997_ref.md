---
document_id: "epmc-pmc12341629"
title: "High-resolution reanalysis biological ocean data from the Copernicus Marine Service Information for Philippine marine research"
authors: ["Brenna Mei M. Concolis"]
publisher: "Elsevier"
journal: "Data in Brief"
publication_year: 2025
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: []
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC12341629"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12341629/fullTextXML"
doi_or_report_id: "10.1016/j.dib.2025.111913"
doi: "10.1016/j.dib.2025.111913"
pmcid: "PMC12341629"
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-28"
language: "en"
---

## Abstract

In the absence of observation data, remotely sensed data provides an effective alternative in characterizing spatiotemporal dynamics and patterns of oceanographic data. Some of the most important variables are biomass estimates which describe the productivity of a certain area. Analyzing data with such indices is a useful tool to identify biological hotspots and shifts in concentrations that could be related to phenomenon and changes in the climate. As biomass patterns are crucial in the coastal areas, it is important to utilize data with high resolution at high frequencies (daily) to reduce the bias and capture significant changes in the coast. The E.U. Copernicus Marine Service Information provides reanalysis data of global biomass content that can be freely access by public users. However, problems accessing data could arise for users without prior knowledge of handling large data which is due to the high-resolution properties of the datasets. In addition, processing of large data can be challenging for users with technical hardware limitations. This dataset is provided to help Philippine marine researchers work with net primary productivity, micronekton, and zooplankton, even if they have technical limitations. Daily values, monthly and annual means, climatologies (daily, monthly, and long-term), and anomalies (daily, monthly, and annual) are provided in the public repository. The dataset will allow short-term and long-term analysis in the Philippine waters.

Specifications TableSubjectMarine Science, Biological OceanographySpecific Subject AreaGridded high-resolution biomass and productivity data in the Philippine seasType of DataReanalysis data from E.U. Copernicus Marine Service Information (CMEMS)VariablesMass content of micronektonMass content of zooplanktonNet primary productivity (NPP)Data Format.csv and .rdsData LimitsLongitude: 110 – 130°ELatitude: 2 – 30°NPeriod covered: 01 January 1998 – 31 December 2023ResolutionSpatial: 0.083° x 0.083°Temporal: daily, monthly, annualData Source LocationE.U. Copernicus Marine Service Information [1]Data AccessibilityData Identification Number:https://doi.org/10.5281/zenodo.14918590Direct URL to data: https://zenodo.org/records/14961405Related Research ArticleNone

## Value of the Data

•This dataset offers long-term, high-resolution biological reanalysis data for Philippine waters—an ecologically critical region known as the global center of marine biodiversity and one of the top fish-producing nations worldwide. In the absence of extensive in situ observational data, this dataset enables researchers to analyze spatiotemporal patterns and trends in biomass (NPP, zooplankton, and micronekton) from 1998 to 2023.•The data is optimal for short-term variability assessment (e.g., seasonal productivity shifts) and long-term trend analyses (e.g., climate-related changes) of local NPP, zooplankton, and micronekton estimates in the Philippines from a large dataset over the period 1998–2023.•By providing a subsetted data restricted to the Philippine boundaries, the dataset significantly reduces the file size, allowing researchers to save memory storage and choose specific local areas of interest only.•The data provides more flexible file formats (.csv and .rds) which can be easily used for further analysis by researchers of diverse backgrounds and levels. This is especially helpful for those who are not familiar with ‘netCDF’ file format, which is the format commonly used for storing and compiling large data, used by the Copernicus Marine Service Information. The .rds files can be used in R programming language, while .csv files can be used and imported in almost all softwares (including geographic information system)–making it accessible even to those with no scientific programming skills.•The processing and calculation of means, climatologies, and anomalies from multi-year global datasets often require high-performance computing capabilities. This dataset removes that barrier by providing pre-processed products, making it a substantial resource for researchers with limited technical capacities–thus adhering to ‘FAIR’ principles of findability, accessibility, interoperability, and reusability.•The dataset includes daily, monthly (seasonal), and long-term climatologies which provide reference baseline information for assessing deviations from ‘normal’ conditions. The inclusion of anomalies allows detection of significant events, such as productivity peaks and declines.

## Background

The Philippines, located in the western tropical Pacific, is known as the global center of marine biodiversity. It is home to thousands of marine flora and fauna [[2], [3], [4]] and lies within the Coral Triangle–the global coral reef biodiversity hotspot [4,5]. Additionally, the country has one of the world’s largest fish productions supplying to global markets [6]. In line with this, assessing short- and long- term changes in ocean biological productivity in these waters is crucial.

While the conventional way of estimating productivity in the marine environment uses chlorophyll data [7,8], the emergence of reanalysis data from sources such as the E.U. Copernicus Marine Service Information enables the use of additional biological variables including NPP, zooplankton, and micronekton biomass, for instance [1]. Among these variables, NPP is considered a key proxy parameter in estimating autotrophic production and serves as a baseline for evaluating trophic abundance [9].

The Philippine seas are highly influenced by seasonal monsoons [10], mesoscale eddies, Rossby waves [11], and large-scale external climate forcings [12]. For example, upwellings southwest off Luzon Strait [13] and Zamboanga Peninsula [14] were reported to induce high levels of productivity due to enhance vertical mixing. Moreover, large-scale climate modes such as El Niño Southern Oscillation (ENSO) and Indian Ocean Dipole (IOD) are highly related to NPP changes in the western tropical Pacific, where high positive anomalies coincided with strong El Niño years [12]. These dynamics underscore the region-specific responses of biological variables to oceanographic and climatic drivers [15,16]. Despite these factors, local studies examining spatiotemporal trends and patterns in ocean biological productivity in the Philippines remain limited as opposed to its adjacent seas– South China Sea [10,17,18] and Indonesian waters [16,19,20]. One key limitation may be the availability of high-resolution and accessible long-record data. In the absence of observational data, reanalysis data can provide long historical records of biological data at equally spaced grids and regular temporal frequency–optimal for detecting trends and patterns.

The present paper offers subsetted publicly available reanalysis data of biological variables namely, mass content of micronekton and zooplankton, and NPP in the Philippine seas, and encourages trends and variability studies. In addition, pre-calculated baseline references in the form of daily, seasonal (monthly), and long-term means (also known as ‘climatology’), which are used to quantify how values deviate from the mean or ‘normal’ conditions [21], along with corresponding anomalies are made available.

Furthermore, researchers may explore the effects of physical variables such as sea surface temperature, ocean currents, surface wind, upwelling [18], seasonal monsoons [10,22], and large-scale remote climate forcing backgrounds [19,23] such as Pacific Decadal Oscillation, ENSO [24], and IOD to these biological data to understand the mechanisms that characterize the productivity in the area. Finally, this data can be used as input data for ecological modeling, forecasting, and prediction, which may serve as reference for fisheries and marine resource management and climate change impact assessment.

## Data Description

The data contains data frames or tables with longitude (x), latitude (y), date, and values columns for each biological variable. The files include daily, monthly, and annual values, as well as climatologies and anomalies for 1998–2023. These data are provided in .csv and .rds formats, except for daily values and daily anomalies, which are only in .rds. This is due to the limited capacity of the .csv format and the limited memory storage of the repository used to store these data. Nevertheless, users can easily access the .rds format in R using the ‘readRDS’ base function and subset the data according to their specific spatial and temporal needs. A sample code will be made available upon request.

## Experimental Design, Materials and Methods

### Data source

The raw data was accessed from the Copernicus Marine Service Information using the ‘copernicusmarine’ API toolbox. This toolbox allows fast-track downloading of datasets available in the E.U. Copernicus Marine Data Store, with functions to subset over specific area and time period of interest. To focus on the Philippine local boundaries, data within these geographical coordinates were downloaded: 110 – 130 °E and 2 – 30 °N. These boundaries, however, do not necessarily depict accepted national boundaries. The specific product used was the ‘Global ocean low and mid trophic levels biomass content hindcast’ with the product identifier ‘GLOBAL_MULTIYEAR_BGC_001_033′ (https://doi.org/10.48670/moi-00020) [1]. The spatial resolution is 0.083° x 0.083° with daily fields of various variables. Only three variables were extracted for climatology and anomaly analysis: net primary productivity (‘npp’, mg/m2), micronekton biomass (‘mnkc_epi’, g/m2), and zooplankton biomass (‘zooc’, g/m2).

### Data processing and calculation

To ensure that pixel-wise mean calculations for all variables were based on sufficiently complete time series, a data quality mask was applied to exclude pixels with excessive missing data. For each pixel, the total number of valid (non-missing) daily values per pixel over the total number of days across the full time period (i.e., 1998–2023) was calculated. This assessment revealed a binary pattern in data availability, with pixels exhibiting either 100 % or 0 % valid observations. Pixels with 100 % valid data corresponded to water bodies, while those with no valid data (0 %) represented land masses–which were then removed prior to means calculations.

The masked data were stored as data frames for easier data manipulation. Daily values were converted to monthly means and annual means. To calculate the daily climatology, means of each day across all years at a given pixel point were calculated such as in Eq. (1):(1)Climatologyd=1N∑y=1NXy,d

Where: ‘d’ is the day index (1 to 365/365); ‘y’ is the year index; ‘N’ is the number of years (in this case, 26 years), and ‘X’ indicates one of the variables (net primary productivity, zooplankton, or micronekton) values for year ‘y’ and ‘d’. Similarly, monthly climatology, as shown in Fig. 1, Fig. 2, Fig. 3, was calculated by computing for the average of the monthly means across all years at each grid point such as in Eq. (2):(2)Climatologym=1N∑y=1NXy,mFig. 1Calculated monthly climatology of NPP across the period 1998–2023.Fig 1Fig. 2Calculated monthly climatology of micronekton biomass across the period 1998–2023.Fig 2Fig. 3Calculated monthly climatology of zooplankton biomass across the period 1998–2023.Fig 3

The annual climatology or long-term mean was calculated by averaging the annual means per grid point, which is also referred as the long-term mean/climatology such as in Eq. (3):(3)Climatologya=1N∑y=1NXy

The anomalies were then calculated by removing the climatology from the daily, monthly, and annual actual values per grid cell. All data manipulation and calculation processes were done using the R programming language [25].

## Limitations

‘Not Applicable’
