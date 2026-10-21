---
document_id: "nasa-technical-reports-server-f50b12de87ff121a"
title: "Retrieval of Marine Water Constituents Using Atmospherically Corrected AVIRIS Hyperspectral Data"
authors: ["Bagheri, Sima", "Peters, Steef"]
publisher: "NASA"
journal: ""
publication_year: 2019
document_type: "data_product_method_qc"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: ["deoxygenation_hypoxia", "marine_organic_matter"]
source_platform: "NASA Technical Reports Server"
source_url: "https://ntrs.nasa.gov/citations/20050192442"
download_url: "https://ntrs.nasa.gov/api/citations/20050192442/downloads/20050192442.pdf"
doi_or_report_id: "nasa-ntrs:20050192442"
doi: ""
pmcid: ""
license_status: "NASA-PUBLIC-USE-PERMITTED"
license_url: "https://sti.nasa.gov/disclaimers/"
accessed_at: "2026-07-28"
language: "en"
---

Retrieval of Marine Water Constituents Using Atmospherically Corrected
AVIRIS Hyperspectral Data
Sima Bagheri1 and Steef Peters2
1. INTRODUCTION
This paper reports on the validation of bio-optical models in estuarine and nearshore (case 2) waters of New
Jersey-New York to retrieve accurate water-leaving radiance spectra and chlorophyll concentration from the
Airborne Visibile/Infrared Imaging Spectrometer (AVIRIS) imaging spectrometer data. MODTRAN-4 was applied
to remove the effects of the atmosphere so as to infer the water-leaving radiance. The study area - Hudson/Raritan of
New York and New Jersey (Figure 1) is an extremely complex estuarine system where tidal and wind-driven
currents are modified by freshwater discharges from the Hudson, Raritan, Hackensack, and Passaic rivers. Over the
last century, the estuarine water quality has degraded in part due to eutrophication, which has disrupted the preexisting natural balance, resulting in phytoplankton blooms of both increased frequency and intensity, increasing
oxygen demand, and leading to episodes of hypoxia. As the end result, a thematic map of chlorophyll-a
concentration was generated using an atmospherically corrected AVIRIS ratio image. This thematic map serves as
an indication of phytoplankton concentration. Such maps are important input into the geographic information system
(GIS) for use as a management tool for monitoring water resources.
Figure 1. Map of the study area with the locations of sampling stations
2. MATERIALS AND METHODS
The research was based on imaging spectrometer data from AVIRIS, field spectroradiometer, and water
samplings. Based on these measurements optical water quality models are constructed linking the water constituent
concentrations to (i) the inherent optical properties (IOP), using the specific inherent optical properties (SIOP), and
(ii) to the subsurface (ir) radiance reflectance (Bagheri and Dekker, 1999, and Bagheri et al., 2000 and 2001. A
simple optical water quality model was calibrated on measurements of optical water constituent concentrations and
inherent optical properties and used to simulate subsurface irradiance reflectance (or water leaving radiance). The
following is a brief description of the field/laboratory method used to establish the IOPs of the estuary for retrieval
of water quality concentrations from the AVIRIS data:
A) Upwelling and downwelling radiances/irradiances (Eu and Ed) were measured using the OL754 field
spectroradiometers. The goal was to parameterize the bio-optical model relating the CDOM, TSM and algal
1 New Jersey Institute of Technology
2 Vrije Universiteit, The Netherlands

pigment concentrations, to the light absorption and scattering and to the water leaving radiance, through direct and
laboratory based optical measurements. In short, the link between remotely sensed upwelling radiance and
underwater inherent optical properties is made through subsurface irradiance reflectance R(0-).
B) To estimate optically-important water quality parameters coincident with the R(0-)measurements, samples
(0.2 to 0.5 m depth) were taken for laboratory analysis. Standard procedures (Rijkeboer et al., 1998) were used to
determine concentrations of total chlorophyll-a (TCHL) defined as the sum of chlorophyll-a and phaeopigment (to
index phytoplankton abundance) and total suspended matter (TSM). TCHL and TSM were determined according to
the Dutch standard methods NEN 6520 (1981) and NEN 6484 (1982) respectively. TCHL varied between 22 mg m3 and 46 mg m-3 indicating that sampling did not coincide with any major phytoplankton bloom. Likewise, TSM (711 g m-3) was not remarkably high nor low for this time of year. Phytoplankton species were also identified and
enumerated in the samples for inclusion in the library spectra of the estuary.
C) The two IOPs measured directly were spectral absorption (a) and spectral beam attenuation (c), using an
Ocean Optics-2000. (Note: Use of this device for measuring IOPs is experimental and has not been referenced in the
published literature.)
Spectral scattering (b) was then deduced via subtraction of a from c (b=c-a).
A simple optical water quality model based on the work of Gordon (1975) was calibrated for measurements of
optical water constituent concentrations and inherent optical properties and used to simulate subsurface irradiance
reflectance (or water leaving radiance).
R(0-) = r (bb/(a+bb))
(1)
Where
a is the total absorption coefficient, bb is the backscatter coefficient
r is a factor based on the geometry of incoming light and volume scattering in the water.
The water constituents are expressed in their specific (per unit measurement) absorption and backscattering
coefficients:
a = aw+a*TSMTSM +a*phCHL+a*CDOMCDOM440
(2)
bb = bbw+bTSMTSM
The asterisks denote that a and bb are specific inherent optical properties (SIOP), i.e. per unit concentration denoted
by the subscript.
The inversion of such a model (using semi-analytical algorithms) can be used to characterize the estuarine
waters in terms of chlorophyll concentration, colored dissolved organic matter and total suspended matter from the
observed spectra. Validation of the concentration estimates by optical means and the AVIRIS atmospheric
correction is based on in situ measurements of spectra and concentrations.
3. SIMULATION MODELING AND RETRIEVAL TECHNIQUE
The AVIRIS images the earth's surface in 224 spectral bands approximately 10 nm wide covering 400-2500nm.
AVIRIS records the integrated effects of the solar source, the atmosphere and the targeted surface. To compensate
for the atmospheric effects, an atmospheric and air-water interface correction algorithm based on MODTRAN-4 was
utilized. MODTRAN is a radiative transfer model developed by US Air Force Geophysical Laboratory which
describes the radiative transfer process in the entire system from the solar source to the remote sensor via the
hydrosols. A quantitative treatment of radiative transfer and atmospheric correction is the only way to achieve
accurate (multi/hyperspectral) water leaving radiance measurements from satellite and airborne observations and to
obtain accurate estimates of concentrations of optical water constituents. The input atmospheric parameters used in
MODTRAN-4 were as follows:
Horizontal visibility = 20 km
Midlattitude summer atmosphere urban (5km) aerosol model
Solar zenith angle=55
Solar azimuth angle=83
Modtran 16 streams mode
O3 scaling factor = 2.0
The above parameters were applied to the spectra where in situ measurements were collected during the course
of the project (1999-2001). MODTRAN was able to bring the envelope of AVIRIS spectra reasonably close to

simulated spectra but the results dictated the reconstruction of the “true” values of the band ratio image (702/675)
based on chlorophyll field observation and measured SIOP (Figure 2). Results of Modtran are summarized as
follows:
1) There is considerable spectral noise
2) There are significant deviations in bands 675 and 702 nm
3) There are unexplained large differences in the blue and NIR
Figure 2. Measured SIOP were input into the forward Gordon model to simulate spectra at the Keyport Harbor (St5)
and Traid Bridge (St4) locations for comparison with AVIRIS spectra.
A semi-analytical CHL algorithm was applied to obtain a reasonable estimate of the spatial distribution of
CHL concentration (Figure 3). Atmospherically corrected ratio image of the AVIRIS was generated as a thematic
map to represent the spatial distribution of CHL concentration as indication of phytoplankton concentration
(Figure 4). The following is a summary of the procedures applied:
1) A CHL algorithm was fitted on simulated spectra
2) The ratio image (702/675 nm); based on atmospherically corrected AVIRIS bands) was scaled between
reasonable values based on a priori knowledge of possible CHL concentrations sampled at Keyport
Harbor (St5) and Traid Bridge (St4) sampling locations
3) The CHL algorithm was applied to the scaled ratio image to obtain the spatial distribution of CHL
concentration
The simulation modeling demonstrates the value of AVIRIS observations. The result of the analysis as shown
in Figure 3 can be summarized as follows:
1) Spectra below 500 nm are uncorrectable and unreliable.
2) The envelope of the spectra is quit irregular, indicating that there remains a substantial amount of sunglint
within the AVIRIS data.
3) The irregularity of the spectra is such that the balance between 670 and 700 nm observations seems to be
affected, making CHL determinations based on ratios difficult.
4) The general shape of the envelope and the range of values seem to be realistic for 500 and 750 nm.
Although normally the spectral maximum is observed around 550 nm, but in this case it is shifted to the
right.

Figure 3. The AVIRIS spectrum after atmospheric correction was scaled down with 20%. (Note: The scaling
difference may be due to many reasons, primarily due to the time difference between the measurements)
Figure 4. Bloom-like structure up the Raritan River as
depicted in AVIRIS atmospherically corrected ratio image
(702/675)

4. CONCLUSION
In our approach IOP of water constituents were used to model the reflectance. A reasonable fit was found
between modeled and measured R(0-) using the optical model and RT code.
We conclude that the AVIRIS spectral data provides the opportunity to distinguish the atmospheric effect from
the marine water effect to set the estimated turbidity for CHL concentration retrieval. Development of a robust
algorithm for simultaneous retrieval of atmospheric aerosol optical properties, CHL, CDOM and TSM is a very
challenging task. Nevertheless, such an algorithm is needed to make progress in this area. The model for the coupled
atmosphere-marine water provides the link between the spectra measured by the AVIRIS spectrometers and the in
situ measurements of spectral irradiances in the water.
5. ACKNOWLEDGEMENT
This project was funded by the National Science Foundation (BES-9806982). Support of the NASA
Headquarters and the AVIRIS Experiment Team is greatly appreciated.
6. REFERENCES
Bagheri, S., and Dekker A. Nearshore Water Quality Assessment Using Bio-Optical Modeling and Retrieval
Techniques, NASA and AVIRIS’99 Geoscience Workshop, JPL Publication 99-17, Jet Propulsion Laboratory,
Pasadena, California, February 8–12,1999.
Bagheri, S, Rijkeboer M, Pasterkamp R, and Dekker A. Comparison of the Field Spectroradiometers in preparation
for Optical Modeling, Proceedings of the Ninth Airborne Earth Science Workshop, JPL Publication 00-18, Jet
Propulsion Laboratory, Pasadena, California, February 23–27, 2000.
Bagheri, S. Stamnes, K and Li, W. Application of Radiative Transfer Theory to Atmospheric Correction of AVIRIS
Data, Proceedings of the Tenth Airborne Earth Science Workshop, JPL Publication 02-1, 2001.
Gordon, H. R., O. B. Brown and M. M. Jacobs, 1975. Computed Relationships between Inherent and Apparent
Optical Properties of a Flat Homogeneous Ocean. Appl. Optics, 14:417–427.
NEN 6484 (1982) Water: Determination of the content of not dissolved material and its ignition residue. Nederlands
Normalisatie instituut, Delft, The Netherlands (in Dutch).
NEN 6520 (1981) Water: Spectrophotometric determination of chlorophyll a content, Nederlands Normalisatie
instituut, Delft, The Netherlands (in Dutch).
Rijkeboer, M, Dekker, A.G., and Hoogenboom, H.J., 1998, Reflectance spectra with associated water quality
parameters measured in Dutch waters (Speclib-TK-database). Institute for Environmental Studies, E98/12, The
Netherlands.
