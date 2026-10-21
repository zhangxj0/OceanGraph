---
document_id: "epmc-pmc10924396"
title: "Gene expression of Pocillopora damicornis coral larvae in response to acidification and ocean warming"
authors: []
publisher: "BMC"
journal: "BMC Genomic Data"
publication_year: 2024
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "ocean_acidification_carbonate"
secondary_topics: ["marine_nutrient_cycles"]
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC10924396"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10924396/fullTextXML"
doi_or_report_id: "10.1186/s12863-024-01211-3"
doi: "10.1186/s12863-024-01211-3"
pmcid: "PMC10924396"
license_status: "CC0"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

## Abstract

The endosymbiosis with Symbiodiniaceae is key to the ecological success of reef-building corals. However, climate change is threatening to destabilize this symbiosis on a global scale. Most studies looking into the response of corals to heat stress and ocean acidification focus on coral colonies. As such, our knowledge of symbiotic interactions and stress response in other stages of the coral lifecycle remains limited. Establishing transcriptomic resources for coral larvae under stress can thus provide a foundation for understanding the genomic basis of symbiosis, and its susceptibility to climate change. Here, we present a gene expression dataset generated from larvae of the coral Pocillopora damicornis in response to exposure to acidification and elevated temperature conditions below the bleaching threshold of the symbiosis.

This dataset is comprised of 16 samples (30 larvae per sample) collected from four treatments (Control, High pCO2, High Temperature, and Combined pCO2 and Temperature treatments). Freshly collected larvae were exposed to treatment conditions for five days, providing valuable insights into gene expression in this vulnerable stage of the lifecycle. In combination with previously published datasets, this transcriptomic resource will facilitate the in-depth investigation of the effects of ocean acidification and elevated temperature on coral larvae and its implication for symbiosis.

Keywords: Transcriptomics, Pocillopora damicornis, Coral larvae, Ocean warming, Acidification

## Objective

The symbiotic relationship between stony corals and their algal endosymbionts (Symbiodiniaceae) is the cornerstone underlying the productivity of coral reefs in the oligotrophic environment in the tropical ocean [1–4]. Yet, this dependence on symbiotic partners may prove to be the Achilles’ heel of corals in the Anthropocene [5]. Elevated temperature and acidification have the potential to perturb the symbiosis, leading to coral bleaching, mortality, and eventually reef degradation [6–8].

Studies of gene expression have proven valuable for detecting genes and signaling pathways underlying the disturbance of the symbiotic relationship between the coral host and its endosymbionts [9–11]. For example, studies on Stylophora pistillata revealed that heat stress alters the energy metabolism of the host, thereby promoting catabolic ammonium release and the destabilization of symbiotic nutrient recycling [12, 13]. However, most of our knowledge of gene expression in corals is based on studies of adult coral colonies [14–17]. In comparison, other stages of the coral lifecycle have received less attention to date.

Coral larvae represent a bottleneck in the reproduction of corals and have been suggested to be susceptible to elevated temperatures and ocean acidification [18, 19]. Larvae of the widespread brooding coral Pocillopora damicornis have emerged as powerful model systems to study the effects of future ocean conditions on gene expression of symbiotic larvae [9, 11, 20, 21]. Jiang et al. recently suggested that the bleaching threshold of P. damicornis larvae harboring the symbiont Durusdinium trenchi was between 32 and 33℃ [21]. Hence, we aimed to improve our understanding of the sub-bleaching stress response of P. damicornis larvae by studying the effects of acidification and warming on host and symbiont gene expression. Here, we present a transcriptomic dataset for 16 samples of coral larvae exposed to four treatments combing modulated pCO2 (450 or 1,000 µatm) and temperature (29 or 32℃) conditions (data file 1 [22]).

## Data description

### Sample collection

Detailed information on the larval collection and experimental setup was previously described in [22]. In brief, P. damicornis larvae were collected in Sanya, Hainan Island, China, on September 15, 2018, and pooled together for the subsequent experiments. Coral larvae were exposed to four different treatment conditions for 5 days, i.e., control, high pCO2, high temperature, combined. The mean temperatures for each treatment were 29.25 ± 0.01 (control, mean ± standard error, 28.90 ± 0.01 (high pCO2), 32.24 ± 0.01 (high temperature), and 31.86 ± 0.01 °C (combined). The mean pCO2 for each treatment was 465 ± 18 (control), 1012 ± 42 (high pCO2), 437 ± 16 (high T), and 966 ± 35 µatm (combined).

### RNA extraction, library construction and transcriptome sequencing

On day five of the experiment, thirty larvae (n = 4 replicates per treatment) were preserved in liquid nitrogen for RNA extraction. Total RNA of each larval sample was extracted using a TRIzol® Reagent RNA Isolation Kit (Invitrogen, Grand Island, NY, United States) following the manufacturer’s instructions. The concentration of total RNA was quantified using the Qubit BR RNA Assay Kit (Thermo Scientific), and its integrity was evaluated using an Agilent 2100 Bioanalyzer (Agilent Technologies), according to the manufacturer’s instructions. PolyA + selection and subsequent messenger RNA (mRNA) library preparation were done using the TruSeq Stranded mRNA Library Kit (Illumina), according to the manufacture’s instructions. All libraries were sequenced on the Illumina Hiseq X Ten platform to obtain paired-end reads with a length of 150-bp.

### Gene expression analysis

Sequences were quality trimmed and reads were split and aligned to the gene sequences of P. damicornis and D. trenchii respectively. This yielded 12–16.5 and 1.9–4.3 million mapped read pairs per sample for the host and Symbiodiniaceae (data file 1 [22]), respectively. Differential gene expression analysis revealed that high pCO2 alone had no significant effects on host gene expression (P < 0.05; Data file 1 [22]). In contrast, high temperature caused pronounced changes in host gene expression with 211 (16 upregulated vs. 195 downregulated) differentially expressed genes compared to control conditions (P < 0.05; Data file 1 [22]). Gene ontology (GO) enrichment analyses revealed that these changes in gene expression translated into 62 enriched GO terms under high temperature conditions (P < 0.05; Data file 1 [22]), including several processes related to development (e.g., lipoprotein metabolic process, protein autoprocessing, growth hormone receptor signaling pathway, cytolysis, regulation of growth, and negative regulation of cell population pathway). Similarly, combined high pCO2 and temperature treatment caused differential expression of 439 (274 upregulated vs. 165 downregulated) host genes (P < 0.05; Data file 1 [22]). GO enrichment analysis further identified 15 significantly enriched GO terms under combined treatment conditions (P < 0.05; Data file 1 [22]), including several processed related to innate immunity (e.g., negative regulation of NF-kappa B transcription factor activity, innate immune response, regulation of apoptotic process). Symbionts showed 8 (5 upregulated vs. 3 downregulated) differentially expressed genes in response to high pCO2 conditions (P < 0.05; Data file 1 [22]). GO enrichment analysis further identified 18 enriched GO terms under high pCO2 conditions (P < 0.05; Data file 1 [22]), including several processes related to catabolism (e.g., cellulose catabolic process, protein catabolic process, polysaccharide catabolic process). High temperature conditions caused differential expression of 40 (18 upregulated vs. 22 downregulated) algal symbiont genes (P < 0.05; Data file 1 [22]). GO enrichment analysis further identified 51 enriched GO terms under high temperature conditions (P < 0.05; Data file 1 [22]), including several processes related to cellular transport (e.g., proton tranmembrane transport, transmembrane transport, ammonium transmembrane transport). Lastly, combined high pCO2 and temperature conditions caused differential expression of 14 (8 upregulated vs. 6 downregulated) algal symbiont genes (P < 0.05; Data file 1 [22]). GO enrichment analysis identified 28 enriched GO terms under combined treatment conditions (P < 0.05; Data file 1 [22]), including several processes related to cellular nitrogen metabolism (e.g., glutamine metabolic process, L-alanine catabolic process, cellular nitrogen compound metabolic process).

## Limitations

P. damicornis larvae usually settle around 7 days after their release. As such, the experimental time frame did not permit a gradual acclimation of larvae to the treatment conditions. Identified transcriptomic response may thus include acute stress response arising from a lack of acclimation by the larvae.

## Acknowledgements

We also thank the staff of Tropical Marine Biological Research Station in Hainan for providing technical assistance and facilities for conducting the work.

## Author contributions

Youfang Sun, Yi Lan, Nils Rädecker, Pei-Yuan Qian, and Hui Huang conceived and designed the study. Youfang Sun and Huaxia Sheng conducted the experiments. Yi Lan and Nils Rädecker provided bioinformatics assistance and analysis. Pei-Yuan Qian, Guillermo Diaz-Pulido, and Hui Huang contributed to lab analysis and interpretation of the results. Youfang Sun, Huaxia Sheng, Yi Lan, and Nils Rädecker analyzed the data and drafted the manuscript. All authors commented on the draft and gave final consent for publication.

## Funding

This work was supported by grants from the National Natural Science Foundation of China (42206153 and 41906040), Science and Technology Projects in Guangzhou (2023A04J0200), Natural Science Foundation of Guangdong Province, China (2023A1515010810), Science and Technology Planning Project of Guangdong Province, China (2023B1212060047), Southern Marine Science and Engineering Guangdong Laboratory (Guangzhou) (2021HJ01, SMSEGL20SC01), and Visiting Fellowship Program of the State Key Laboratory of Marine Environmental Science (Xiamen University) (MELRS2302).

## Data availability

All raw sequencing reads of the coral P. damicornis are available in the NCBI Sequence Read Archive under BioProject accession number SRR24750928-SRR11802621 and PRJNA976470 (https://identifiers.org/bioproject:PRJNA976470). In addition, results of differential gene expression and gene ontology enrichment analysis are available via FigShare (10.6084/m9.figshare.24474484.v4). Please see Table 1 and references [22, 23] for details and links to the data.

**Table 1 — Overview of data files/data sets**
| Label | Name of data file/data set | File types (file extension) | Data repository and identifier (DOI or accession number) |
| --- | --- | --- | --- |
| Data file 1 | Sun_et al_GeneExpressionData | MS Excel file (.xlsx) | Figshare (10.6084/m9.figshare.24474484.v4) [22] |
| Data file 2 | Sun_et al_DetailedMethods | MS Word file (.docx) | Figshare (10.6084/m9.figshare.24474484.v45) [22] |
| Data set 1 | Transcriptomic dataset for larval P. damicornis | FASTQ files (.fastq) | NCBI Sequence Read Archive (https://identifiers.org/bioproject:PRJNA976470) [23] |

## Declarations

### Ethics approval and consent to participate

Not applicable.

### Consent for publication

Not applicable.

### Competing interests

The authors declare that they have no competing interest.

## Footnotes

## Contributor Information

Pei-Yuan Qian, Email: boqianpy@ust.hk.

Hui Huang, Email: huanghui@scsio.ac.cn.

## References

## Associated Data

### Data Availability Statement

All raw sequencing reads of the coral P. damicornis are available in the NCBI Sequence Read Archive under BioProject accession number SRR24750928-SRR11802621 and PRJNA976470 (https://identifiers.org/bioproject:PRJNA976470). In addition, results of differential gene expression and gene ontology enrichment analysis are available via FigShare (10.6084/m9.figshare.24474484.v4). Please see Table 1 and references [22, 23] for details and links to the data.

**Table 1 — Overview of data files/data sets**
| Label | Name of data file/data set | File types (file extension) | Data repository and identifier (DOI or accession number) |
| --- | --- | --- | --- |
| Data file 1 | Sun_et al_GeneExpressionData | MS Excel file (.xlsx) | Figshare (10.6084/m9.figshare.24474484.v4) [22] |
| Data file 2 | Sun_et al_DetailedMethods | MS Word file (.docx) | Figshare (10.6084/m9.figshare.24474484.v45) [22] |
| Data set 1 | Transcriptomic dataset for larval P. damicornis | FASTQ files (.fastq) | NCBI Sequence Read Archive (https://identifiers.org/bioproject:PRJNA976470) [23] |
