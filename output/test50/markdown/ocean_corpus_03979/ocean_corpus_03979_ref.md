---
document_id: "zenodo-2609da1fb9329353"
title: "Elevated CO2 does not alter behavioural lateralization in free‐swimming juvenile European sea bass ( Dicentrarchus labrax) tested in groups"
authors: ["Jarvis, Dominic M.", "Pope, Edward C.", "Duteil, Mathieu", "Fürtbauer, Ines", "Brown, M. Rowan", "Davis, Richard J.", "King, Andrew J."]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2023
document_type: "technical_report"
domain: "carbon_biogeochemistry"
subdomain: "ocean_acidification_carbonate"
secondary_topics: []
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/8170302"
download_url: "https://zenodo.org/api/records/8170302/files/README_Dataset_EuropeanSeaBassBehaviouralLateralization_v1.txt/content"
doi_or_report_id: "10.5061/dryad.cjsxksn5q"
doi: "10.5061/dryad.cjsxksn5q"
pmcid: ""
license_status: "CC0"
license_url: "https://creativecommons.org/publicdomain/zero/1.0/"
accessed_at: "2026-07-28"
language: "en"
---

#############################################################################################################################
# Elevated CO2 does not alter behavioural lateralization in free-swimming juvenile European sea bass (Dicentrarchus labrax) #
#############################################################################################################################

#########
# README
#

File name: README_Dataset_EuropeanSeaBassBehaviouralLateralization_v1.txt
Authors: Dominic M Jarvis
Other Contributors: Edward C Pope, Mathieu Duteil, Ines Furtbauer, M Rowan Brown, Richard J Davis, Andrew J King
Date created: 06June2023
Date modified: 06June2023

##################
# Dataset Version
#

Current Version: v1
Date: 2022-09-20
Persistent identifier: DOI: 10.5061/dryad.cjsxksn5q
Summary of changes: none
License: CC0 1.0 Universal (CC0 1.0)
License Summary: https://creativecommons.org/publicdomain/zero/1.0/; the authors respectfully request to be contacted by researchers interested in the re-use of these data so that the possibility of collaboration can be discussed.

###################
# Dataset Contents
#

Fish Data Plotter (text file)
Fish Turn Plotter (text file)
Sea Bass All Angles (.csv file)
Sea Bass data 76° (.csv file)
Sea Bass Script (text file)

######################
# Contact Information
#

Name: Dominic Jarvis
Orchid ID: https://orcid.org/0000-0002-9257-1550
Email: dominic.jarvis1@googlemail.com

###############
# Instructions
#

This dataset is intended to be used to replicate the findings of the published document which it is related to, in the same manner in which it was approached by the authors.

The contents of this dataset is intended to be used with the following:

Matlab
Excel
R Studio x64 bit version
Dataset from Duteil, Mathieu et al. (2016), Data from: European sea bass show behavioural resilience to near-future ocean acidification
Identifier: DOI: 10.561/dryad.2dc8k

Further instructions can be found in the following sections regarding each file.

####################
# Fish Data Plotter
#

File name: FDP_-_txt.txt
Format: .txt
Description: A text document written out in the form of a script to be loaded into Matlab in conjunction with dataset from Duteil et al.
The script shall load the fish positional data and will prompt the user to choose between the "experimental" or "simulated" dataset, then to enter a "experiment number" and "fish number" in the form of numbers.
Once inputted, the script will run and produce an outline of the movement that the selected fish took during the selected experiment.
Size: 6,825 bytes
Suggested software: Matlab
Required datasets: ESM_ExperimentalData.mat; ESM_SimulatedData.mat;

####################
# Fish Turn Plotter
#

File name: FTP3_-_txt.txt
Format: .txt
Description: A text document written out in the form of a script to be loaded into Matlab in conjunction with dataset from Duteil et al.
The script shall load the fish positional data and will prompt the user to choose between the "experimental" or "simulated" dataset, then to enter a "experiment number" and "fish number" in the form of numbers.
Once inputted, the script will run and produce the number of turns the selected fish took in the selected experiment, depending on the parameters (speed of fish, minimum turn angle) that the user defines listed in the script.
The script contains within itself isntructions for its use, and the published paper contains information on the relevance of its operation to the paper.
Size: 8,044 bytes
Suggested software: Matlab
Required datasets: ESM_ExperimentalData.mat; ESM_SimulatedData.mat;

######################
# Sea Bass All Angles
#

File name: Sea_Bass_All_Angles_-_paper.csv
Format: .csv
Description: A comma-separated value file containing all the possible angles each fish could have taken during the 1 hour experiment at a speed greater than 0.7 cm/s from -180° to +180° (right and left).
This is because, each fish in the experimental and simulated dataset produced by Duteil et al had 90,000 xy co-ordinates.
As the video footage was recorded at 25 frames per second, the data was analysed in sets of 25 frames as one frame = line between 2 xy co-ordinates. This gives 3,600 sets of 25 frames for each fish.
If one looks at the Fish Data Plotter, it could appear that between the 1st frame and the 25th frame in a 25 frame set that a fish took multiple turns, when it may have only taken one turn.
A change in direction needs to be calculated every second/every 25 frames.
From this the 1st and 25th frame in each 25-frame set was extracted and the directional heading from -180° to +180° calculated to give the data in this csv file.
Size: 5,553,166 bytes
Dimensions: 3600 Rows x 260 columns
Suggested software: Matlab
Required datasets: ESM_ExperimentalData.mat; ESM_SimulatedData.mat;

####################
# Sea Bass data 76°
#

File name: Sea_Bass_data_R_76.csv
Format: .csv
Description: A comma-separated value file containing data that can be gathered using the Fish Turn Plotter script and the Sea Bass All Angles dataset.
This is an example of how the output data can be organised ready for statistical analysis using the Sea Bass script below in R Studio.
For example, it contains the Relative Lateralization score for each fish (a calculation of turn preference, calculated by the Relative Lateralization Index)
Where R = Total number of right turns, and L = Total number of left turns
(R-L)/(R+L) x 100
This csv file contains the same information for both the Experimental and Simulated datasets. Each fish has a unique identifier and has a Experiment ID, Tank ID, and Condition (respective of ocean acidification condition)
(i.e. Sea_Bass_data_R_76.csv , gathered using the above data files and parameters such as a minimum turn angle of 76°).
Size: 14,658 bytes
Dimensions: 270 columns x 11 rows
Suggested software: R Studio
Variables: Fish_ID: Unique identifier for each fish (270 fish)
Exp_ID: Unique identifier for each experiment (27 experiments)
Tank_ID: Unique identifier for each tank (5 tanks)
Condition: Identifier for experimental condition i.e. Ocean acidification OA, Ambient AM, raised in Ambient tested in Ocean acidified AMOA
Turn_Tot_(76): Total number of turns (both left and right) taken at a minimum turn angle of 76°, using Experimental dataset
Turn_Angle_(76): Mean turn angle taken at a minimum turn angle of 76°, using Experimental dataset
LatR_Score_(76): Relative lateralization score taken at a minimum turn angle of 76°, values are between -100 (all left turns) and +100 (all right turns), using Experimental dataset
Abs_Lat_Score_(76): Absolute lateralization score taken at a minimum turn angle of 76° (no - or +), using Experimental dataset
Turn_Tot_(76S): Total number of turns (both left and right) taken at a minimum turn angle of 76°, using Simulated dataset
Turn_Angle_(76S): Mean turn angle taken at a minimum turn angle of 76°, using Simulated dataset
LatR_Score_(76S): Relative lateralization score taken at a minimum turn angle of 76°, values are between -100 (all left turns) and +100 (all right turns), using Simulated dataset


##################
# Sea Bass Script
#

File name: Sea_bass_script_-_txt.txt
Format: .txt
Description: A text document split into section to allow the user to perform statistical data analysis on an example dataset
(i.e. Sea_Bass_data_R_76.csv , see above description).
There is also instructions for statistical data analysis on a dataset where the minimum turn angle is 130°, but it would be beneficial to the user's learning of the dataset to produce the data for themselves using the Fish Turn Plotter and editing the parameters accordingly with the Sea Bass All Angles dataset, and using the layout of the Sea Bass data 76° file to organise the data for use with this script).
Additionally, this script can be edited according to how the user names the dataset files they create, to ensure that the correct dataset is loaded for statistical analysis.
Size: 17,835 bytes
Suggested software: R studio
Required datasets: Sea Bass data 76°

#######
# End #
#######
