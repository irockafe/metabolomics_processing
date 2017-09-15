# Script that accepts a user-generated parameters file,
# or a handful of preset LC-MS presets

# Input possibilities
# Rscript run_xcms.R --preset uplc_orbitrap
# Rscript run_xcms.R -sf summary_file.txt
library(optparse)
# library(CAMERA) TODO!

parser <- OptionParser()
parser <- add_option(parser, c('--preset'),
   type='character', default=NULL,
   help=paste('Preset xcms settings taken from',
'https://dx.doi.org/10.1038%2Fnprot.2011.454',
' (Siuzdak 2012).', 'Options are:',
'hplc_qtof, hplc_qtof_hires, hplc_orbitrap',
'uplc_qtof, uplc_qtof_hires, uplc_orbitrap'))
parser <- add_option(parser, c('--summaryfile', '-s'), type='character',
    default=NULL, 
    help=paste('A file containing xcms parameters.',
   'If you run this script with no arguments,',
   'A mostly-blank summary file will be made',
   'You can then fill in parameters as you like.',
   'See the xcms documentation for defaults or if',
   'you are confused'))
parser <- add_option(parser, c('--path', '-p'), type='character',
		     default=NULL,
		     help=paste('Path to your data'))
parser <- add_option(parser, c('--polarity'), type='character',
                              default=NULL,
                     help=paste('polarity mode of MS used - Required.'))

args = parse_args(parser)

generate_blank_summary_file <- function(path) {
output = "### General Parameters
data_dir
polarity_mode
### Peak Detection Parameters
detection_method\tcentWave
ppm
peak_width
prefilter

### Peak-grouping parameters
bw
mzwid
minfrac\t0
minsamp\t2

### retention-correction parameters
retcor_method\tloess
missing
extra"
    print(output)
    params_file = paste(path, '/xcms_params.tab', sep='')
    write(output, file=params_file)
}


default_params = function(string) {
   # Default xcms parameters for various MS and LC combinations
   # Taken from "Meta-analysis of untargeted metabolomic 
   # data from multiple profiling experiments", Patti et al   
   # RETURN [param_name1=param_value1, param_name2=param_value2...]
   
   # Define the preset values as nested list, indexed on 
   # as [LC-MS[ppm, peakwidth, bw, mzwid, prefilter]]
   default_params = list(
   hplc_qtof = list(ppm=30, peakwidth=c(10,60), bw=5, 
   mzwid=0.025, prefilter=c(0,0)),
   hplc_qtof_hires = list(ppm=15, peakwidth=c(10,60), bw=5,
    mzwid=0.015, prefilter=c(0,0)),
   hplc_orbitrap = list(ppm=2.5, peakwidth=c(10,60), bw=5,
  mzwid=0.015, prefilter=c(3,5000)),
   uplc_qtof = list(ppm=30, peakwidth=c(5,20), bw=2,
    mzwid=0.025, prefilter=c(0,0)),
   uplc_qtof_hires = list(ppm=15, peakwidth=c(5,20), bw=2,
 mzwid=0.015, prefilter=c(0,0)),
   uplc_orbitrap = list(ppm=2.5, peakwidth=c(5,20), bw=2,
  mzwid=0.015, prefilter=c(3,5000))
  )
    # If your string is found in the default list,
    # return the default params
 if (exists(string, where=default_params)) {
 # double brackets because it removes the name of
 # the top-level nested-list (i.e. uplc_orbitrap$ppm becomes
 # simply $ppm when you use double brackets )
 params = default_params[[string]]
  return(params)
 } else{
  msg = sprintf(paste("I couldn't understand your preset value.",
  "The allowed inputs are: %s"),
  paste(names(default_params), collapse=', '))
  stop(msg)
   }
}


### Parse a tab-delimited summary file
char_to_numeric <- function(char) {
   # Take in a space-delimited character that represents
   # a number or vector. Convert it to numeric.
   numeric <- as.numeric(strsplit(char, " ")[[1]])
    return(numeric)
}

get_params <- function(path, char_to_numeric) {
   # INPUT: tab-delim file of 
   # space-delimited values 
   # OUTPUT: A labeled list with each label from the first column
   # of the file. Each value, character or numeric, from the second column
   # It will accept vectors as space-delimited entries in the second column 
   # of the text file
   df <- read.table(path, sep='\t', header=FALSE, row.names=1,
                    colClasses="character", blank.lines.skip=TRUE, fill=TRUE)
   print(df)
   print(dim(df))
   # There should only be one column of values
   if (dim(df)[2] > 1){
       stop(paste("Your summary file should only have 1 (tab-delimited) column of values.",
       sprintf("it has %s columns", dim(df)[2])))
   }
   print('read table output:')
   print(paste('Df dimensions', dim(df)))
   # Make an empty list to gather param values
   param_lst = setNames(vector("list", dim(df)[1]), rownames(df))
   # If a summary file entry is missing, raise an error
   for (idx in rownames(df)){
       if (df[idx,] == "") {
           stop(paste(sprintf('The parameter %s is missing!', idx),
                              'Please set it, or use one of the preset parameter settings'))
       }
       # if no alphabetic characters, convert character to numeric
       digit = grepl("[[:digit:]]", df[idx,])
       alpha = grepl("[[:alpha:]]", df[idx,])
       if (digit &&! alpha) {
           sprintf('%s is a number(s)', df[idx,])
           print(class(df[idx,]))
           param_lst[[idx]] = char_to_numeric(df[idx,])
       
       } else if (alpha &&! digit){
           param_lst[[idx]] = df[idx,]
       }
    }
    return(param_lst)
}

# Code to run xcms
run_xcms = function(data_dir, xcms_params, polarity_mode,
           # Optional params below. To set them, includ
           # a summary file or use a preset
           # peak detection params
           detection_method='centWave', ppm=25, 
           peak_width=c(10,60), prefilter=c(3,100),
           # grouping parameters
           bw=20, mzwid=0.025, minfrac=0, minsamp=5,
           # retention-correction parameters
           retcor_method='loess', missing=1, extra=1)
           {
    # INPUT - data_dir, a path to your data in one directory
    #   xcms_params - a named-list containing xcms parameters
    #       It's origin is from a preset value or a summary file
    #   polarity_mode, 'positive' or 'negative'          
    # FUNCTION - Runs xcms with the supplied parameters
    #   doing a group-retcor-group pass
    # OUTPUT - A feature table, retcor deviation plot, and xcmsSet
    #   objects after each grouping stage of xcms

    # CALL - To call this function, use
    # run_xcms(data_dir, xcms_params, polarity_mode)
    # The parameters will be adopted from the summary file
    # xcms_params


    # override default params if present in parameters
    # 
    if (!is.null(xcms_params$detection_method )){
        detection_method<-xcms_params$detection_method
    }
    if (!is.null(xcms_params$ppm  )){
        ppm <- xcms_params$ppm
    }
    if (!is.null(xcms_params$peak_width  )){
       peak_width <- xcms_params$peak_width 
    }
    if (!is.null(xcms_params$prefilter  )){
        prefilter <- xcms_params$prefilter
    }
    if (!is.null(xcms_params$bw  )){
        bw <- xcms_params$bw
    }
    if (!is.null(xcms_params$mzwid )){
        mzwid <- xcms_params$mzwid
    }
    if (!is.null(xcms_params$minfrac  )){
        minfrac <- xcms_params$minfrac
    }
    if (!is.null(xcms_params$minsamp   )){
        minsamp <- xcms_params$minsamp 
    }
    
    if (!is.null(xcms_params$retcor_method   )){
        retcor_method <- xcms_params$retcor_method
    }
    if (!is.null(xcms_params$missing   )){
        missing <- xcms_params$missing
    }
    if (!is.null(xcms_params$extra   )){
        extra <- xcms_params$extra
    }
    
    
    # escape spaces in data_dir path
    output_dir = getwd()
    xcms_feature_table = "xcms_result"
    camera_feature_table = "xcms_camera_results.csv"
    nSlaves=0
                  
    ### change working directory to your files, see +++ section
    setwd(data_dir)
    # wrtie parameters to file
    peak_width_str = paste(paste(peak_width), collapse=" ")
    prefilter_str = paste(paste(prefilter), collapse=" ")
    param_string = sprintf(
"### General Parameters
data_dir\t%s
polarity_mode\t%s
### Peak Detection Parameters
peak_picking\t%s
ppm\t%i
peak_width\t%s
prefilter\t%s

### Peak-grouping parameters
bw\t%i
mzwid\t%.4f
minfrac\t%i
minsamp\t%i

### retention-correction parameters
retcor_method\t%s
missing\t%i
extra\t%i
", 
                       data_dir, polarity,
                       detection_method, ppm, peak_width_str, prefilter_str,
                       bw, mzwid, minfrac, minsamp, 
                       retcor_method, missing, extra)
                         
    params_file = paste(output_dir, '/xcms_params.tab', sep='')
    write(param_string, file=params_file)
    

    #stop("Don't run xcms while you're debugging")

    # Load packages
    library(xcms)
    library(snowfall)
    library(BiocParallel)
    # set the number of cores
    register(MulticoreParam(4))
                             
    # Detect peaks
    xset <- xcmsSet(method=detection_method, ppm=ppm, prefilter=prefilter,
                    peakwidth=peak_width, )
    print("finished peak Detection!")
    # Group peaks together across samples
    # save the detected peaks in case downstream processing fails 
    # and you have to go in manually to figure out parameters
    # TODO - should the bw parameter here be changed depending
    # on the platform used (i.e. bw=30 is default, but for uplc, 
    # maybe the coarse grouping should be bw=15 or something)
    xset <- group(xset)
    print("finished first group command!")
    print(xset)
    saveRDS(xset, paste(output_dir, '/xset.Rdata', sep=''))
         
    # Try to retention-correct
    xset2 <- retcor(xset, method=retcor_method,
                    family="s", plottype="m",
                    missing=missing)
    print("finished retcor!")
     
    # regroup after retention time correction
    xset2 <- group(xset2, bw =bw, mzwid=mzwid,
                          minfrac=0, minsamp=minsamp)
    saveRDS(xset2, paste(output_dir, '/xset2.Rdata', sep=''))
    print("finished second group command!")
                                 
    # Fill in peaks that weren't detected
    xset3 <- fillPeaks(xset2)
    print("Finished filling peaks!")
    print(xset3)
    # Move back to output_dir and write out your feature table
    setwd(output_dir)
    xcms_peaklist = peakTable(xset3, filebase=xcms_feature_table)
    write.csv(xcms_peaklist, paste(xcms_feature_table,ppm, sep='_'))
    print("Finished xcms!")
    }

print(args$summaryfile)
print(args$preset)
print(is.null(args$summaryfile))
print(paste('class of summary file:', class(args$summaryfile)))

# if they don't give a preset, or a sample summary file, generate a sample summary file
# and raise an error
if (is.null(args$summaryfile) && is.null(args$preset)) {
    generate_blank_summary_file(getwd())
    stop(paste("You didn't pass any parameters.",
 "Please use on of the presets, or",
 "fill out the summary file I generated for you.\n\n",
 "If you need to enter a vector in the summary file",
 "(i.e. for prefilter), enter it as space-delmiited text" ))
    }
# if preset, get parameter
print(is.character(args$preset))
if (is.character(args$preset)) {
    xcms_params <- default_params(args$preset)
    print(xcms_params)
# if summary file, parse it and get the values
} else if (is.character(args$summaryfile)){
    xcms_params <- get_params(args$summaryfile, char_to_numeric)  
    print(xcms_params)
}
# If user gave both preset and summary file, warn them that
# preset will take precedence
if (is.character(args$preset) && is.character(args$summaryfile)){
	warning("You specified a preset parameter and a summaryfile.
	     The summary file will be ignored and preset parameters used.")
}

#TODO Add run_xcms function and how to extract parameters from lists
# and what to do with values not given
# check if value is in your user-defined parameters. if so, define it
# peak detection params
if (is.null(xcms_params$data_dir)) {
    data_dir <- getwd()
} else {
    data_dir <- xcms_params$data_dir
}

# If you gave a summary file with polarity specified
# Make sure that it matches what you wrote on command line
# If no polarity specified, kill process
if (is.null(xcms_params$polarity_mode) && is.null(args$polarity)){
    stop("You didn't specify polarity mode in the command line or
         the summary file")
}

# If no command-line arg for polarity, get it from summary-file.
# Otherwise, get it from command line
if (is.null(args$polarity)){
    polarity <- xcms_params$polarity_mode
} else {polarity <- args$polarity}

# If gave summary file and command-line polarity, make sure they match
if (is.character(xcms_params$polarity_mode) && is.character(args$polarity)){
    if (xcms_params$polarity_mode != args$polarity){
        stop(paste("The polarity mode given in the summary file",
                  "doesn't match the polarity specified in the",
                 "command line arguments", 
                 sprintf("Command line: %s, Summary file: %s",
                        args$polarity, xcms_params$polarity_mode)))
    }
} 

# TODO - Done -test for presets
# Done - test for full summary file
# Done - fails for missing items - test for partial summary file
# Done - test for summary file and preset
system.time(debug(run_xcms(data_dir, xcms_params, )))
