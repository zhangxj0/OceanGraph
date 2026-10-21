---
document_id: "nasa-technical-reports-server-e7d9fe7f2559f8c3"
title: "Using NASA Earth Observations to Identify Trends in Harmful Algal Blooms in Narragansett Bay"
authors: ["Isabella Giordano", "Mahnoor Naeem", "Chloe Rowen", "Samuel Millay"]
publisher: "NASA"
journal: ""
publication_year: 2024
document_type: "sop_manual_instrument"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: []
source_platform: "NASA Technical Reports Server"
source_url: "https://ntrs.nasa.gov/citations/20240014776"
download_url: "https://ntrs.nasa.gov/api/citations/20240014776/downloads/2024AGU_Poster_H11K_Giordano.pdf"
doi_or_report_id: "nasa-ntrs:20240014776"
doi: ""
pmcid: ""
license_status: "NASA-PUBLIC-USE-PERMITTED"
license_url: "https://sti.nasa.gov/disclaimers/"
accessed_at: "2026-07-28"
language: "en"
---

H11K-0831
Using NASA Earth Observations to Identify Trends in Harmful Algal Blooms in
Narragansett Bay
Isabella Giordano1,2 (igiordano418@gmail.com), Mahnoor Naeem1,2 (mahnoorn@gmail.com), Chloe Rowen1,2 (chloe.rowen@gmail.com), Samuel Millay1,2 (smillay55@gmail.com)
NASA DEVELOP National Program, 2 Analytical Mechanics Associates Inc.
ABSTRACT
OBJECTIVES
RESULTS
Identify proxy parameters for remote sensing models
In Situ Chl-a VS Ratio 709/665*10
Station B3 (Conimicut Point)
Station B3 (Conimicut Point)
Chl-a VS nFLH 2017
In Situ Chl-a VS OLCI Chl-a 2020
Station B6 (Mountain View)
Chl-a (ug/L)
nFLH *100
Chl-a (ug/L)
Ratio 709/665 *100
In SituChl-a (ug/L)
OLCI Chl-a (mg/m3)
of HABs
Analyze the presence of HABs both spatially and
temporally
Investigate the feasibility of remote sensing products
to identify small scale HABs
Chl-a (ug/L) & Ratio*10
Chl-a (ug/L) & mg/m3
Chl-a (ug/L) & nFLH
DATA & METHODS
-10
6/1/20 7/1/20 8/1/20
9/1/20 10/1/20 11/1/20
7/1/2017 8/1/2017 9/1/2017
10/1/2017
7/1/2017 8/1/2017 9/1/2017
10/1/2017
In Situ Dataset:
Identified peak bloom events using the phytoplankton
Date
Date
Date
Figure 2: Time series visualization of in situ chl-a
Figure 3: Time series visualization of in situ chl-a values
vs. Sentinel-3 OLCI band ratio values for the year 2017
Figure 4: Time series visualization of in situ chl-a
values vs. Sentinel-1 chl-a values for the year 2020
values vs. nFLH (sr-1) values for the year 2017
timeseries from the Environmental Protection Agency
(EPA) and Rhode Island Department of Environmental
Management (RIDEM) YSI sondes.
Mapped a transect from the Upper Bay to the Lower
Bay through 7 EPA sondes and 7 RIDEM sondes.
Created 3x3 pixel areas (900x900m) along transect for
direct comparison of in situ chlorophyll and total
suspended solids (TSS) values and remotely sensed
values.
Narragansett Bay in Rhode Island is known for its quahog, or hardshell clam, shellfisheries. However, increased levels in harmful algal
blooms (HABs) have posed threats to quahog populations and
raised public health concerns due to shellfishery closures resulting
from contamination with neurotoxins released by phytoplankton.
NASA DEVELOP partnered with the Environmental Protection
Agency’s National Health and Environmental Effects Research
Laboratory and Rhode Island’s Department of Environmental
Management to use Earth observations and the partners’ in situ
data to visualize phytoplankton bloom events within the bay. The
team used Sentinel-3 Ocean and Land Color Instrument (OLCI),
Landsat 8 Operational Land Imager (OLI), and Landsat 9 OLI-2 to
track proposed proxies for phytoplankton from June 2016 to
October 2023. Multiple sensors and datasets were employed for
more accurate results due to the small spatial extent of
Narragansett Bay. Chlorophyll-a and total suspended solids were
determined to be accurate parameters to monitor HAB events.
Although complications could arise due to the relatively small size
of the bay and small-scale of the bloom events, which may be
difficult to visualize via remote sensing, Earth observations have
proven to help strengthen HAB research, monitoring, and
prediction and will complement the extensive in situ data in
Narragansett Bay.
Nechad TSS, FNU
STUDY AREA
EPA TSS, milligrams/liter
Figure 5: Time series visualization of in situ TSS values
N
vs. Nechad TSS (sr-1) values from 2016 to 2023
Providence
Figure 6. SeaDAS visualization of nFLH (sr-1) through the months of June-October in 2016
Figure 1: Map showing EPA and RIDEM field measurement
stations and acquired satellite data transect points in the West
Passage.
Warwick
Sentinel-3 Dataset
Calculated the Normalized Fluorescence Line Height, or
nFLH (Equation 1) and ratio between OLCI bands 709
nm and 665 nm (Equation 3) from values along transect
in MATLAB, to be used as chlorophyll proxies
Retrieved remotely-sensed chlorophyll values from OLCI
Newport
as an additional chlorophyll proxy
Calculated the Nechad Turbidity Algorithm (Equation 2)
Narragansett
as a proxy for TSS.
Created timeseries in Excel to compare chlorophyll and
TSS proxies to in situ samples and performed a
correlation analysis to calculate R2
25km
Figure 7. NDTI Timeseries for years 2016, 2017, 2018,
Figure 8. SeaDAS visualization of TSS (FNU) through the months of June-October in 2016
Esri, TomTom, Garmin, SafeGraph, METI/NASA, USGS, EPA, NPS, USDA, USFWS
2019, 2021, 2022
Visualized the two most accurate proxies in SeaDAS
Landsat 8/9 Dataset
Calculated Normalized Difference Turbidity Index (NDTI)
CONCLUSIONS
ACKNOWLEDGEMENTS
using Landsat 8 OLI & Landsat 9 OLI-2 data
Created timeseries in Excel to compare NDTI to the in
Narragansett Bay
situ TSS values
MA
Chlorophyll-a and TSS are both effective proxies for
Table 1.
tracking HABs.
nFLH was the best remote sensing product for
CT
RI
Equations for Earth observations pre-processing
Study Area:
Narragansett Bay, RI
nFLH
tracking chlorophyll.
The Nechad algorithm was the best remote sensing
Nechad Turbidity Algorithm
product for tracking TSS.
Landsat 8 and Landsat 9 products were not effective in
Esri, TomTom, Garmin, SafeGraph, METI/NASA,
USGS, EPA, NPS, USDA,USFWS
Study Period:
June to October,
2016 to 2023
Advisor:
Dr. Cedric Fichot (Boston University)
Partners:
Dr. Autumn Oczkowski (United States Environmental Protection Agency)
Dr. David Borkman (Rhode Island Department of Environmental
Management)
Lead:
Madison Arndt (DEVELOP Massachusetts – Boston)
709 mm/665 nm Band Ratio
tracking turbidity because of the lack of data and
appropriate bands to analyze this dark body of water.
NDTI
W H A T I S D E V E L O P ?
N A S A E A R T H A C T I O N | D E V E L O P N A T I O N A L P R O G R A M
This material is based upon work supported by NASA through contracts NNL16AA05C and 80LARC23FA024. Any mention of a commercial product, service, or activity in this material does not constitute NASA endorsement. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Aeronautics and Space Administration and partner organizations.
Since 1998, DEVELOP has fostered the use of Earth observation data and geospatial information to better inform
environmental decision making. As a dual capacity building program, DEVELOP builds skills to access and apply
satellite data in both its participants (students, recent graduates, and transitioning career professionals) and
project partners (federal, state, and local governments; non-profits and for-profits; and international organizations).
Projects are conducted in rapid, 10-week terms (spring, summer, & fall), by small teams of participants under the
guidance of NASA and partner Science Advisors.
Visit the DEVELOP website for more information for how to get involved!
