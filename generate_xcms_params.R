# Goal is to create a blank xcms parameters file for user to fill in
# or a preset parameter file based on 

# To call with no preset: Rscript scritname.R
      # This will create a blank summary file
# Rscript scriptname.R --output path/to/output
#     --polarity positive
#     # THis will make a blank summary file with 
      # some directories filled out
# For presets, do:
# Rscript scriptname.R --preset 'hplc_orbitrap'
library(optparse)

parser <- OptionParser()
parser <- add_option(parser, c('--preset'),
		     type='character', default=NULL,
		     help=paste('Preset xcms settings taken from',
				'https://dx.doi.org/10.1038%2Fnprot.2011.454',
				' (Siuzdak 2012).', 'Options are:',
				'hplc_qtof, hplc_qtof_hires, hplc_orbitrap',
				'uplc_qtof, uplc_qtof_hires, uplc_orbitrap')
		     )
parser <- add_option(parser, c('--output', '-o'), type='character',
		     default=getwd(),
		     help=paste('Path to output directory')
		     )
parser <- add_option(parser, c('--polarity'), type='character',
                              default=NULL,
                     help=paste('polarity mode of MS used - Required.
                                 Options are "positive" or "negative"'))
parser <- add_option(parser, c('--study', '-s'), type='character',
		     default=NULL,
		     help=paste('Unique study name from database you are 
				downloading from. Required')
		     )
args = parse_args(parser)

generate_blank_summary_file <- function(path, study) {
# Create a summary file that contains xcms parameters that
# a user can fill in. add tab between name and value 
# If need to create a list, delimit entries with spaces, 
# (i.e. bw\t0 2)
output = "### General Parameters
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
    params_file = paste(path, sprintf('/xcms_params_%s.tsv', study),
		       	sep='')
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

write_params = function(output_dir, xcms_params, polarity_mode,
           # Optional params below. To set them, include
           # a summary file or use a preset
           # peak detection params
           detection_method='centWave', ppm=25,
           peak_width=c(10,60), prefilter=c(3,100),
           # grouping parameters
           bw=20, mzwid=0.025, minfrac=0, minsamp=5,
           # retention-correction parameters
           retcor_method='loess', missing=1, extra=1) {


    # wrtie parameters to file
    peak_width_str = paste(paste(peak_width), collapse=" ")
    prefilter_str = paste(paste(prefilter), collapse=" ")

    gen_params = sprintf(
"### General Parameters
polarity_mode\t%s", polarity_mode
    )
    
    peak_pick_params = sprintf(
"### Peak Detection Parameters
peak_picking\t%s
ppm\t%s
peak_width\t%s
prefilter\t%s", param_defined(xcms_params, 'detection_method',
                              detection_method),
                param_defined(xcms_params, 'ppm', ppm), 
                param_defined(xcms_params, 'peakwidth',
                              peak_width_str), 
                param_defined(xcms_params, 'prefilter', 
                              prefilter_str)
    )
    

    peak_group_params = sprintf(
"### Peak-grouping parameters
bw\t%s
mzwid\t%s
minfrac\t%s
minsamp\t%s
",  param_defined(xcms_params, 'bw', bw),
    param_defined(xcms_params, 'mzwid', mzwid), 
    param_defined(xcms_params, 'minfrac', minfrac), 
    param_defined(xcms_params, 'minsamp', minsamp)
    )
    
    retcor_params = sprintf(
"### retention-correction parameters
retcor_method\t%s
missing\t%s
extra\t%s
",
    param_defined(xcms_params, 'retcor_method', 
                  retcor_method), 
    param_defined(xcms_params, 'missing', missing), 
    param_defined(xcms_params, 'extra', extra)
    )
    
    param_string = paste(gen_params, peak_pick_params,
                         peak_group_params, retcor_params,
                         sep='\n')
    print(param_string)
    filename = sprintf('/xcms_params_%s.tsv', args$study)
    print(filename)
    params_file = paste(output_dir, filename, sep='')
    write(param_string, file=params_file)
}


param_defined = function(xcms_params, param_name, default_param) {
    # Check if particular parameter, param, defined by user in xcms_params
    # INPUT
    #    default_param - various (mostly string or list)
    #    param - string
    #    xcms_params - named list
    #print(paste('param_name', param_name, sep=' '))
    #print(paste('default', default_param, sep=' '))
    #print(paste('output?', xcms_params[param_name], sep=' '))
    # If find parameter in xcms params, return it
    #print(!is.null(xcms_params[[param_name]]))
    if (!is.null(xcms_params[[param_name]])) {
        # The paste(paste()) is a a hacky way to print out 
        # a list with two entries as as a space-delimited string, 
        # because fuck R
        return(paste(paste(xcms_params[[param_name]]), collapse=" "))
    } else {
        #print('DIDN"T FIND IT')
        return(default_param)
    }
}


# If any of these things are null, raise a friendly error message
if (is.null(args$output) | is.null(args$polarity) | is.null(args$study)){
    stop("When calling the function, you need to specify an
	 output directory (--output), 
	 and polarity mode (--polarity),
	 and study name to proceed. 
	 type --help to learn more about the parameters") 
}


# If a preset is given, write a filled-in summary file out
if (is.character(args$preset)) {
    print('PRESET IS A THING')
    # get the parameters if given preset
    xcms_params <- default_params(args$preset)
    print( xcms_params)
    # Write to file 
    write_params(args$output, xcms_params, 
                 args$polarity) 
} else {
    # pass
    generate_blank_summary_file(args$output, args$study)
}



