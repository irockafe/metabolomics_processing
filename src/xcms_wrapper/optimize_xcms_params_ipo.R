library(optparse)
#library(IPO)
#library(snowfall)
library(yaml)
library(BiocParallel)

parser <- OptionParser()
# parser <- add_option(parser, c('--data', '-d'), type='character',
#		     help=paste('Path to data. Required'))
parser <- add_option(parser, c('--output', '-o'), type='character',
		     help=paste('Path where xcms_parameter will be output'))
parser <- add_option(parser, c('--yaml', '-y'), type='character',
		     help=paste('Path to yaml file with name of study
				chromatography used, and instrument type'))
parser <- add_option(parser, c('--assay', '-a'), type='character',
			default='all', help=paste('Which assay, listed in the yaml
                        file do you want to parametrize through IPO? Default is
                        to process all assays. If not choosing all assays, you can only list one assay'))
parser <- add_option(parser, c('--cores'), type='integer',
                     default = 4,
                     help=paste('Optional, number of cores to 
                        run things with'))
parser <- add_option(parser, c('--numFiles'), type='character',
                     default=5, help=paste('Number of files to use when optimizing xcms parameters'))
args = parse_args(parser)



parse_yaml <- function(yaml_path) {
# Parse the yaml file, return the 
# data location, and xcms parameters (peak-pick and group)
# based on the chromatography-type and mass-spectrometer used
# (both those pieces of info are in the yaml file,
  # a named list
  yaml_info = yaml.load_file(yaml_path)
  study = names(yaml_info)
  print(study)
  aggregator = list('Study' = study)
  
  for (assay in names(yaml_info[[study]][['assays']] )) {
    print(assay)
    chromatography = (yaml_info[[study]] [['assays']] [[assay]] [['chromatography']])
    mass_spec = (yaml_info[[study]] [['assays']] [[assay]] [['mass_spectrometer']])
    data_path = (yaml_info[[study]] [['assays']] [[assay]] [['data_path']])
    all_params = get_initial_params(mass_spec, chromatography)
    peak_pick_params = all_params[['peak_pick_params']]
    retcor_params = all_params[['retcor_params']]
    # add to aggregator
    varname = paste(assay)
    aggregator[[assay]] = list('data_path'=data_path, 
                               'peak_pick_params' = peak_pick_params,
                               'retcor_params' = retcor_params )
  }

  return(aggregator)
}


get_initial_params <- function(mass_spec, chromatography) {
  # get default xcms params and modify them based on 
	# the chromatography used (hplc, uhplc) 
	# and instrument type (orbitrap,
	# qtof, qtof_hires)
  # INPUT - type of mass spectrometer (qtof, qtof_hires, orbitrap)
  #    type of chromatography (hplc, uplc)
  # OUTPUT - peakPickingParams & Retetnetion-correction-params for IPO
  #   also output the params from Patti et. al in case need them for
  #   the future
  
  # Get default params from IPO
  peak_picking_params <- IPO::getDefaultXcmsSetStartingParams('centWave')
  
  # dictionaries to replace stuff with
  # Values from Patti et al 2012 metaXCMS paper
  instrument_params = list(
    qtof = list(ppm=30, peakwidth=c(10,60), prefilter=c(0,0)),
    qtof_hires = list(ppm=15, peakwidth=c(10,60), prefilter=c(0,0)),
    orbitrap = list(ppm=2.5, peakwidth=c(5,20), prefilter=c(3,5000))
    )
  chromatograph_params = list(
    uplc = list(bw=c(2,5)),
    hplc = list(bw=c(4,7))
    )
  
  # Change some of the defaults, based on type of
  # chromatography and instrument used
  min_peakwid = instrument_params[[mass_spec]][['peakwidth']][1]
  max_peakwid = instrument_params[[mass_spec]][['peakwidth']][2]
  my_ppm = instrument_params[[mass_spec]][['ppm']]
  prefilter_number = 0  # because we're dealing with small subset of actual number of files
  prefilter_intensity = instrument_params[[mass_spec]][['prefilter']][2]

  # Edit the parameters for IPO to optimize  
  peak_picking_params$min_peakwidth = c(min_peakwid - (min_peakwid / 2), min_peakwid + (min_peakwid / 2))
  peak_picking_params$max_peakwidth = c(max_peakwid - (max_peakwid / 2), max_peakwid + (max_peakwid / 2))
  peak_picking_params$ppm = my_ppm + 1.5 # TODO just for testing, b/c I know that 4ppm is a decent choice
  # peak filter intensity value
  peak_picking_params$value_of_prefilter = c( prefilter_intensity - (prefilter_intensity / 3),
                                              prefilter_intensity + (prefilter_intensity / 3))
  peak_picking_params$prefilter = prefilter_number
  # allow overlapping peaks
  peak_picking_params$mzdiff = -0.001
  
  # IPO retention time correction params
  retcor_params = IPO::getDefaultRetGroupStartingParams()
  retcor_params$bw = chromatograph_params[[chromatography]][['bw']]
  # Don't deal with these params, just use defaults
  retcor_params$gapInit = 0.3  # Default for xcms using cor_opt distance fxn
  retcor_params$gapExtend = 2.4  # Default for xcms using cor_opt distance fxn
  retcor_params$profStep = 1
  
  # Just require 1 sample to define a group, especially for optimization, since you're only using 5-ish samples
  retcor_params$minfrac = 0
  retcor_params$minsamp = 1
  # TODO do I want to optimize gapInit, gapExtend, profStep?
  #retcor_params$profStep = 1

  return(list("peak_pick_params" = peak_picking_params, 
              "retcor_params" = retcor_params))
}


write_params <- function(ipo_params, total_files,
                         output_file_path) {
	# write out the optimized parameters
  # INPUT - output_file_path - whole-path, including filename
  #   ipo_params - named list containing parameters from IPO
  # total_files - the total number of Mass-Spec files that will be processed
  #     Use this to set the minimum samples needed to define a group, and possibly to prefilter
  # First write out the most important parameters
  
  # Print out for debugging purposes
  print(ipo_params)  

  peak_pick_params = sprintf(
"### Peak Detection Parameters
peak_picking\t%s
ppm\t%s
peak_width\t%s %s
prefilter\t%s %s
",
    "CentWave", ipo_params$ppm,
    ipo_params$min_peakwidth, ipo_params$max_peakwidth,
    ipo_params$prefilter, ipo_params$value_of_prefilter
  )
  peak_group_params = sprintf(
    "### Peak-grouping parameters
bw\t%s
mzwid\t%s
minfrac\t%s
minsamp\t%s
",  ipo_params$bw,
    ipo_params$mzwid, 
    ipo_params$minfrac, 
    ceiling(total_files / 10) # default to 10% of samples as minimum needed for a group
  )
  
  retcor_params = sprintf(
    "### retention-correction parameters
retcor_method\t%s
",
    ipo_params[['retcorMethod']]
  )
  
  # Then define the ones that we care less about
  already_used_params = c('ppm', 'min_peakwidth', 'max_peakwidth',
                          'prefilter', 'value_of_prefilter',
                          'bw', 'mzwid', 'minfrac', 'minsamp',
                          'retcor_method')
  
  other_params = '### Other parameters'
  for (name in names(ipo_params)){
    # skip to next entry if already wrote it earlier
    if (name %in% already_used_params) {
      next
    }
    # write to new line, tab-delimited
    other_params = paste(other_params, sprintf('\n%s\t%s', name, ipo_params[name]), sep='')
  }
  print(names(ipo_params))
  print(other_params)
  param_string = paste(peak_pick_params,
                       peak_group_params, retcor_params,
                       other_params,
                       sep='\n')
  print(peak_pick_params)
  print(param_string)
  write(param_string, file=output_file_path)
}


run_ipo <- function(assays, local_path, study, parameters_all_assays, num_files, output_path) {
  # GOAL: Run IPO to optimize selected xcms parameters
  # INPUT: assays: a list of assay names that should match the yaml file
  #    local_path: the git repo's home path
  #    study: The unique name of study (usually MTBLS or STxxx), taken from the yaml file.
  #    parameters_all_assays: baseline IPO parameters, generated with parse_yaml(). 
  #         These parameters vary depending on the Mass Spec used and the chromatography listed
  #         in the yaml file. See get_initial_params() for the types currently supported
  #    num_files: The number of files in the data/raw/{study}/{assay} directory
  #         that will be processed. The data directory should only contain raw data files for this reason
  #         This number will be used to set the minimum number of samples that must be in a group
  #         for xcms grouping. Default fraction is set in write_params()
  # OUTPUT: 
  #    unoptimized parameters: /user_input/xcms_parameters/unoptimized_xcms_params_{study}_{assay}.tsv
  #    optimized peak parameters (Rdata)
  #    optimized retcor parameters (Rdata)
  #    final xcms parameters (tsv): /user_input/xcms_parameters/xcms_params_{study}_{assay}.tsv
  
  for (assay_name in assays) { # first entry is study name
    processed_data_path = file.path(local_path, sprintf('data/processed/%s/%s/', study, assay_name))
    print(processed_data_path)
    dir.create(processed_data_path, recursive=TRUE)
    setwd(processed_data_path)
    print(assay_name)
    
    # If assay name is wrong, print message and stop code
    if (is.null(parameters_all_assays[[assay_name]])){
      stop('The assay name provided was not found in the yaml file. Check the spelling on the --assay flag, or
           check the spelling of the yaml file (user_input/study_info/))')
    } else{
      print(paste('About to start on: ', assay_name))
    }
    
    # select files to use
    data_path = file.path(local_path, parameters_all_assays[[assay_name]]$data_path)
    file_list = list.files(data_path)
    total_files = length(file_list)
    
    # Write the initial parameters for future reference
    initial_params = c(parameters_all_assays[[assay_name]]$peak_pick_params, 
                       parameters_all_assays[[assay_name]]$retcor_params)
    initial_param_path = file.path(local_path, output_path, sprintf('unoptimized_xcms_params_%s_%s.tsv',
                                                       study, assay_name))
    
    write_params(initial_params, total_files, initial_param_path)
    
    # Run IPO on peak_picking
    set.seed(1)
    random_files = file.path(data_path, sample(file_list, num_files))
    print(random_files)
    print('Starting to optimize peak_picking_params')
    t1 = timestamp()
    optimized_params_peak_picking = IPO::optimizeXcmsSet(files = random_files,
                                                         params = parameters_all_assays[[assay_name]]$peak_pick_params,
                                                         plot=TRUE,
                                                         nSlaves=0  # because default is 4, which causes an error since we're using bpparam()
    )
    t2 = timestamp()
    message(paste('Started to optimize xcmsSet params at ', t1))
    message(paste('Finished optimizing xcmsSet params at ', t2))
    saveRDS(optimized_params_peak_picking, file.path(processed_data_path, 
                                                     'optimized_peak_params.Rdata'))
    
    # Run IPO on retcor from the same random set of files
    message('Starting retcor optimization')
    t1 = timestamp()
    optimized_params_retention_correction = IPO::optimizeRetGroup(xset = optimized_params_peak_picking$best_settings$xset,
                                                                  params = parameters_all_assays[[assay_name]]$retcor_params,
                                                                  plot=TRUE,
                                                                  nSlaves=0)
    t2 = timestamp()
    message(paste('Started to optimize grouping params at ', t1))
    message(paste('Finished optimizing grouping params at ', t2))
    saveRDS(optimized_params_retention_correction, paste(processed_data_path,
                                                         'optimized_retcor_params.Rdata', sep='/'))
    
    # Finally, write the best parameters out to a file
    optimized_param_output = file.path(local_path, output_path, sprintf('xcms_params_%s_%s.tsv',
                                                           study, assay_name))
    params = c(optimized_params_peak_picking$best_settings$parameters, optimized_params_retention_correction$best_settings)
    write_params(params, total_files, optimized_param_output)
  }
}


# Set number of cores to use
print(paste('Number of cores ', args$cores))
register(MulticoreParam(args$core))
print(bpparam())

yaml_path = args$yaml
output_path = args$output
num_files = args$numFiles


"
####### debug shit
peak_params = readRDS('optimized_peak_params.Rdata')
retcor_params = readRDS('optimized_retcor_params.Rdata')
params = c(peak_params$best_settings$parameters, retcor_params$best_settings)
yaml_path = file.path(local_path, 'user_input/study_info/MTBLS315.yaml')
print(yaml_path)
####### debug shit
"

local_path = system('git rev-parse --show-toplevel', intern=TRUE)

# get a named list containing the path to data and the initial xcms parameters to use
# based on the instrument type and chromatography listed in the yaml file
parameters_all_assays = parse_yaml(yaml_path)


# then do the peak-picking optimization, write params
# then do retcor optimization, write all the params,
# then just write the params to be used by xcms? (b/c all params are overkill) or just order them better

study = parameters_all_assays$Study
print(paste('Study: ', study))

# Run on all assays found in the yaml file, unless args$assay != 'all'
# then run only on a single assay
if (args$assay =='all') {
  assays = names(parameters_all_assays[c(-1)])
} else {
  assays = args$assay
}

# Loop through assays and run IPO, outputting peak_picking, retcor parameters, and 
# finally writing the parameters to be used by xcms
run_ipo(assays, local_path, study, parameters_all_assays, num_files, output_path)
