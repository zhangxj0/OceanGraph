---
document_id: "zenodo-ee72b0237b76dcd4"
title: "The vulnerability of shellfish aquaculture to climate change and ocean acidification– a global assessment"
authors: ["Stewart-Sinclair, Phoebe", "Wilding, Tom", "Last, Kim", "Payne, Ben"]
publisher: "Zenodo deposit"
journal: ""
publication_year: 2022
document_type: "technical_report"
domain: "carbon_biogeochemistry"
subdomain: "ocean_acidification_carbonate"
secondary_topics: []
source_platform: "Zenodo"
source_url: "https://zenodo.org/records/4532267"
download_url: "https://zenodo.org/api/records/4532267/files/R_Script.txt/content"
doi_or_report_id: "10.5061/dryad.t4b8gthz3"
doi: "10.5061/dryad.t4b8gthz3"
pmcid: ""
license_status: "CC0"
license_url: "https://creativecommons.org/publicdomain/zero/1.0/"
accessed_at: "2026-07-28"
language: "en"
---

#R script
#install libraries
>install.packages("bigmemory")
>install.packages("xlsx")
>install.packages("chron")
>install.packages("lattice")
>install.packages("RColorBrewer")
>install.packages("maptools")
>install.packages("ncdf4")
>install.packages("raster")
>install.packages("rgdal")
>install.packages("rgeos")
>install.packages("rworldmap")
>install.packages("vegan")

#load libraries
>library(bigmemory)
>library(xlsx)
>library(chron)
>library(lattice)
>library(RColorBrewer)
>library(maptools)
>library(ncdf4)
>library(raster)
>library(rgdal)
>library(rgeos)
>library(rworldmap)
>library(vegan)

 
#R script for Exposure variables from RCP8.5
#This script can be adapted to analyse data for any of the climate change and ocean acidification indicators.
#Extracting a time slice (e.g. a decade).
>Exposure.2099_2100 <- open.nc(file.choose()) # 'tos_Omon_HadGEM2-CC_rcp85_r1i1p1_209912-210012.nc' #example here is 2090-2100 NetCDF file type.

#coordinate variables (longitude and latitude) are read.
>lon <- var.get.nc(Exposure.2099_2100, "lon")
>nlon <- dim(lon)
>head(lon) #[1] 0 1 2 3 4 5

>lat <- var.get.nc(Exposure.2099_2100, "lat")
>nlat <- dim(lat)
>head(lat) #[1] -90 -89 -88 -87 -86 -85

>print(c(nlon, nlat)) #confirms the dimensions of the data.
#[1] 360 216.
#longitude values resolution=1, whereas latitude values resolution varies 0.3396, 1.

#read the time variable
>t <- var.get.nc(Exposure.2099_2100, "time")
>tunits <- att.get.nc(Exposure.2099_2100, "time", "units")
>t # list the values

>nt <- dim(t) # get the number of values and list them
>nt
#[1] 13
#Dec 2099 to Dec 2100.

>tunits #[1] "days since [1] "days since 1859-12-01"

#variable and its longname, units and fill value (_FillValue) attributes are read next.
>tos.array <- var.get.nc(Exposure.2099_2100, "tos")
>dlname.tos <- att.get.nc(Exposure.2099_2100, "tos", "long_name")
>dunits.tos <- att.get.nc(Exposure.2099_2100"tos", "units")
>fillvalue.tos <- att.get.nc(Exposure.2099_2100, "tos", "_FillValue")

#The dimensions of the array containing the values of the variables can be confirmed using the dim() function:
>dim(tos.array) #[1] 360 216 13
#lon, lat, time, no depth in this example

#Next, a set of "global attributes" (or metadata) are read.
>title <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "title")
>institution <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "institution")
>datasource <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "source")
>references <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "references")
>history <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "history")
>Conventions <- att.get.nc(Exposure.2099_2100, "NC_GLOBAL", "Conventions")

#attribute values can be listed by printing their values, e.g. title of data file.
>title #[1] "HadGEM2-CC model output prepared for CMIP5 RCP8.5"

#Convert the whole array to a data frame, and calculate the annual mean.
#First, create a long vector tmp.vec.long using the as.vector() reshaping function, and verify its length.
>Exposure.2099_2100.vec.long <- as.vector(tos.array)
>length(Exposure.2099_2100.vec.long) #[1] 1010880

#Then reshape that vector into a x by 13 matrix using the matrix() function, and verify its dimensions.
>Exposure.2099_2100.mat <- matrix(Exposure.2099_2100.vec.long, nrow = nlon * nlat, ncol = nt)
>dim(Exposure.2099_2100.mat) #[1] 77760 13
#Create the second data frame from the tmp.mat matrix.
>lonlat <- expand.grid(lon, lat)
>Exposure.2099_2100.mat.2 <- data.frame(cbind(lonlat, Exposure.2099_2100.mat))

#name columns containing yearly averages for ease of understanding.
>names(Exposure.2099_2100.mat.2) <- c("lon", "lat", “Dec2099", "Jan2100", "Feb2100", "Mar2100", "Apr2100", "May2100", "Jun2100", "Jul2100", "Aug2100", "Sep2100", "Oct2100", "Nov2100", "Dec2100")
>options(width = 110)

#Get annual mean and add them the second data frame.
>Exposure.2099_2100.mat.2$mean <- apply(Exposure.2099_2100.mat.2[3:15], 1, mean)

#Write the second data frame out as a .csv file, dropping NAs.
>write.csv(na.omit(Exposure.2099_2100.mat.2), " Exposure.2099_2100.means.csv", row.names=FALSE)

#Now have an average for each time slice for each set of coordinates (lat and long)
#To convert to SpatialPointsDataFrame
>Exposure.2099_2100.spg <- SST.2100.means.csv
>coordinates(Exposure.2099_2100.spg) <- ~ lon + lat

#assign a CRS to your spatial object
>proj4string(Exposure.2099_2100.spg) = CRS("+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0")

#reclassification of layer on to our exposure classification from 1-5.
#Custom reclassification matrix that reclassifies indicator raw values to exposure category in excel ‘reclas_ Exposure.2099_2100’.


#overlay of exposure scores with Exclusive Economic Zone (EEZ) polygons.
#Overlay world map using wrld_simpl from maptools.
>plot(reclas_ Exposure.2099_2100, xlim = c(-180, 180), ylim = c(-80, 90), legend = T)
>data(wrld_simpl)
>plot(wrld_simpl, add = T)

#Read EEZ shapefile
>eez <- readOGR(file.choose(), layer = "eez") #eez.shp is a large spatialpolygons data frame.

#visualise EEZ polygon data.
>plot(eez)

#CRS of the EEZ shapefile.
>crs(eez) # +proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0

#extract points from Exposure Indicator layer based on spatial polygons of EEZ.
#Assuming that "shape" is a polygon, you can then use the "over" function to identify overlap between the two feature classes (i.e. Exposure Indicator points and EEZ).
> require(sp)

#Use over function to add polygon ID’s of EEZ to points. Non-overlapping points will have NA.
> reclas_ Exposure.2099_2100@data <- data.frame(reclas_ Exposure.2099_2100@data, over(reclas_ Exposure.2099_2100, eez) )

#averaging of Exposure within each nation’s EEZ.
#average the Exposure Indicator scores across each country’s EEZ
#for each country
>Exposure.2099_2100_EEZmean.Countries <-aggregate(reclas_ Exposure.2099_2100@data, by=list(reclas_ Exposure.2099_2100@data$Sovereign1),
FUN=mean, na.rm=TRUE)

#join new national average Exposure Indicator score data to a map.
>ExposureIndicatorMap <- joinCountryData2Map(Exposure.2099_2100_EEZmean.Countries,
nameJoinColumn="Country",
joinCode="NAME" )

#plot (map) of country average exposure based on EEZ reclassified values.
#map graphics.
>mapDevice() #create a world shaped window
>mypalette <- brewer.pal(5, "Reds")

#plot the map
>MapExposureIndicator <- mapCountryData( ExposureIndicatorMap,
nameColumnToPlot=’Exposure',
catMethod='categorical', addLegend='FALSE', borderCol = 'white',
numCats=5, col = mypalette, mapTitle = " ", oceanCol = 'lightblue', missingCountryCol = 'white' )

#add a legend
>do.call( addMapLegendBoxes, c(ExposureIndicatorMap, x='bottomleft', horiz=TRUE, title="Exposure"))
 
R script for Sensitivity and Adaptive capacity variables.
#Read in .csv file with reclassified S and AC scores for all nations that we have data for.
>S <- read.csv(file.choose()) #Sensitivity in this example
>head(S.Norm.PPCA.coast)
#Group.1 Sensitivity
#1 Afghanistan 2.0
#2 Albania 1.5
#3 Algeria 1.0

#remove all countries that are not coastal.
>S.coast. <- merge(S, Counties.coast.names, by = "Group.1")

#graph data as above.

R script of PCA of indicators to test for redundant indices.
#Load data
>S <- read.table (file.choose(), header=T, sep= ",") #Sensitivity is the example here.
>head(S)
# Group.1 Production Economic.dependence Nutritional.dependence
#1 Argentina 1 1 NA
#2 Australia 2 1 NA
#3 Belize NA NA 3

#remove row names
>write.csv(S, "S.csv", row.names = FALSE)

#separate country (categorical variable) from index scores (continuous).
>S.scores <- S[, 2:5]
>S.countries <- S[, 1]

#apply PCA: scale. = TRUE is highly advisable, but default is FALSE.
>PCA.S. <- prcomp(na.omit(S),
center = TRUE,
scale. = TRUE)

#print PCA analysis
>summary(PCA.S)
#Importance of components:
# PC1 PC2 PC3 PC4
#Standard deviation 1.6362 0.8550 0.7288 0.24601
#Proportion of Variance 0.6693 0.1827 0.1328 0.01513
#Cumulative Proportion 0.6693 0.8521 0.9849 1.00000

NMDS of decades for each sub-layer (E, S and AC) and for overall V.
#load post-PCA scores for coastal countries for all sub-layers.
>V <- read.csv(file.choose(), header = T) #Vulnerability is the example here.
>head(V)
# Year Albania Algeria Angola
#1 2020 3 4 3 2
#2 2030 3 4 3 2
#3 2040 3 4 3 2
#4 2050 3 4 3 2
#5 2060 3 4 3 3
#6 2070 4 4 3 3

#change year column to row names
>rownames(V) <- V[,1]
>V[,1] <- NULL

#transform the remaining dataset to a matrix.
>V.1 <-as.matrix(V)

>is.matrix(V.1)
#[1] TRUE

#perform monoMDS.
>V.d <- dist(V.YEARS.1) #calculate euclidean distances between the rows.
>V.MDS <- monoMDS(V.d, k=2)

#use ordilabel to stop years overlapping on the plot.
>ordilabel(V.MDS, Display= "sites", priority=colnames(V))

#add environmental factors to determine the drivers of the distances between decades.
>ef <- envfit(V.MDS, V, permu = 999)

#add environmental factors to plot.
>plot(V.MDS, display = "sites")
>plot(ef, p.max = 0.1, col="black")

#Print NMDS results
>V.MDS

#get NMDS scores
>nmds.SCORES <- scores(V.MDS, choices = NA)

#NB: if there are any questions about this code please direct them to the author, Phoebe Stewart-Sinclair
at phoebe-stewart@hotmail.com.
