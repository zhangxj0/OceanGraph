---
document_id: "epmc-pmc8759385"
title: "Draft Genome Sequences of Sulfurovum spp. TSL1 and TSL6, Two Sulfur-Oxidizing Bacteria Isolated from Marine Sediment"
authors: []
publisher: "American Society for Microbiology (ASM)"
journal: "Microbiology Resource Announcements"
publication_year: 2022
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "trace_gases_microbial_biogeochemistry"
secondary_topics: ["ocean_acidification_carbonate"]
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC8759385"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8759385/fullTextXML"
doi_or_report_id: "10.1128/mra.00922-21"
doi: "10.1128/mra.00922-21"
pmcid: "PMC8759385"
license_status: "CC-BY"
license_url: "https://creativecommons.org/licenses/by/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

## Abstract

Sulfurovum spp. TSL1 and TSL6 are sulfur-oxidizing chemolithoautotrophic bacteria isolated from the tsunami-launched marine sediment in the Great East Japan earthquake. This announcement describes the draft genome sequences of the two isolates that possess the gene sets for the sulfur oxidation pathway.

## ANNOUNCEMENT

An epsilonproteobacterial genus, Sulfurovum, mainly inhabiting deep-sea hydrothermal vents, is a group of sulfur-oxidizing chemolithoautotrophs governing the biogeochemical cycling of elements in seafloor ecosystems (1–5). A large amount of marine sediment was launched on land by a tsunami that occurred in the Great East Japan earthquake, and thereafter, the Sulfurovum-affiliated bacteria participated in sulfur oxidation when the marine sediment was exposed to oxic conditions (6). Two sulfur-oxidizing bacteria, TSL1 and TSL6, were isolated from the marine sediment (38°25′N, 141°14′E; Higashimatsushima, Miyagi, Japan). Briefly, the sediment was preincubated aerobically for 3 days and then incubated using serial dilution in basal salts of MJ medium (7) supplemented with a vitamin solution containing biotin, folic acid, pyridoxine hydrochloride, thiamine hydrochloride, riboflavin, nicotinic acid, DL-calcium pantothenate, vitamin B12, p-aminobenzoic acid, and lipoic acid (8), and thiosulfate or elemental sulfur as an energy source. After repeating serial subcultivation 4 to 7 times, TSL1 and TSL6 were obtained as pure cultures using the thiosulfate and elemental sulfur as energy source, respectively. Based on 16S rRNA gene sequences (Fig. 1), these two bacteria could represent the undescribed Sulfurovum species. Here, we sequenced the genomes of these bacteria to reveal the genetic features underlying their biogeochemical activities.

**Figure caption:** FIG 1 — Phylogenetic relationship of TSL1 and TSL6 with the representative strains in the genera Sulfurovum, Nitratifractor, Arcobacter, Sulfurospirillum, and Sulfurimonas. Neighbor-joining phylogenetic tree (left) is reconstructed using near full-length 16S rRNA gene sequences, and bootstrap values (1,000 replicates) of more than 70% are indicated by solid circles at the branches. Heatmap (right) shows pairwise nucleotide identities of the near full-length 16S rRNA gene sequences. Column numbers below the heatmap indicate the bacterial strains as follows: 1, Sulfurovum lithotrophicum 42BKTT; 2, Sulfurovum sp. strain NBC371; 3, Sulfurovum riftiae 1812ET; 4, Sulfurovum indicum ST-419T; 5, Sulfurovum aggregans Monchim33T; 6, Sulfurovum denitrificans eps51T; 7, TLS1; 8, TSL6; 9, Nitratifractor salsuginis E9I37-1T; 10, Arcobacter nitrofigilis DSM 7299T; 11, Arcobacter canalis F138-33T; 12, Sulfurospirillum multivorans DSM 12446T; 13, Sulfurospirillum halorespirans PCE-M2T; 14, Sulfurospirillum barnesii SES-3T; 15, Sulfurospirillum deleyianum 5175T; and 16, Sulfurimonas autotrophica OK 10T. TSL1 and TSL6 shared 95.2% to 96.8% of the 16S rRNA gene identities with the type strains of type species in the genus Sulfurovum, indicating that the two strains can represent the undescribed species affiliated in the genus Sulfurovum.

TSL1 and TSL6 were aerobically grown in the above-mentioned medium supplemented with the vitamin solution, PIPES [piperazine-N,N′-bis(2-ethanesulfonic acid)] (20 mM), and sodium thiosulfate (20 mM) at room temperature for 2 to 3 weeks. Genomic DNA was isolated using a lysozyme buffer method (9). Paired-end libraries (insert size, ∼350 bp) were prepared using a VAHTS universal DNA library prep kit for Illumina (Vazyme Biotech) and sequenced using a HiSeq 2500 system (Illumina), which generated 8.9 and 11.1 million reads (2 × 150 bp) for TSL1 and TSL6, respectively. Adapters were removed using Cutadapt v3.1 (10), while the reads with a Q score of <30 were removed using Sickle v1.33 (https://github.com/najoshi/sickle). High-quality reads were preassembled using Unicycler v0.4.8 with default settings (11) and then assembled using SPAdes v3.15.0 (12) with the trusted-contigs tool, as previously described (13). The draft genomes were annotated by the DFAST v1.4.0 (14) and KofamKOALA v2021-07-05 (15). Whole-genome average nucleotide identity (ANI) and digital DNA-DNA hybridization (dDDH) between the two genomes were calculated using the JSpeciesWS (16) and GGDC v2.1 (17), respectively.

TSL1 had a genome size of 2,353,154 bp assembled into 6 contigs (N50 value, 1,782,176 bp; GC content, 40.7 mol%; coverage, 500×), while TSL6 had the genome size of 2,254,663 bp assembled into 7 contigs (N50 value, 760,548 bp; GC content, 38.4 mol%; coverage, 650×) (Table 1). A total of 2,359 genes were predicted as 3 rRNAs, 42 tRNAs, and 2,314 protein-coding sequences (CDSs) in the TSL1 genome, while there was a total of 2,259 genes as 3 rRNAs, 43 tRNAs, and 2,213 CDSs in the TSL6 genome (Table 1). The ANI and dDDH values between the two isolates were calculated to be 86.5% (aligned coverage, 75.9%) and 32.3%, respectively, which suggests that TSL1 and TSL6 can be classified into different species. Genome annotation revealed that both of the two bacteria possessed a sulfur oxidation system, which would be helpful to understand their roles in the acidification of the tsunami-launched marine sediment (6).

**TABLE 1 — Statistics for genome assemblies of Sulfurovum spp. TSL1 and TSL6**
| Characteristic | Data for: |  |
| --- | --- | --- |
| TSL1 | TSL6 |  |
| No. of contigs | 6 | 7 |
| N50 value (bp) | 1,782,176 | 760,548 |
| GC content (mol%) | 40.7 | 38.4 |
| Total length (bp) | 2,353,154 | 2,254,663 |
| Genome coverage (×) | 500 | 650 |
| Genome completeness (%) | 99.6 | 99.6 |
| No. of rRNAs | 3 | 3 |
| No. of tRNAs | 42 | 43 |
| No. of CDSs | 2,314 | 2,213 |
| GenBank accession no. | BPFI01000001 to BPFI01000006 | BPFJ01000001 to BPFJ01000007 |
| DRA accession no. | DRA011857 | DRA011856 |

### Data availability.

The draft genome sequences of Sulfurovum spp. TSL1 and TSL6 are available under the DDBJ/ENA/GenBank accession numbers BPFI01000001 to BPFI01000006 and BPFJ01000001 to BPFJ01000007, respectively. The raw reads are available under the DRA accession numbers DRA011857 and DRA011856 for TSL1 and TSL6, respectively.

## ACKNOWLEDGMENTS

This work was supported in part by commissioned research, “Work on the investigation regarding preservation measures for the mural paintings of Takamatsuzuka Tumulus, a national treasure,” from the Agency for Cultural Affairs, Japan.

## Contributor Information

Tomoyuki Hori, Email: hori-tomo@aist.go.jp.

Yoko Katayama, Email: katayama@cc.tuat.ac.jp.

Frank J. Stewart, Montana State University

## REFERENCES

## Associated Data

### Data Availability Statement

The draft genome sequences of Sulfurovum spp. TSL1 and TSL6 are available under the DDBJ/ENA/GenBank accession numbers BPFI01000001 to BPFI01000006 and BPFJ01000001 to BPFJ01000007, respectively. The raw reads are available under the DRA accession numbers DRA011857 and DRA011856 for TSL1 and TSL6, respectively.
