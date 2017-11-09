# Script that accepts a user-generated parameters file,
# or a handful of preset LC-MS presets

# Input possibilities
# Rscript run_xcms.R --preset uplc_orbitrap
# Rscript run_xcms.R -sf summary_file.txt
library(optparse)
# library(CAMERA) TODO!

parser <- OptionParser()
parser <- add_option(parser, c('--summaryfile', '-s'), type='character',
    default=NULL, 
    help=paste('A file containing xcms parameters.',
   'If you run this script with no arguments,',
   'A mostly-blank summary file will be made',
   'You can then fill in parameters as you like.',
   'See the xcms documentation for defaults or if',
   'you are confused. Required.'))

parser <- add_option(parser, c('--data', '-d'), type='character',
		     default=NULL,
		     help=paste('Directory containing data for xcms
				to process. Required.'))

parser <- add_option(parser, c('--output', '-o'), type='character',
		     default=NULL,
		     help=paste('Path to output processed
				data to (single directory)'))

args = parse_args(parser)

### Parse a tab-delimited summary file
char_to_numeric <- function(char) {
   # Take in a space-delimited character that represents
   # a number or vector. Convert it to numeric.
   numeric <- as.numeric(strsplit(char, " ")[[1]])
    return(numeric)
}

get_params <- function(path, char_to_numeric) {
   # INPUT: tab-delim file of 
   # space-delimited values. Meaning that if you want c(20,60), 
   # You should input "20 60"	
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
                              'in your xcms_params file'))
       }
       # if no alphabetic characters, convert character to numeric
       digit = grepl("[[:digit:]]", df[idx,])
       alpha = grepl("[[:alpha:]]", df[idx,])
       if (digit &&! alpha) {
           sprintf('%s is a number(s)', df[idx,])
           param_lst[[idx]] = char_to_numeric(df[idx,])
       
       } else if (alpha){ # Anything that isn't all numbers is string
	   print('Setting this as parameter')
           print(df[idx,])
           param_lst[[idx]] = df[idx,]
       }
    }
    return(param_lst)
}

# Code to run xcms
run_xcms = function(xcms_params, output_dir, data_dir,
           # Optional params below. To set them, include
           # a summary file 
           detection_method='centWave', ppm=25, 
           peak_width=c(10,60), prefilter=c(3,100),
           # grouping parameters
           bw=20, mzwid=0.025, minfrac=0, minsamp=5,
           # retention-correction parameters
           retcor_method='loess', missing=1, extra=1)
           {
    # INPUT - 
    #    xcms_params - a named-list containing xcms parameters
    #       It's origin is from a preset value or a summary file
    #       parsed through the function get_params() 
    # FUNCTION - Runs xcms with the supplied parameters
    #    doing a group-retcor-group pass
    # OUTPUT - A feature table, retcor deviation plot, and xcmsSet
    #    objects after each grouping stage of xcms
    #    output xcmsSet incase you want to repeat the group-retcor-group
    #    again (TODO: not implemented)

    # CALL - To call this function, use
    # run_xcms(xcms_params, output_dir)
    #     xcms_params will come from the get_params function 
    # The parameters will be adopted from the summary file
    # xcms_params


    # override default params if present in parameters
    # TODO: learn how to loop over entry-names 
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
    xcms_feature_table = "xcms_result"
    camera_feature_table = "xcms_camera_results.csv"
    # nSlaves=0
                  
    ### change working directory to your files
    ### TODO - this can probably be changed - xcms certainly has
    ### a way to point to files
    setwd(data_dir)
    
    #stop("Don't run xcms while you're debugging")

    # Load packages
    library(xcms)
    library(snowfall)
    library(BiocParallel)
    # TODO - Learn to set the number of cores
    #register(MulticoreParam(4))
                             
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
    saveRDS(xset, paste(output_dir, '/grouped.Rdata', sep=''))
         
    # Try to retention-correct
    xset2 <- retcor(xset, method=retcor_method,
                    family="s", plottype="m",
                    missing=missing)
    print("finished retcor!")
     
    # regroup after retention time correction
    xset2 <- group(xset2, bw =bw, mzwid=mzwid,
                          minfrac=0, minsamp=minsamp)
    saveRDS(xset2, paste(output_dir, '/grouped_retcor.Rdata', sep=''))
    print("finished second group command!")
                                 
    # Fill in peaks that weren't detected
    xset3 <- fillPeaks(xset2)
    print("Finished filling peaks!")
    print(xset3)
    # Move back to output_dir and write out your feature table
    setwd(output_dir)
    xcms_peaklist = peakTable(xset3, filebase=xcms_feature_table)
    #write.csv(xcms_peaklist, paste(xcms_feature_table, sep='_'))
    print("Finished xcms!")
    }

print(args$summaryfile)
print(is.null(args$summaryfile))
print(paste('class of summary file:', class(args$summaryfile)))

# if they don't give a sample summary file, raise an error
if (is.null(args$summaryfile) ) {
    stop(paste("You didn't pass any parameters.",
 "Please generate a params file using generate_xcms_params.R ",
 "You will need to edit the output of generate_xcms_params.R",
 "after it has run if you don't choose a preset"))
    }
if (is.null(args$output) | is.null(args$data)) {
	stop("You didn't provide an output directory (--output)
		   or a data directory (--data). Please do so.")
}

# if summary file, parse it and get the values
if (is.character(args$summaryfile)){
    xcms_params <- get_params(args$summaryfile, char_to_numeric)  
    print(xcms_params)
}

#TODO Add run_xcms function and how to extract parameters from lists
# and what to do with values not given
# check if value is in your user-defined parameters. if so, define it
# peak detection params
if (is.null(args$data)) {
    stop('You need to specify the directory where your data is (--data).
	That way xcms can find it')
}

print('Output directory!')
print(args$output)
# Done - test for full summary file
# Done - fails for missing items - test for partial summary file
# Done - test for summary file
system.time(debug(run_xcms(xcms_params, args$output, args$data)))
