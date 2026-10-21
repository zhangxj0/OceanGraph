---
document_id: "nasa-technical-reports-server-75fbe63db0a6e3e6"
title: "Effects of Whitecaps on Satellite-Derived Ocean Color"
authors: ["Frouin, Robert"]
publisher: "NASA"
journal: ""
publication_year: 2019
document_type: "data_product_method_qc"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: []
source_platform: "NASA Technical Reports Server"
source_url: "https://ntrs.nasa.gov/citations/20010097639"
download_url: "https://ntrs.nasa.gov/api/citations/20010097639/downloads/20010097639.pdf"
doi_or_report_id: "nasa-ntrs:20010097639"
doi: ""
pmcid: ""
license_status: "NASA-PUBLIC-USE-PERMITTED"
license_url: "https://sti.nasa.gov/disclaimers/"
accessed_at: "2026-07-28"
language: "en"
---

NASA
Proposal
NAG5-6202
of Whitecaps
on Satellite-Derived
Principal
Investigator:
Robert
Frouin
Scripps
Institution
of Oceanography
La Jolla
Shores
Drive,
La Jolla,
92037
Tel:
858 534
(voice),
(fax)
Award
period:
September
1, 1997
- December
31, 2000
Final
Report

1. Summary
of Accomplishments
the
3.25
years
of
the
project
various
aspects
of
ocean-color
sensing
were
investigated,•
including
effect
of
whitecaps
on
correction,
validity
of
models,
and
evaluation
of
ocean-color
products.
Algorithms
to
estimate
concentration
and
photo-synthetically
active
(PAR)
were
developed,
and
studies
of
geophysical
phenomena,
such
as the
event,
were
performed.
The
of solar
absorption
by phytoplankton
on mixed
dynamics,
circulation,
and climate
was also
investigated.
The project's
results
and findings
are described
in the articles
listed
at the end
of the report.
The main
results
are summarized
below.
°
The
spectral
properties
of
whitecaps,
obtained
by
interpreting
aircraft
over
the
open
(NASA
AVIRIS
and
CNES
push
broom
radiometer),
appear
to
be
fairly
independent
of
environmental
conditions,
and
in
agreement
previous
in situ
observations
(refs.
and
21).
Consequently,
for
sensing
applications,
the spectral
dependence
of whitecap
may
be
represented
accurately
by a unique
formula.
This
simplifies
greatly
the
correction
of
whitecap
in atmospheric
correction
algorithms.
.
Whitecaps
were
found
to exert
a cooling
on the planet
by increasing
albedo
(ref.
19). The
direct,
globally
averaged
due
to whitecaps
was
estimated
to lie in the
range
0-14
Wm 2 with
a probable
value
of 0.03
Wm a. Though
small,
this
value
is not
negligible
compared
the
due
to
some
greenhouse
gases
and anthropogenic,
aerosols
since
pre-industrial
times.
Values
reach
0.7
Wm "2 in
the
Indian
summer,
indicating
a potentially
larger
importance
of whitecaps
on regional
and seasonal
scales.
Whitecap
on surface
albedo
should
be taken
into
account
explicitly
in the modeling
and
analysis
of climate
change.
°
Multi-layered
perceptrons
were
educated
to
retrieve
concentration
SeaWiFS-derived
marine
at 412,
443,490,
510,
and
nm
(refs.
7 and
14).
Learning
and
testing
perceptrons
was
accomplished
using
synthetic
data,
to which
was
added
realistic
correction
and
radiometric
noise.
The
perceptrons
approximate
well
the
complex,
non-linear
marine
and pigment
concentration;
they
are
also
able
to
filter
noise
efficiently.
Compared
standard
blue-green
ratio
algorithms,
perceptrons
provide
much
better
results.
The
effect
of atmospheric
correction
errors
is
reduced
by a factor
of 4-5.
4.
A simple,
yet
efficient
was
developed
to estimate
PAR
at the
(ref.
13).
The
utilizes
plane-parallel
theory
and
separates
the
clear
atmosphere
and
clouds.
PAR
is computed
as the
difference
the
400-700
nm
solar
energy
fluxes
incident
at the
top
of
the
-
atmosphere
(known)
and
reflected
back
to
space
by the
atrn_-sphere
(derived
:
-7
.

radiance),
taking
into
account
absorption.
Knowledge
of pixel
composition
is not
required,
eliminating
the
need
for
cloud
screening
and
arbitrary
assumptions
about
sub-pixel
cloudiness.
For
each
pixel,
clear
or cloudy,
a
daily
PAR
estimate
is obtained.
The
unknown
diurnal
variability
atmosphere,
especially
clouds,
is neglected.
The
results
were
verified
against
ISCCP
and
in
situ
fixed
buoys
in
the
equatorial
Pacific
and
the
Georgia
Strait,
Canada.
Agreement
the
ISCCP
and
estimates
was
generally
good,
root-mean-squared
differences
of
13.6
(32.6%),
5.7
(13.4%),
and
3.6
(8.4%)
on
daily,
weekly,
and
monthly
time
scales,
and
small
biases.
The
comparison
buoy
also
showed
good
agreement,
respective
inaccuracies
of 6.2
(15.0%),
3.7
(9.1%),
and
3.3
(8.1%)
Em2d
-' when
the
two
buoys
were
combined
(1387
daily
values).
The
good
statistical
performance,
even
on
a daily
time
scale,
makes
the
suitable
for
large-scale
studies
of aquatic
photosynthesis.
In fact,
the
was
used
in a major
study
of biospheric
primary
production
an
EI Nifio/La
Nifia
transition
(ref.
18).
5. Numerical
experiments
were
conducted
a
general
circulation
model
to
investigate
the
effect
of solar
absorption
by
on
sea
temperature
(SST).
The
vertical
profile
of
heating
rate
was
parameterized
as
a
of phytoplankton
concentration,
specified
in space
and
time
imagery.
The
dynamic
model
was
run
without
and
(control
and
anomaly
runs,
respectively),
and
the
difference
anomaly
and
control
runs
yielded
the
effect.
Due
to
the annual
amplitude
of
SST
increases
by
0.5
to
1 K in most
oceans,
positive
anomalies
summer
and
negative
anomalies
winter
(ref.
16). The
effect
is enhanced
in regions
of
shallow
mixed
(e.g.,
sub-tropical
gyres,
Mediterranean
Sea).
Persistent
negative
anomalies
reaching
2.5 K are obtained
in the
eastern
equatorial
Pacific,
and
are
explained
by
a shoaling
of
the
isotherms
toward
the
equator,
anomalous
geostrophic
currents
north
and
south
equator,
and
a strengthening
of
the
equatorial
undercurrent
(refs.
and
17).
The
SST
response
to the large
concentration
increase
in the Arabian
Sea during
fall
is
dampened
by
reduced
incoming
solar
(refs.
15 and
16).
On
a global
and
annual
scale,
SST
is higher
by 0.04
K (0.07
in the
Northern
Hemisphere
and
0.02
K
in the
Southem
Hemisphere).
The
resulting
impact
on climate,
locally
and
remotely,
is expected
to be significant.
.
It was
shown
that
may
exert
a significant
warming
on
the
planet,
not
only
by redistributing
heat
in the
upper
ocean,
but
by decreasing
albedo
(ref.
25).
Compared
the case
of pure
seawater,
the globally
and
annually
averaged
outgoing
flux
is decreased
by a probable
value
of 0.25
Wm -2. This
value
corresponds
to about
20%
of the net radiative
by greenhouse
gases
and
anthropogenic
aerosols
since
pre-industrial
times,
including
indirect
effects.
The
relative
importance
of phytoplankton
is greater
on regional
and seasonal
scales,
values
reaching
-1.5
Wm 2 in coastal
zones
and high
latitudes
summer.
Spatial
and
temporal
variability
of the forcing
is however
affected
by phytoplankton

•
.
g*
type,
some
reflective
species
increa_irlg
the
outgoing
flux.
An
increase
in
abundance
associated
enhanced
(e.g.,
artificial)
pumping
of atmospheric
carbon
dioxide
might
not
decrease
warming
as much
as expected
(due
to increased
heating
of the upper
ocean).
2. Publications
supported
by NASA
Grant
NAG5-6202
1.
Swindling,
M.,
P.-Y.
Deschamps,
and R. Frouin,
1998:
Verification
of aerosol
models
for
sensing.
103,
24919-24935.
.
Fougnie,
B.,
P.-Y.
Deschamps,
and
1999:
Vicarious
calibration
of
the
POLDER
spectral
bands
using
in-situ
measurements.
1EEE
Trans.
Geos.,
Rein.
Sen.,
37,
1567-1574.
.
Fougnie,
B.,
R.
P.
Lecomte,
and
P.-Y.
Deschamps,
1999:
Reduction
of
skylight
reflection
in
the
above-water
measurement
of
marine
diffuse
reflectance.
Appl.
Opt.,
38,
3844-3856.
.
Nakajima,
T.,
A.
Higurashi,
K.
Aoki,
T.
Endoh,
H.
Fukushima,
M.
Toratani,
Y.
Mitomi,
B. G.
Mitchell,
and
1999:
Early
phase
analysis
of OCTS
radiance
for aerosol
sensing.
IEEE
Trans.
Geos.,
Rem.
Sen.,
37,
1575-1585.
5.
Tratt,
D. M.,
and
D. L. Westphal,
1999:
A Southern
perspective
April
trans-Pacific
event.
Proc.
10 'h Conference
on
Coherent
Laser
radar,
Mt.
Hood,
Oregon,
June
28- July 2,
1999,
137-140.
6.
Iacobeltis,
S. F.,
and
R. C. J. Somerville,
1999:
Direct
climate
by
biomass-burning
aerosols:
Impact
of
correlation
controlling
variables.
J.
104,
12031-12045.
7.
Gross,
L.,
S.
Thiria,
and
R.
i999:
Applying
artificial
neurol
network
methodology
to ocean
sensing.
Ecological
Modelling,,
120,
237-246.
8.
R.,
H.
Kawamura,
and
M.
Kishino,
Eds.,
2000:
HyperspectraI
Sensing
of the ocea n, SPIE
Vol.
4154,
252 pp.
. Frouin,
R.,
and
P.-Y.
Deschamps,
2000:
AVIRIS
of
spectral
characteristics
of
whitecaps.
In Hyperspectral
Sensing
of
the
Ocean,
H. Kawamura,
and M. Kishino,
Eds.,
SPIE
Vol.
4154,
41-48.
10 .Chen
W.-Z.,
H.
Fukushima,
and
R.
2000:
GLI
correction
algorithms:
performance
test
GLI
synthetic
set.
In HyperspectraI
Sensing
Ocean,
R.
H.
Kawamura,
and
M.
Kishino,
Eds.,
SPIE
Vol.
4154,
49-56.

11.Flamant,C.,J.Pelon,P.Chazette,V. Trouillet, P.Quinn,R. Frouin,D. Bruneau,J.-F.
Leon, T. Bates,J. Johnson,andJ.Livingston,2000:Airborne lidar measurementsof
aerosolspatialdistribution andopticalpropertiesoverthe Atlantic Oceanduring an
Europeanpollution outbreakduringACE-2. Tellus,
52B,
652-677.
12. Higurashi,
A.,
T. Nakajima,
B. H. Holben,
A.
Smirnov,
and
B. Chatenet,
2000:
climatology
2-channel
AVHRR
sensing.
J.
Climate,
13, 2011-2027.
13. Frouin,
R.,
B. Franz,
and
M. Wang,
2000:
to estimate
PAR
data.
Version
1.2 -
Documentation.
Available
at the
following
web
page
address,
http://orca.gsfc.nasa.gov/seawifs/par/doc/seawifs_.par_wfigs.pdf.
14. Gross,
L., Thiria,
S., R. Frouin,
and
B. G. Mitchell,
2000:
Artificial
neural
networks
for
modeling
the
transfer
mearine
and
concentration.
105,
3483-3495.
15. Nakamoto,
S.,
S. Prasanna
Kumar,
J. M.
Oberhuber,
K.
Muneyama,
and
2000:
Chlorophyll
control
of sea
temperature
in the
Arabian
Sea
in a mixed
isopycnal
general
circulation
model.
Res.
Lett.,
27,
747-750.
16. Frouin,
R.,
S. Nakamoto,
A. Paci,
A. J. Miller,
and
S. F. Iacobellis,
2000:
modulation
of sea
temperature.
Proc.
ofPORSEC,
Goa,
India,
5-8 Dec.
2000,
Vol.
2, 498-501.
17. Nakamoto,
S.,
S. Prasanna
Kumar,
J. M. Oberhuber,
J. Ishizaka,
K.
Muneyama,
and
R.
2001:
Response
equatorial
pacific
of
chlorophyll
pigments
in a
mixed
layer-isopycnal
general
circulation
model.
Res.
Lett.,
28,
2021-2024.
i-ii_,_-
:-T :
18. Behrenfeld,
M.
J., J. T.
Randers0nl
C. R.
McClain,
G.
C. Feldman,
S. O.
Los,
C. J.
Tucker,
P. G. Faikowski,
C. B. Field,
W.
E. Esaias,
D. K.
Kolber,
and
N.
H.
Pollack
2001:
Biospheric
primary
production
and
ENSO
transition.
Science,
291,
2594-2597.
i:
: ' :_:::_ig.Frouin;
R.,
s.
F,
Iacobellis,
and
P2-Y_ Deschamps,
2001:
of
oceanic
i
whitecaps
on the global
budget.
Res.
Lett.,
28,
1523-1526.
20. Holben,
D. N.,
D.
Tanr6,
A.
Smirnov,
T.
F. Eck,
I. Slutsker,
N.
Abuhassan,
W.
W.
Newcomb,
J. S. Schafer,
B. Chatenet,
F. Lavenu,
Y. F. Kaufman,
J. Vande
Castle,
A.
Setzer,
B. Markham,
D.
Clark,
R. Halthore,
A. Karneli,
N.
T.
O'neill,
C.
Pietras,
R.
T.
Pinker,
K.
Voss,
and
G.
Zibordi,
2001:
An
emerging
ground-based
climatology:
depth
AERONET.
J.
106,
12067-12097.

21.Nicolas,J.-M.,P.-Y. Deschamps,andR. Frouin,2001:Spectralreflectanceof oceanic
whitecapsin the visible andnear-infrared:Aircraft measurementsover openocean.
Res.
Lett.,
in press.
22. Tratt,
D. M.,
and
D. L. Westphal,
2001:
The
April
event:
A Southern
perspective.
Jr. Geophys.
in press.
23. Husar,
R. B., D. Tratt,
D. Jaffe,
S. Gasso,
T. Gill,
N. S. Laulinen,
F. Fu,
M. Reheis,
Y.
Chun,
D.
Westphal,
B.
N.
Holben,
G.
Geymard,
I.
McKndry,
N.
Kuring,
G.
C.
Feldman,
C. R. McClain,
1. Merrill,
D. Dubois,
F. Vignola,
T. Murayama,
N.
Sugimoto,
S. Nickovic,
W. E. Wilson,
K. Sassen,
B. A.
Schichtel,
and
S. R. Falke,
2001:
The
event
of April
1998. J. Geophys.
Res.,in
press.
24.
Voss,
K.
J., E.
J. Welton,
P. K.
Quinn,
R.
M. Miller,
and
R. M.
Reynolds,
2001:
depth
the
Aerosols-99
experiment.
J.
in press.
25.Frouin,
R.,
and
S.
F.
Iacobellis,
2001:
of
on
the
budget.
in revision.
