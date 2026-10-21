---
document_id: "epmc-pmc7141858"
title: "Link-HD: a versatile framework to explore and integrate heterogeneous microbial communities"
authors: ["Laura M Zingaretti", "Gilles Renand", "Diego P Morgavi", "Yuliaxis Ramayo-Caldas"]
publisher: "Oxford University Press"
journal: "Bioinformatics"
publication_year: 2020
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "trace_gases_microbial_biogeochemistry"
secondary_topics: []
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC7141858"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7141858/fullTextXML"
doi_or_report_id: "10.1093/bioinformatics/btz862"
doi: "10.1093/bioinformatics/btz862"
pmcid: "PMC7141858"
license_status: "CC-BY-NC"
license_url: "http://creativecommons.org/licenses/by-nc/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

## Abstract

We present Link-HD, an approach to integrate multiple datasets. Link-HD is a generalization of ‘Structuration des Tableaux A Trois Indices de la Statistique–Analyse Conjointe de Tableaux’, a family of methods designed to integrate information from heterogeneous data. Here, we extend the classical approach to deal with broader datasets (e.g. compositional data), methods for variable selection and taxon-set enrichment analysis.

The methodology is demonstrated by integrating rumen microbial communities from cows for which methane yield (CH4y) was individually measured. Our approach reproduces the significant link between rumen microbiota structure and CH4 emission. When analyzing the TARA’s ocean data, Link-HD replicates published results, highlighting the relevance of temperature with members of phyla Proteobacteria on the structure and functionality of this ecosystem.

The source code, examples and a complete manual are freely available in GitHub https://github.com/lauzingaretti/LinkHD and in Bioconductor https://bioconductor.org/packages/release/bioc/html/LinkHD.html.

## 1 Introduction

The reduction of ‘omics’ technology costs now enables collection of data from multiple sources. This allows researchers to simultaneously study several datasets and investigate their relationship with complex traits. The integration of these heterogeneous datasets is not trivial and several statistical methods have been developed to address this challenge (Argelaguet et al., 2018; Mariette and Villa-Vialaneix, 2018; Meng et al., 2014). In particular, the amalgamation of multiple microbial ecosystems poses unique challenges as these are compositional and sparse data. MixKernel (Mariette and Villa-Vialaneix, 2018) is a well-known tool designed to integrate heterogeneous datasets including microbial communities, but no method to perform a taxonomic enrichment analysis is available. Another popular integrative approach is MOFA (Argelaguet et al., 2018), however, it is unable to deal with compositional data.

Here, we present Link-HD, a tool to integrate and explore multiple microbial communities based on STATIS (Des Plantes, 1976), a family of multivariate methods to integrate multiple datasets. Link-HD generalizes STATIS with Regression Biplot (Ter Braak, 1997), clustering, differential abundance, enrichment taxonomic analysis and visualization tools. Link-HD analyzes distance tables computed from numerical, categorical, or compositional data as a generalization of multidimensional scaling (Abdi et al., 2007). Furthermore, Link-HD performs variable selection and can link the obtained common sub-space with phenotype information.

## 2 Materials and methods

Like STATIS, Link-HD aims to compare and analyze the relationships between datasets with a shared set of observations or variables. However, our package was specifically designed to integrate microbial communities and incorporate distances and transformations to deal with compositional data (Aitchison, 1982). The method is implemented in three main phases (Fig. 1).

- Inter-structure step: The algorithm first assesses the similarity between transformed distance tables using the vector correlation coefficient (Rv) (Escoufier, 1973), which can be interpreted as a general ‘vector covariance’ between matrices, i.e. this step evaluates similarity between the disparate datasets.
- Compromise step: Next, the ‘compromise’ matrix is calculated, which is a weighted sum of each cross-product matrix. This step involves an optimization problem since the weights are chosen to maximize the correlation between the compromise matrix and each individual component.
- Intra-structure step: Finally, the compromise matrix is evaluated through a Principal Component Analysis. The coordinates of the common elements are projected into a low rank space, where the relationships between them can be easily interpreted.

**Figure caption:** Fig. 1. — Link-HD Workflow. In the Inter-structure step, raw data are transformed using cumulative sum scaling or centered log ratio, and the correlation coefficient (Rv) is computed. The second step is the compromise (W) and, finally, the intra-structure step involves the Eigen-decomposition of W. Observations can be clustered and methods for selecting variables and association with phenotypes are available

Variable selection is tackled by two alternative approaches: (i) by projecting all the input variables into the compromise through a general Biplot formulation (Ter Braak, 1997); and (ii) by computing the differential abundance of features between clusters of samples. A novelty of Link-HD is its ability to aggregate the selected variables at several taxonomic levels and to establish whether that level is enriched using a cumulative hypergeometric distribution. This function also allows users to add a custom OTUs list. Finally, the SPIEC-EASI (Kurtz et al., 2015) tool can be used to visualize variable interactions.

## 3 Case studies

We illustrate our approach with rumen microbial (Ramayo-Caldas et al., 2019), TARA’s Ocean expedition (Sunagawa et al., 2015) and transcriptome NCI-60 cell line datasets (Reinhold et al., 2012).

In the rumen study, we integrated Bacteria, Archaea and Protozoa from 65 Holstein cows. Link-HD was able to reproduce previous results (Danielsson et al., 2017; Kittelmann et al., 2014; Ramayo-Caldas et al., 2019), showing a link between the structure of the rumen microbiota and CH4 emission. We also identify microbial markers associated to CH4. In the TARA’s example, Link-HD replicates the relevant role of temperature and Proteobacteria phyla on the structure of this ecosystem, as described in Mariette and Villa-Vialaneix (2018). Finally, we show the potential of Link-HD to integrate other omics layers by using transcriptome NCI-60 cell lines. Link-HD recapitulates the reported data structure (Meng et al., 2014) and ontology analysis reveals several cancer-related pathways.

In all, our results demonstrate that Link-HD is robust in combining several heterogeneous data types. A detailed description of these case studies and the theory behind Link-HD is available at https://lauzingaretti.github.io/LinkHD/ and in Bioconductor (https://bioconductor.org/packages/release/bioc/html/LinkHD.html).

## 4 Conclusions

We have developed an R package to integrate multiple microbial communities and other ‘omics’ layers combining a plethora of statistical methods in a fast, simple and flexible way.
