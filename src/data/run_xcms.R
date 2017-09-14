# Script that accepts a user-generated parameters file,
# or a handful of preset LC-MS presets

# Input possibilities
# Rscript run_xcms --preset uplc_orbitrap
# Rscript run_xcms -sf summary_file.txt
library(optparse)
# library(CAMERA) TODO!
parser <- OptionParser()
parser <- add_option(parser, c('--preset', '-ps'),
   type='character', default=NULL,
   help=paste('Preset xcms settings taken from',
'https://dx.doi.org/10.1038%2Fnprot.2011.454',
' (Siuzdak 2012).', 'Options are:',
'hplc_qtof, hplc_qtof_hires, hplc_orbitrap',
'uplc_qtof, uplc_qtof_hires, uplc_orbitrap'))
parser <- add_option(parser, c('--summaryfile', '-f'), type='character',
    default=NULL, 
    help=paste('A file containing xcms parameters.',
   'If you run this script with no arguments,',
   'A mostly-blank summary file will be made',
   'You can then fill in parameters as you like.',
   'See the xcms documentation for defaults or if',
   'you are confused'))

args = parse_args(parser)

generate_blank_summary_file <- function(path) {
   output = '### Peak Detection Parameters
peak_picking\tcentWave
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
extra'
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
 }
    else{
  msg = sprintf(paste("I couldn't understand your input.",
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

print

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
 "fill out the summary file I generated for you"))
    }

# if preset, get parameter
if (is.character(args$preset)) {
    xcms_params <- default_params(args$preset)
    print(xcms_params)

# if summary file, parse it and get the values
} else if (is.character(args$summaryfile)){
    xcms_params <- get_params(args$summaryfile, char_to_numeric)  
    print(xcms_params)
}

#TODO Add run_xcms function and how to extract parameters from lists
# and what to do with values not given

