### ***********************************************************************
### xcms v1.3.2
### URL: http://metlin.scripps.edu/download/
### LC/MS and GC/MS Data Analysis and Alignement from netCDF data
### Author: Colin A. Smith <csmith@scripps.edu>;
### ***********************************************************************
### ***********************************************************************
### The script assumes xcms is installed via Packages->Install->BioConducor
### Copy this file into commandline or open via "Open script"
### Set 4 variables in +++ section and run have fun
### Example Script: Tobias Kind fiehnlab.ucdavis.edu 2006
### ***********************************************************************
### Part of script taken from https://github.com/vanmooylipidomics/LipidomicsToolbox/blob/master/prepOrbidata.R

myAlign <- function () {

	### +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	### These are the 4 variables you have to set for your own datafiles anything else runs automatically
	### Set your working directory under Windows, where your netCDF files are stored
	### Organize samples in subdirectories according to their class names WT/GM, Sick/Healthy etc.
	### Important: use "/" not "\"
	myDir = "/home/irockafe/Dropbox (MIT)/Alm_Lab/projects/revolutionizing_healthcare/data/cirrhosis_v_liver_cancer/MTBLS105/cdf_test"
	#myClass1 = "cirrhosis"
	#myClass2 = "liver_cancer"
	xcms_feature_table = "xcms_result"
	camera_feature_table = "xcms_camera_results.csv" 
	polarity_mode = "positive"
	nSlaves = 4
	### +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	### change working directory to your files, see +++ section
	setwd(myDir)

	### get working directory
	(WD <- getwd())

	### load the packages
	library(xcms)
	library(CAMERA)
	library(snowfall)

	### you can get help typing the following command at the commandline
	# ?retcor
	### finds peaks in NetCDF
	#xset <- xcmsSet(method="centWave", ppm= 5, snthresh=10,
	#		prefilter = c(5,1000), mzCenterFun = "wMean",
	#		integrate = 2, verbose.columns=TRUE, 
	#		peakwidth = c(20,60), fitgauss = TRUE,
	#		noise = 1000, mzdiff = -0.005, nSlaves=nSlaves 
	#		)
	xset <- xcmsSet()

	### print used files and memory usuage
	xset

	### Group peaks together across samples and show fancy graphics
	### you can remove the sleep timer (silent run) or set it to 0.001
	xset <- group(xset)

	### calculate retention time deviations for every time
	xset2 <- retcor(xset, family="s", plottype="m")

	### Group peaks together across samples, set bandwitdh, change important m/z parameters here
	### Syntax: group(object, bw = 30, minfrac = 0.5, minsamp= 1, mzwid = 0.25, max = 5, sleep = 0)
	xset2 <- group(xset2, bw =10)

	### identify peak groups and integrate samples
	xset3 <- fillPeaks(xset2)

	### print statistics
	xset3

	# Get number of samples
	nSamples = length(xset3@filepaths)
	print(nSamples)

	### create report and save the result in EXCEL file, print 20 important peaks as PNG
	#reporttab <- diffreport(object = xset3, 
	#			#class1 = myClass1, 
				#class2 = myClass2, 
	#			filebase = xcms_feature_table, 
	#			eicmax = 20, 
	#			metlin = 0.15)

	### print file names
	# dir(path = ".", pattern = NULL, all.files = FALSE, full.names = FALSE, recursive = FALSE)

	### output were done!
	print("Finished xcms, open by yourself the file myAlign.tsv and pictures in myAlign_eic")

	### now do CAMERA
	xset3_aligned = annotate(xset3,
				 nSlave=4,
				ppm=1.5,
			        mzabs=0.0001,
				quick=FALSE,
				polarity=polarity_mode,
				)
					

	# Generate result
	peaklist <- getPeaklist(xset3_aligned)	
	# Save results
	write.csv(peaklist, file=camera_feature_table)
}

### gives CPU, system, TOTAL time in seconds
system.time(myAlign())

### Currently R has no dual or multicore functionality, only a parallel library(snow)
### Benchmark on Dual Opteron 254 2.8 GHz with ARECA-1120 RAID5:
### 55 seconds total for the original 12 samples of the faahKO testset
### [1] 51.61 2.27 54.85 NA NA
### ***********************************************************************
### function finished
### ***********************************************************************
