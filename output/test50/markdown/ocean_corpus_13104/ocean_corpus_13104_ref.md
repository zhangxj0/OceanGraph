---
document_id: "epmc-pmc6328299"
title: "Complete Genome Sequence of Novel Sulfitobacter pseudonitzschiae Strain SMR1, Isolated from a Culture of the Marine Diatom Skeletonema marinoi"
authors: ["Mats Töpel", "Matthew I.M. Pinder", "Oskar N. Johansson", "Olga Kourtchenko", "Adrian K. Clarke", "Anna Godhe"]
publisher: "Ivyspring International Publisher"
journal: "Journal of Genomics"
publication_year: 2019
document_type: "peer_reviewed_article"
domain: "carbon_biogeochemistry"
subdomain: "trace_gases_microbial_biogeochemistry"
secondary_topics: ["marine_nutrient_cycles", "primary_production_phytoplankton"]
source_platform: "Europe PMC"
source_url: "https://europepmc.org/articles/PMC6328299"
download_url: "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6328299/fullTextXML"
doi_or_report_id: "10.7150/jgen.30559"
doi: "10.7150/jgen.30559"
pmcid: "PMC6328299"
license_status: "CC-BY-NC"
license_url: "https://creativecommons.org/licenses/by-nc/4.0/"
accessed_at: "2026-07-29"
language: "en"
---

## Abstract

When studying diatoms, an important consideration is the role of associated bacteria in the diatom-microbiome holobiont. To that end, bacteria isolated from a culture of Skeletonema marinoi strain R05AC were sequenced, one of which being bacterial strain SMR1, presented here. The genome consists of a circular chromosome and seven circular plasmids, totalling 5,121,602 bp. After phylotaxonomic analysis and 16S rRNA sequence comparison, we place this strain in the taxon Sulfitobacter pseudonitzschiae on account of similarity to the type strain. The annotated genome suggests similar interactions between strain SMR1 and its host diatom as have been shown previously in diatom-associated Sulfitobacter, for example bacterial production of growth hormone for its host, and breakdown of diatom-derived DMSP by Sulfitobacter for use as a sulfur source.

## Introduction

The diatom groups of phytoplankton are responsible for around a fifth of the world's photosynthesis, as well as being an important component of marine food webs 1. As with other organisms, diatoms are found associated with a microbiome with which they can have beneficial interactions including exchange of nutrients, but also be exposed to adverse effects such as parasitism and algicidal activity 2. Growth of the diatom Skeletonema marinoi is impaired when attempts are made to culture it axenically (Johansson et al., unpublished data), highlighting the importance of the microbiome, and so efforts are being made to identify these associated bacteria, in order to better understand the roles they may play in aiding, or indeed hindering, S. marinoi's growth.

The culture of the host diatom, S. marinoi strain R05AC, was established from a resting cell revived from sediments collected from 14 m depth. This sediment was collected in May 2010 from Öresund, Sweden (55°59.16′ N, 12°44.02′ E), using a box corer. The culture is available from the Gothenburg University Marine Culture Collection (GUMACC) algal bank (https://marine.gu.se/english/research/marine-biology/algal-bank).

Isolation of the bacterial strain SMR1 was performed in April 2016, by dilution streaking on marine agar plates incubated in darkness at 16°C. The culture is currently maintained through monthly subculturing on marine agar plates. Strain SMR1 produces white colonies with firm edges under standard growth conditions, and grows well down to a media pH of 5 and salt ranges between 1-8%.

The PacBio RSII platform (Pacific Biosciences, Menlo Park, CA, USA) was used for sequencing strain SMR1. A single SMRT cell was used to sequence a 10kb fragment library, yielding 94,470 uncorrected reads of total size 1.1 Gbp. The de novo PacBio assembler Falcon version 1.7.5 (https://github.com/PacificBiosciences/FALCON/, 3) was used to assemble these reads (seed read length parameter - 10,600 bp), and contig circularization was confirmed by joining the opposite ends of each contig and realigning the sequencing reads using SMRT Portal version 2.3.0's RS_Resequencing.1 protocol (Pacific Biosciences, 4) to ensure consistent supporting read coverage. This circularization confirmation also included a correction step using the Quiver algorithm 4. The final assembly consists of eight circular contigs - one chromosome and seven plasmids - totalling 5,121,602 bp (per-contig figures are given in Table 1), with average read coverage of 166.75x.

Annotation was performed using Prokka version 1.12beta 5. This pipeline inferred 4,938 CDSs (of which 4,299 have a functional prediction, and 639 are labelled 'hypothetical protein'), 11 pseudogenes, 43 tRNAs, 6 rRNAs, 17 ncRNAs and one tmRNA (per-contig figures are given in Table 1).

Two rRNA operons were identified in the annotation - one on the chromosome and one on plasmid pSMR1-2 - in which the 16S rRNA sequences are identical to one another. These 16S rRNA genes share 99.2% identity with those of the Sulfitobacter pseudonitzschiae type strain H3T (= DSM 26824T) (accession nos. NZ_JAMD00000000 and NZ_FQVP00000000, respectively), S. guttiformis strain R16 (accession no. AB607871) and S. sp. 20_GPM-1509m (accession no. NZ_JIBC00000000), as well as 99.9% identity with Sulfitobacter sp. SAG13 (accession no. KX268604). To complement the 16S comparison, a phylotaxonomic analysis was performed using PhyloPhlAn version 0.99 6, which compared strain SMR1 to all whole-genome sequenced Rhodobacteraceae species on NCBI's RefSeq ftp site (ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/; accessed 11 June 2018). This showed strain SMR1 to be sister to the clade of the S. pseudonitzschiae type strain and S. sp. 20_GPM-1509m; the three-strain clade has 100% bootstrap support (Figure 1). Despite the 16S rRNA similarity to strain SMR1, S. guttiformis appears elsewhere in the Sulfitobacter clade. Based on these analyses, we place this strain in the taxon Sulfitobacter pseudonitzschiae.

A point of interest regarding this genome assembly is the large number of plasmids present, five of which are larger than 100 kbp. Multiple techniques were used to try and eliminate the possibility that this was the result of a misassembly, including the use of different assemblers (Canu 7 and HGAP 4, in addition to different parameters in Falcon 3). Manually joining contigs was also attempted, however nothing yielded fewer circular contigs than the assembly presented here, so we believe this result to be accurate. In addition, there is a precedent for a Sulfitobacter species to have a high number of plasmids - Sulfitobacter sp. AM1-D1 (accession nos. CP018076-CP018081) contains five plasmids, of which three are larger than 100 kbp. A strain of another Rhodobacteraceae species from the same clade, Tateyamaria omphalii (accession nos. CP019312-CP019319), also contains 7 plasmids, although these are smaller (46.3 - 84.5 kbp, compared to 92.8 - 428.1 kbp in strain SMR1).

A previous study by Amin et al. into the interaction between a Sulfitobacter species and a diatom (Sulfitobacter sp. SA11 and Pseudo-nitzschia multiseries) revealed a wide array of interactions between the two organisms, including production of the growth hormone indole-3-acetic acid (auxin) by Sulfitobacter and bacterial breakdown of diatom-produced DMSP for use as a sulfur source 8. Based on our genomics data, these two examples are also potential interactions in the S. marinoi-SMR1 system. Pathway Tools version 21.0 9 was used to predict potential pathways in strain SMR1, and this analysis found components of an indole-3-acetate biosynthesis pathway (nitrile hydratase and amidase) in the genome, as well as the dddL gene for DMSP lyase. This implies that strain SMR1 may have a similar relationship with S. marinoi as Sulfitobacter sp. SA11 has with P. multiseries. In addition, associations between Sulfitobacter and Skeletonema have previously been noted 10,11.

Nucleotide sequence accession numbers: This whole-genome project has been deposited in GenBank under the accession numbers CP022415-CP022422, as part of BioProject No. PRJNA380207.
