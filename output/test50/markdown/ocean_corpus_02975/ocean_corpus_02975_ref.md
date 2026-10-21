---
document_id: "epmc-pmc12243495"
title: "High-quality metagenomic-assembled genomes from sea ice and seawater of the Southern Ocean"
authors: ["Z. M. Buthelezi", "R. E. Pierneef", "O. K. I. Bezuidt", "T. P. Makhalanyane"]
publisher: "American Society for Microbiology (ASM)"
journal: "Microbiology Resource Announcements"
publication_year: 2025
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "trace_gases_microbial_biogeochemistry"
secondary_topics: []
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC12243495"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12243495/fullTextXML"
doi_or_report_id: "10.1128/mra.01298-24"
doi: "10.1128/mra.01298-24"
pmcid: "PMC12243495"
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-28"
language: "en"
---

## Abstract

We provide high-quality metagenome-assembled genomes (MAGs) derived from seawater and sea ice samples collected in the Southern Ocean. Several MAGs encode genes associated with dimethylsulfoniopropionate (DMSP) lyase activity and methane oxidation. This resource provides insights regarding the role of microbial communities in the production of key volatile compounds.

## ANNOUNCEMENT

The Southern Ocean (SO) supports essential ecosystem services, and there is strong evidence showing the central role of microbes as mediators of these processes (1–4). These microorganisms are subject to significant environmental shifts, particularly during winter, as SO waters transition to ice-covered states (5). Here, we report the taxonomic classification and functional annotation of seven high-quality MAGs obtained from seawater and sea ice. Notably, some of these MAGs harbor functional genes linked to DMSP and methane metabolism.

Two surface seawater and two ice-core samples were collected during the Southern oCean seAsonaL Experiment (SCALE) winter cruise (July 11–31, 2022) aboard the RV SA Agulhas II. Seawater samples (20 L each) were obtained using the underway system and Niskin water bottles. Floating sea ice was collected using a net deployed from the ship’s aft crane. Ice cores were then sampled and stored at 4°C for thawing, resulting in 2 L of meltwater per core. These samples were filtered through 142 mm diameter isopore membrane filters (Merck, USA) to target the bacterioplankton size fraction, as previously described (6). DNA was extracted from these filters using the DNeasy PowerSoil Pro Kit (Qiagen, USA), following the manufacturer’s protocol (7). DNA quality was verified using the Qubit dsDNA Assay kit on a Qubit 4 Fluorometer (Thermo Fisher Scientific, USA), followed by 1% gel electrophoresis (8). Library preparation was performed for the four samples using the KAPA HyperPrep Kit (Roche, Switzerland) with a low-cycle PCR as detailed in the manufacturer’s protocol. Library quality and quantity were assessed using the Qubit 2.0 DNA High Sensitivity Assay (ThermoFisher, USA), Tapestation High Sensitivity D1000 Assay (Agilent Technologies, USA), and QuantStudio 5 System (Applied Biosystems, USA). Illumina 8-nt dual indices (Illumina, USA) were used for indexing and barcoding. Equimolar pooling of libraries was performed, based on QC values, prior to sequencing. Metagenomic sequencing was performed using the 2 × 150 bp sequencing chemistry NovaSeq platform (Illumina, USA), which was outsourced to Admera Health Biopharma Services, New Jersey, USA.

All analyses were performed using default parameters unless specified otherwise. The quality of raw reads was assessed using FastQC v1.15 (https://github.com/s-andrews/FastQC) (9). Low-quality reads and adapters were filtered using Trimmomatic v0.36 (10). Quality-filtered paired-end reads were assembled with metaSPAdes v3.15.5 (11), and assembly quality was evaluated using MetaQUAST v5.2.0 (12). Contigs ≥ 1,500 bp were used to reconstruct MAGs, by mapping quality-filtered reads to the assemblies using BBMap v38.95 (13). MetaBAT 2 v2.15 was used to generate bins as described previously (14), and the quality of these MAGs was assessed with CheckM v2 (15). Based on established criteria (16), seven high-quality MAGs (Table 1) were obtained and used for taxonomic classification using GTDB-TK v2.3.0 (17). These high-quality genomes are publicly available, and their annotation was carried out using the NCBI’s Prokaryotic Genome Annotation Pipeline (PGAP) (18). Identification of protein-coding genes for DMSP lyases and methane oxidation (19) was performed using eggNOG-mapper v2 (20) with DIAMOND v2.1.8 (21). The genome information, including isolation sources for the seven genomes, is summarized in Table 1.

**TABLE 1 — Information and quality report of seven MAGs together with four SRA accession numbers of their metagenomes**
| Genome ID | Genome accession no. | Organism | SRA accession | No. of Illumina reads | Source | Latitude (S) | Longitude (E) | Completeness (%) | Contamination (%) | Total length (bp) | GC content (%) | Total genes | Coding genes | tRNAs | ncRNAs | No. of contigs | Contig N50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OD-2 DCM_metabat.8 | JBIYRN000000000 | Oceanospirillaceae bacterium | SRX26916982 | 37,710,320 | Deep chlorophyll maximum | 58° 4 | 0° 6 4 | 99.54 | 0.13 | 2,247,091 | 45 | 2216 | 2159 | 41 | 4 | 163 | 26 kb |
| OD-2 DCM_metabat.25 | JBIYRM000000000 | Cellvibrionales bacterium | SRX26916982 | 37,710,320 | Deep chlorophyll maximum | 58° 4 | 0° 64 | 97.29 | 4.16 | 2,855,154 | 52 | 2659 | 2617 | 24 | 4 | 220 | 23.5 kb |
| OD-2 DCM_metabat.39 | JBIYRL000000000 | Halioglobus sp. | SRX26916982 | 37,710,320 | Deep chlorophyll maximum | 58° 4 | 0° 64 | 100 | 1.6 | 3,167,572 | 52 | 3051 | 3001 | 27 | 4 | 313 | 15.6 kb |
| IO-Ice_metabat.12 | JBIYRP000000000 | Pseudoalteromonas sp | SRX26916981 | 26,649,967 | Sea ice | 59° 41 | 0° 64 | 100 | 0.05 | 4,422,849 | 39 | 3942 | 3850 | 47 | 4 | 67 | 132.9 kb |
| IO-Ice_metabat.13 | JBIYRO000000000 | Polaribacter sp. | SRX26916981 | 26,649,967 | Sea ice | 59° 41 | 0° 64 | 97.73 | 1.01 | 2,506,219 | 35 | 2281 | 2240 | 32 | 4 | 214 | 19.4 kb |
| OD-2 ICE_metabat.1 | JBIYRK000000000 | Flavobacteriales bacterium | SRX26916983 | 38,490,889 | Sea ice | 58° 4 | 0° 64 | 96.62 | 1.69 | 3,049,849 | 32 | 2631 | 2593 | 30 | 3 | 15 | 355.5 kb |
| PUZ-DCM_metabat.5 | JBIYRJ000000000 | Opitutales bacterium | SRX26916984 | 27,225,834 | Deep chlorophyll maximum | 59° 99 | 0° 06 | 93.64 | 2.77 | 4,011,623 | 50 | 3785 | 3682 | 34 | 3 | 570 | 9.4 kb |
