---
document_id: "epmc-pmc10457287"
title: "Vitamin B12 conveys a protective advantage to phycosphere-associated bacteria at high temperatures"
authors: []
publisher: "Oxford University Press"
journal: "ISME Communications"
publication_year: 2023
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "primary_production_phytoplankton"
secondary_topics: ["marine_nutrient_cycles", "trace_gases_microbial_biogeochemistry"]
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC10457287"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10457287/fullTextXML"
doi_or_report_id: "10.1038/s43705-023-00298-6"
doi: "10.1038/s43705-023-00298-6"
pmcid: "PMC10457287"
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

## Abstract

Many marine microbes require vitamin B12 (cobalamin) but are unable to synthesize it, necessitating reliance on other B12-producing microbes. Thus, phytoplankton and bacterioplankton community dynamics can partially depend on the production and release of a limiting resource by members of the same community. We tested the impact of temperature and B12 availability on the growth of two bacterial taxa commonly associated with phytoplankton: Ruegeria pomeroyi, which produces B12 and fulfills the B12 requirements of some phytoplankton, and Alteromonas macleodii, which does not produce B12 but also does not strictly require it for growth. For B12-producing R. pomeroyi, we further tested how temperature influences B12 production and release. Access to B12 significantly increased growth rates of both species at the highest temperatures tested (38 °C for R. pomeroyi, 40 °C for A. macleodii) and A. macleodii biomass was significantly reduced when grown at high temperatures without B12, indicating that B12 is protective at high temperatures. Moreover, R. pomeroyi produced more B12 at warmer temperatures but did not release detectable amounts of B12 at any temperature tested. Results imply that increasing temperatures and more frequent marine heatwaves with climate change will influence microbial B12 dynamics and could interrupt symbiotic resource sharing.

Subject terms: Microbial ecology, Microbial biooceanography

## Introduction

Vitamin B12 (cobalamin) is required by many marine bacteria and unicellular eukaryotes [1, 2] but is scarce throughout broad regions of the global ocean, forcing microbes that cannot synthesize B12 to rely on others that can [3, 4]. Many phytoplankton fulfill their B12 requirements through interactions with B12-producing bacteria in the phycosphere [5, 6]. Some phycosphere bacteria, like Ruegeria pomeroyi, are known B12 producers and require B12 for growth [6]. Other phycosphere inhabitants, like Alteromonas macleodii, cannot produce B12 and do not strictly require it for growth but benefit from its availability [7], potentially competing with phytoplankton for B12 as has been demonstrated for nitrate [8]. Climate-change-induced temperature increases will influence bacterial growth rates in the oceans [9], but it is unclear how temperature will impact B12 quotas and dynamics or downstream effects on microbial communities and interactions. We investigated how temperature stress interacts with B12 limitation in phycosphere residents with flexible (A. macleodii MIT1002) and absolute (R. pomeroyi DSS-3) B12 requirements and how temperature stress impacts production and release of B12 by a B12-producer (R. pomeroyi).

To determine the interaction effect of temperature and B12 availability on growth, A. macleodii and R. pomeroyi were grown in a minimal media prepared with (replete) and without (–B12) B12 across a range of temperatures from 15 °C to 40 °C (Supplementary Information; SI Table 1, SI Fig. 1). Lack of exogenous B12 significantly diminished A. macleodii growth at all temperatures, with the largest effect at the highest temperature (Fig. 1). A. macleodii biomass was reduced by 57% when grown without B12 at the highest temperature in trial 1 (Fig. 1B, SI Fig. 2), and by 22% in trial 2 (Fig. 1A, B). Withholding B12 also significantly decreased A. macleodii’s mean maximum growth rate (µmax; Trial 2): µmax decreased by 0.32 at the highest temperature (27%; p < 0.05), by 0.14 at the mid temperature (14%; p < 0.05), and by 0.13 at the cool temperature (18%; p < 0.05) (Fig. 1C). Cell size was largely stable across treatments, but a significant increase was observed at 24 h for cells grown without B12 at the highest temperature in both trials (SI Figs. 6, 7), which is consistent with a reduced growth rate [10] or an arrested cell cycle [11].

**Figure caption:** Fig. 1 — Growth parameters for Alteromonas macleodii and Ruegeria pomeroyi grown in replete minimal media and minimal media without a vitamin B12 source across a range of temperature treatments.A Growth curves for both species from experimental trial 2. Colors represent temperature treatments, with the exact temperature for each treatment included in the legend. Point and line shapes represent the media treatment: replete (replete minimal media; circles and solid lines) and –B12 (minimal media without vitamin –B12; triangles and dashed lines). Each point is the mean log cell concentration of three biological replicates determined by flow cytometry, with error bars representing one standard deviation of the mean. Black vertical lines indicated by arrowheads designate time points where R. pomeroyi cultures were harvested for B12 measurements by mass spectrometry. B Maximum cell concentrations (biomass) reached by A. macleodii in experimental trials 1 and 2. Horizontal marks represent the mean cell concentration for each treatment; vertical error bars are one standard deviation of the mean; open circles are individual data points. The statistical significance of media treatment at each temperature was tested by t-test and p < 0.05 is indicated on the plots by an asterisk (‘*’). There was a statistically significant reduction in maximum biomass by 57% and 22% in trials 1 and 2, respectively, when A. macleodii was grown without vitamin B12 at the hottest temperature tested. C Maximum growth rates (µmax) for A. macleodii and R. pomeroyi in each temperature and media treatment combination in experimental trial 2. Growth rates were calculated from individual growth curves using the ‘growthrates’ package in the R computing environment. The statistical significance of media treatment on mean maximum growth rate at each temperature was tested by t-test and p < 0.05 is indicated on the plots by an asterisk (‘*’). A. macleodii cultures grown in replete media had a significantly higher maximum growth rate at all temperatures but the difference in mean maximum growth rate (µmax) between media treatments was largest in the hot temperature treatment (0.32 (27%), compared to 0.14 (14%) in mid and 0.13 (18%) in cool). The impact of media treatment on maximum growth rate was more varied for R. pomeroyi with the maximum growth rate significantly higher in replete media only at the highest temperature treatment.

The observed changes in growth parameters suggest that B12 has a protective or growth-promoting effect in A. macleodii at high temperatures. While such observations have not been reported in prokaryotes, B12 is protective at high temperatures in the model unicellular eukaryotic alga, Chlamydomonas reinhardtii [12]. Like A. macleodii, the C. reinhardtii genome encodes B12-independent (MetE) and B12-dependent (MetH) methionine synthases, meaning it can grow with and without B12 [13]. However, exposing C. reinhardtii to high temperatures (39 °C) triggers heat shock, chlorosis, and death if B12 is unavailable [12]. If B12 is available, C. reinhardtii exhibits enhanced thermal tolerance, maintaining growth at 42 °C. At high temperatures, C. reinhardtii MetE had decreased activity, indicating MetH is more temperature-stable and suggesting a mechanism for thermal protection [12]. This may also hold true for A. macleodii. Methionine, however, conveyed a smaller boost in C. reinhardtii thermal tolerance than B12, advancing the hypothesis that B12 enhances thermal tolerance through additional pathways [12]. Notably, B12 increases growth in bacteria exposed to other stressors, including oxidative stress [14], low-temperature, and copper stress [15], demonstrating that methionine synthesis at higher temperatures is not the only growth-promoting benefit provided by B12 [16].

Exogenous B12 had a smaller effect on R. pomeroyi’s growth, presumably because it is a B12-producer. Withholding B12 did not impact the maximum biomass reached by R. pomeroyi at any temperature (SI Fig. 3) but did significantly decrease growth rates at the highest temperature (Fig. 1C). We detected elevated intracellular B12 levels in mid and hot temperatures compared to the cool treatment, although not statistically significant (Fig. 2). Thus, R. pomeroyi may produce more B12 at warmer temperatures to maintain similar biomass and growth rates as when exogenous B12 is supplied, but B12 synthesis cannot keep up with growth requirements at extremely high temperatures. This suggests B12 plays a similar growth-promoting or protective role in R. pomeroyi as observed for A. macleodii. In future studies, this could be tested by growing R. pomeroyi mutants incapable of synthesizing B12 at high temperatures and determining if growth is diminished when B12 is withheld. Of note, extracellular B12 was not detected in any of the warm or hot treatment replicates and only trace amounts were detected in two cool treatment replicates (Fig. 2). These results imply that little to no B12 is released by R. pomeroyi in our experimental conditions and that temperature does not have a measurable effect on B12 release. While many B12-producing bacteria do not release B12 [17], these results were surprising because R. pomeroyi fulfills the B12 requirement of the diatom Thalassiosira pseudonana when grown in co-culture [6]. While co-culture with T. pseudonana does not influence R. pomeroyi expression of the B12 biosynthetic pathway [6], our study suggests that a cue from symbiotic phytoplankton may be required for R. pomeroyi to release B12.

**Figure caption:** Fig. 2 — Concentrations of intracellular and extracellular vitamin B12 normalized to cell counts in Ruegeria pomeroyi cultures grown without an exogenous B12 source across three temperature treatments.R. pomeroyi cultures in early stationary phase were harvested for cyanocobalamin (B12) measurements by mass spectrometry. Measured values were normalized to the number of cells in the originating culture volume (i.e., the number of cells in a cell pellet or the number of cells removed from a supernatant). Horizontal marks represent the mean B12 concentration per cell for each treatment; vertical error bars are one standard deviation of the mean; open circles are individual data points. Pelleted cells contained significantly more B12 than was present in supernatants (p < 0.05, t-test). While not a statistically significant difference, cells grown in the mid and hot-temperature treatments tended to have higher intracellular vitamin B12 concentrations than cells grown in the cool-temperature treatment.

This study demonstrates that B12 conveys a protective or growth-promoting effect at high temperatures for two bacterial species commonly associated with phytoplankton. While the highest temperatures in the study are rare in the current global ocean, they are found in tide pools in subtropical and tropical regions [18], and summer sea surface temperatures (SST) in the Persian Gulf regularly exceed 37 °C [19]. Marine heatwaves—such as the 2023 heatwave affecting the Florida Keys, the Bahamas, and Cuba that caused SST to reach 38 °C (ndbc.noaa.gov)—are expected to become more frequent and severe due to climate change [20]. Our results suggest that increasing temperatures will increase the biochemical need for B12 among marine microbial consortia. Shifting B12 dynamics may impact symbiotic relationships that sustain phytoplankton and other organisms. Future work should investigate protective mechanisms for B12 in marine microbes and the impact of inter-species interactions on B12 production and release with changing temperatures.

## Supplementary information

## Acknowledgements

MMB is supported by a Simons Foundation Postdoctoral Fellowship in Marine Microbiology (award 874439). HA is supported by a Simons Foundation Early Career Investigator in Aquatic Microbial Ecology and Evolution Award (award 931886). AS was supported by the Community College Research Experiences in Woods Hole program (CC-CREW; NSF award ICER-2023192). MAS and MRM were supported by the Simons Foundation, NIH award GM135709-01A1, and NSF award 1850719. AIK was supported by the U.S. Department of Energy, Office of Science, Office of Advanced Scientific Computing Research, Department of Energy Computational Science Graduate Fellowship under Award Number DE-SC0020347. Support for this project also came from the NSF Center for Chemical Currencies of a Microbial Planet (C-CoMP NSF-STC 2019589). We thank Julie Huber and Gretta Serres for organizing and facilitating the CC-CREW program. We thank Erin McParland and Liz Kujawinski for providing the bacterial strains used in this study.

## Author contributions

MMB, HA, and MAS designed the experiments. MMB, AS, and MRM performed experiments and collected data. MMB and AIK analyzed data. MMB wrote the manuscript with input from all authors.

## Data availability

The raw flow cytometry data generated for this project are publicly available from 10.5281/zenodo.8133026. Vitamin B12 mass spectrometry data, intermediate data products, and code used for this study are available in the GitHub repository https://github.com/maggimars/bactB12. The full analysis pipeline is further available as an interactive document: https://maggimars.github.io/bactB12/Flow_Cytometry_Analysis.html.

## Competing interests

The authors declare no competing interests.

## Footnotes

## Contributor Information

Margaret Mars Brisbin, Email: mmarsbrisbin@usf.edu.

Mak A. Saito, Email: msaito@whoi.edu

## Supplementary information

The online version contains supplementary material available at 10.1038/s43705-023-00298-6.

## References

## Associated Data

### Supplementary Materials

### Data Availability Statement

The raw flow cytometry data generated for this project are publicly available from 10.5281/zenodo.8133026. Vitamin B12 mass spectrometry data, intermediate data products, and code used for this study are available in the GitHub repository https://github.com/maggimars/bactB12. The full analysis pipeline is further available as an interactive document: https://maggimars.github.io/bactB12/Flow_Cytometry_Analysis.html.
