---
document_id: "nasa-technical-reports-server-37047029d47a3aa3"
title: "Optical Identification of Phytoplankton Groups in the Chesapeake Bay: Toward Application of a Hyperspectral Algorithm to Aid Resource Managers"
authors: ["S Morgaine Mckibben", "Stephanie Schollaert Uz"]
publisher: "NASA"
journal: ""
publication_year: 2021
document_type: "data_product_method_qc"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: ["marine_organic_matter"]
source_platform: "NASA Technical Reports Server"
source_url: "https://ntrs.nasa.gov/citations/20210020718"
download_url: "https://ntrs.nasa.gov/api/citations/20210020718/downloads/OSA_HISE-Final-McKibben_Summary.pdf"
doi_or_report_id: "nasa-ntrs:20210020718"
doi: ""
pmcid: ""
license_status: "NASA-PUBLIC-USE-PERMITTED"
license_url: "https://sti.nasa.gov/disclaimers/"
accessed_at: "2026-07-28"
language: "en"
---

Optical Identification of Phytoplankton Groups in the
Chesapeake Bay: Toward Application of a Hyperspectral
Algorithm to Aid Resource Managers
S. Morgaine McKibben1, Stephanie Schollaert Uz2
1NASA Postdoctoral Program/NASA Goddard Space Flight Center, Earth Science Division, 8800 Greenbelt Rd, Greenbelt, MD 20771
2NASA Goddard Space Flight Center, Earth Science Division, 8800 Greenbelt Rd, Greenbelt, MD 20771
morgaine.mckibben@nasa.gov, stephanie.uz@nasa.gov
Abstract: Multi- to hyperspectral evolution of satellite ocean color sensors is advancing spacebased coastal ocean science and applications. An approach for optically partitioning phytoplankton
(microalgae) communities into component groups is being developed for the Chesapeake Bay.
© 2021 The Author(s)
1. Introduction & Rationale
The upcoming Ocean Color Instrument (OCI) aboard the PACE orbiter will be NASA's first ocean color imager
with hyperspectral, global coverage (1-2 day revisit, 1 km resolution) [1]. In contrast to current and legacy
multispectral ocean color sensors, OCI will provide the spectral resolution necessary to deconvolve in-water
constituents in optically-complex coastal and estuarine waters. Two hyperspectral missions with complimentary
temporal and spatial coverage are also in development: Geostationary Littoral Imaging and Monitoring Radiometer
(GLIMR; 300 meter, ~sub daily resolution) Earth Venture Instrument launching in ~2027 [2] and a polar-orbiting
Surface Biology and Geology dedicated observable platform (SBG; ~30m, ~8-16 day revisit), currently an
architecture study [3]. Regional-scale efforts to develop novel satellite data products that meet end user needs are
needed to leverage the next-generation capabilities of these hyperspectral ocean color missions.
In this work a bio-optical algorithm that differentiates phytoplankton communities into component groups is
regionally-parameterized and evaluated in the Chesapeake Bay. This estuarine system provides a range of
economically important ecosystem services to the Mid-Atlantic United States and also exhibits impairment from
anthropogenic pressures and harmful algal blooms (HABs). Extensive Chesapeake Bay water quality monitoring
programs guide resource management and public health related decision making. With high in situ data density and
established relationships between NASA Goddard and regional stakeholders, the Chesapeake Bay is an ideal focus
area to develop hyperspectral-based ocean color applications.
2. Approach
This work will employ the theoretical framework of PHYtoplankton Detection with Optics (PHYDOTax), a semianalytical algorithm that deconvolves the spectral shape of remote sensing reflectance (Rrs) into phytoplankton taxa
at the class level (e.g. diatoms, dinoflagellates, cryptophytes, etc.) [4]. This approach is unique among other optical
phytoplankton-discrimination algorithms (e.g. [5]) in that it was developed for optically complex waters, is
regionally customizable, and allows for addition of other optically active constituents such as colored dissolved
organic matter (CDOM) and non-algal particles (NAP). Based on this framework, the research objectives of this
work are: 1) regional parameterization of algorithm; 2) quantitative evaluation of output using in situ and synthetic
data; 3) investigation of practical applications in the context of water quality monitoring in the Chesapeake Bay.
Objective 1: Regional parameterization requires creating a spectral signature library representative of
phytoplankton classes and other optically-dominant constituents that are commonly observed in the Chesapeake
Bay. Lab-measured (or modeled when measuring is not possible) inherent optical properties (IOPs) of
phytoplankton monocultures will be used to model an Rrs spectral signature for each culture. This work builds on
previous and current PHYDOTax application efforts by also incorporating CDOM and NAP signatures based on in
situ observations into the library. Once the regional signature library is developed the algorithm can be applied to
hyperspectral Rrs measurements.
Objective 2: Application of an inverse-matrix-based decomposition algorithm deconvolves the signature library
of “known” Rrs spectra into relative proportions of the constituents present in the “unknown” (measured) Rrs
spectrum. Coincident, in-water measures of Rrs and phytoplankton community composition in the Chesapeake Bay
from NASA’s SeaWiFS Bio-optical Archive and Storage System (SeaBASS; https://seabass.gsfc.nasa.gov) will be

used to statistically evaluate algorithm output. SeaBASS is a standardized system for archiving, cataloging, and
distributing in situ data collected during satellite ocean color field validation efforts. Synthetic datasets will also be
used to estimate measurement uncertainty due to variability in CDOM, NAP, and bottom reflectance.
Objective 3: Demonstrate practical application of the algorithm using hyperspectral data (in situ, airborne, and
satellite-based) and monitoring data. Points of hyperspectral satellite information with coincident in situ data at
numbers sufficient for statistical validation are not available. Rather, this effort will investigate whether known
physical drivers (e.g. season, salinity, temperature) of particular bloom types can be related to distributions of
phytoplankton groups in the imagery. For example, are expected seasonal patterns observable over time? The results
of this objective will qualitatively evaluate the algorithm and demonstrate practically applicable ways to utilize
imagery of phytoplankton distribution information (Figure 1) in the context of benefiting Chesapeake Bay water
quality monitoring efforts.
Figure 1: Sample maps of the distribution of 6 phytoplankton classes along the Potomac River and part of the Chesapeake Bay. Color
represents percent of total phytoplankton community. Maps are derived from Level 3 Hyperspectral Imager for the Coastal Ocean (HICO)
data for July 30, 2014 from NASA’s Ocean Biology Processing Group (OBPG, https://oceancolor.gsfc.nasa.gov). Note this imagery is 90
meter resolution, finer than the 1 km anticipated for the Ocean Color Imager on PACE and closer to the 30m resolution anticipated for SBG.
3. Conclusion
This work tests proof-of-concept for application of the theoretical framework of PHYDOTax in an estuarine system.
Algorithm evaluation across an estuarine-salinity gradient is anticipated inform development of hyperspectral water
quality monitoring tools for optically complex waters. This talk will detail methods for, and progress of, spectral
library development and approaches for inclusion of CDOM and NAP. Potential monitoring applications using
hyperspectral information collected from both in situ and satellite platforms will be discussed.
4. References
[1] P. J. Werdell et al. “The Plankton, Aerosol, Cloud, ocean Ecosystem (PACE) mission: status, science, advances.” B Am Meteorol Soc,
100(9), 1775-1794 (2019).
[2] NASA Press Release. NASA Targets Coastal Ecosystems with New Space Sensor (2019) https://www.nasa.gov/press-release/nasa-targetscoastal-ecosystems-with-new-space-sensor [Accessed: 2021-03-15].
[3] K. Cawse-Nicholson et al., “NASA's Surface Biology and Geology designated observable: A perspective on surface imaging algorithms.”
Remote Sens Environ, 257:112349 (2021).
[4] S.L. Palacios et al. “Remote sensing of phytoplankton functional types in the coastal ocean from the HyspIRI preparatory flight campaign.”
Remote Sens Environ, 167:269 – 280 (2015).
[5] C. B. Mouw et al. “A consumer's guide to satellite remote sensing of multiple phytoplankton groups in the global ocean.” Front Mar Sci, 4:41
(2017).
Acknowledgements: S.M. McKibben's research was supported by an appointment to the NASA Postdoctoral Program at the NASA Goddard
Space Flight Center, administered by Universities Space Research Association under contract with NASA.
