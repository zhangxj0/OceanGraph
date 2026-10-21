---
document_id: "nasa-technical-reports-server-98b5e664c47230b5"
title: "Exploring Climatology and Long-Term Variations of Aerosols from NASA Reanalysis MERRA-2 with Giovanni"
authors: ["Shen, Suhung", "Ostrenga, Dana", "Vollmer, Bruce", "Li, Zhanqing"]
publisher: "NASA"
journal: ""
publication_year: 2019
document_type: "technical_report"
domain: "carbon_biogeochemistry"
subdomain: "marine_nutrient_cycles"
secondary_topics: ["marine_organic_matter", "trace_gases_microbial_biogeochemistry"]
source_platform: "NASA Technical Reports Server"
source_url: "https://ntrs.nasa.gov/citations/20160000956"
download_url: "https://ntrs.nasa.gov/api/citations/20160000956/downloads/20160000956.pdf"
doi_or_report_id: "nasa-ntrs:20160000956"
doi: ""
pmcid: ""
license_status: "NASA-PUBLIC-USE-PERMITTED"
license_url: "https://sti.nasa.gov/disclaimers/"
accessed_at: "2026-07-29"
language: "en"
---

Poster: #415
AMS 2016
New Orleans, Louisiana
January 10-14 2016
NASA/Goddard EARTH SCIENCES DATA and INFORMATION SERVICES CENTER (GES DISC)
Exploring Climatology and Long-Term Variations of Aerosols from NASA Reanalysis MERRA-2 with Giovanni
Suhung Shen1,2 , Dana Ostrenga1,3, Bruce Vollmer1, Zhanqing Li4
Description of Data Access Methods and Examples
suhung.shen@nasa.gov 1NASA Goddard Space Flight Center, 2George Mason University, 3ADNET, 4University of Maryland
About MERRA-2 Aerosol Products
Data Services
MERRA-2 Aerosol Products
File Specification: http://gmao.gsfc.nasa.gov/pubs/docs/Bosilovich785.pdf
Aerosol Components: Dust, Black Carbon
Finding Data: UUI
Subsetting: MERRA Subsetter
http://disc.sci.gsfc.nasa.gov/daac-bin/FTPSubset2.pl
http://disc.sci.gsfc.nasa.gov/uui/#/search/”MERRA+aerosol”
Product ShortName
Sample Parameters
Temporal
Resolution
(BC), Organic Carbon(OC), Sea-salt, Sulfate
(SO4)
Products
Description
Parameter, spatial, temporal subsetting
Regridding (bilinear interpolation, nearest
Aerosol Property: mixing ratio, column mass
Hourly
Monthly Diurnal
Monthly
neighbor, distance-weighted average, …)
Resolution (gpcp2.5, cfsr1.0, ERA40, …)
Data Format (netCDF4, NetCDF4-classic)
M2T1NXAER (tavg1_2d_aer_Nx )
M2TUNXAER (tavgU_2d_aer_Nx)
M2TMNXAER (tavgM_2d_aer_Nx)
Product Landing Page
density, emission, optical depth, deposition,
sedimentation, etc.
Aerosol Diagnostics
SO2 Column Mass Density
Dust Surface Mass Concentration
Dust Surface Mass Concentration -PM 2.5
Total Aerosol Extinction AOT at 550nm
Total Aerosol Scattering AOT at 550nm
Model: MERRA-2 (based on MERRAero,
Aerosol Diagnostics
(extended)
Hourly,
Monthly Diurnal
Monthly
M2T1NXADG (tavg1_2d_adg_Nx)
M2TUNXADG (tavgU_2d_adg_Nx)
M2TMNXADG (tavgM_2d_adg_Nx)
Spatial
aerosol components are fully coupled with
meteorological fields)
Dust Dry/Wet Deposition
Dust Emission
Dust Sedimentation
Black Carbon Biomass Burning Emissions
SO2 Biomass Burning Emissions
Assimilation Inputs: MODIS, MISR,
Temporal
Aerosol Optical Depth Analysis
Aerosol Optical Depth Analysis Increment
AERONET, and AVHRR (pre-EOS period)
Aerosol Optical Depth
Analysis
Visualization: Giovanni
http://giovanni.gsfc.nasa.gov/Giovanni/
3-hourly
Monthly Diurnal
Monthly
M2I3NXGAS (inst3_2d_gas_Nx)
M2IUNXGAS (instU_2d_gas_Nx)
M2IMNXGAS (instM_2d_gas_Nx)
Parameter
Temporal Coverage: 1980-present
3-hourly
M2I3NVAER (inst3_3d_aer_Nv)
Temporal Resolution: hourly, 3-hourly,
Aerosol Mixing Ratio
(3D - L72)
monthly, and monthly diurnal
Dust Mixing Ratio
SO2 Mixing ratio
Hydrophilic /Hydrophobic Black Carbon
Methanesulphonic acid
Spatial Coverage: Global
Other Data Services:
HTTP (for direct downloading)
OPeNDAP
GDS
NASA centralized Earth Data search
3-hourly
M2I3NVGAS (inst3_3d_gas_Nv)
Spatial Resolution: 0.5ox0.625o
system (http://reverb.echo.nasa.gov)
Data Recipes (step-by-step instruction
Aerosol Mixing Ratio
Analysis Increments
(3D - L72)
Dust Mixing Ratio Analysis Increments
Sulfate Mixing Ratio Analysis Increments
Black Carbon Mixing Ratio Analysis
Increments
on reading data with varies data tools)
Data Format: NetCDF-4
Monthly Climatology of Aerosols
Example Dust Storm from Asia to North America
Interannual Variations of Aerosols
(Base period: 1980-2014)
All-Dry-Bins , Global mean
2001.04.04 00Z
Scattering AOT 550nm
Jan
Dust Wet Deposition
Jan
2001.04.06 00Z
Right: Example monthly
climatology: aerosol
scattering AOT at 550 nm
and Dust wet deposition
for Jan, Apr, Jul, and Oct,
respectively. The average
is made for 35 years period
from 1980-2014.
2001.04.08 00Z
Scattering AOT 550nm
Apr
Apr
Dust Wet Deposition
Above: True color image
from MODIS, the famous
“Perfect Dust Storm” on
April 7 2001 over Northeast
China. Courtesy:
http://earthobservatory.nasa.gov/IO
TD/view.php?id=8341)
All-Wet-Bins , Global mean
The dust depositions are
available as dry and wet at
five dust particle size bins
in the range from 0.1 to 10
(μm) in radius.
2001.04.10 00Z
Right: Time series of
global mean dust
deposition for April
(blue line) and July
(black line) from 1980
to 2014. Both Wet and
Dry dust deposition
show systematic
difference before and
after about year 2000.
More studies are
needed to investigate
if it is a real signal or
the artifact due to
different input satellite
data.
Scattering AOT 550nm
Jul
Dust Wet Deposition
Jul
Jul
2001.04.12 00Z
(Images are generated with
Giovanni plot function: “Maps:
User Defined Climatology”. This
function enables monthly
climatology calculation of user
selected base-periods.)
(Plots are generated with
Giovanni function: “Time
Series: Seasonal”. This
function is able to plot time
series for an interested month
or season over a desired
region.)
Left: MERRA-2 assimilated
hourly column dust mass
density, the dust travels
eastward from Asia across the
Pacific reaching California
and even Maryland in about
6-10 days.
(Images are generated with
Giovanni plot function: “Maps:
Time Averaged Map”. This
function is able to plot time
averaged map over an interested
region.)
Scattering AOT 550nm
2001.04.14 00Z
Oct
Oct
Dust Wet Deposition
Acknowledgements:
We are grateful to Giovanni team for helping to integrate MERRA-2
data into the system; to Dr. Arlindo Da Silva from NASA GMAO for
review and comments.
References:
Bosilovich, M. G., R. Lucchesi, and M. Suarez, 2015. MERRA-2: File Specification. GMAO Office Note No. 9, http://gmao.gsfc.nasa.gov/pubs/docs/Bosilovich785.pdf
Colarco, P., A. Da Silva, M. Chin, and T. Diehl (2010), Online simulations of global aerosol distributions in the NASA GEOS-4 model and comparisons to satellite and ground-based aerosol optical depth, J. Geophys. Res., 115, D14207, doi:10.1029/2009JD012820
da Silva, A. M., C. A. Randles, V. Buchard, A. Darmenov, P. R. Colarco, and R. Govindaraju, 2015. File Specification for the MERRA Aerosol Reanalysis (MERRAero). GMAO Office Note No. 7
