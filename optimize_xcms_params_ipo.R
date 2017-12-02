library(optparse)
#library(IPO)
#library(snowfall)
library(yaml)
library(BiocParallel)

parser <- OptionParser()
# parser <- add_option(parser, c('--data', '-d'), type='character',
#		     help=paste('Path to data. Required'))
parser <- add_option(parser, c('--output', '-o'), type='character',
		     help=paste('Path to output directory'))
parser <- add_option(parser, c('--yaml', '-y'), type='character',
		     help=paste('Path to yaml file with name of study
				chromatography used, and instrument type'))
parser <- add_option(parser, c('--local'), type='character',
                     help=paste('Required. Local path to the project '))
parser <- add_option(parser, c('--cores'), type='integer',
                     default = 4,
                     help=paste('Optional, number of cores to 
                        run things with'))
args = parse_args(parser)

# Set number of cores to use
print(paste('Number of cores ', args$cores))
register(MulticoreParam(args$core))
print(bpparam())


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
  prefilter_number = instrument_params[[mass_spec]][['prefilter']][1]
  prefilter_intensity = instrument_params[[mass_spec]][['prefilter']][2]

  # Edit the parameters for IPO to optimize  
  peak_picking_params$min_peakwidth = c(min_peakwid - (min_peakwid / 2), min_peakwid + (min_peakwid / 2))
  peak_picking_params$max_peakwidth = c(max_peakwid - (max_peakwid / 2), max_peakwid + (max_peakwid / 2))
  peak_picking_params$ppm = c(my_ppm - (my_ppm/2), my_ppm + (my_ppm/2))
  # peak filter intensity value
  peak_picking_params$value_of_prefilter = c( prefilter_intensity - (prefilter_intensity / 3),
                                              prefilter_intensity + (prefilter_intensity / 3))
  peak_picking_params$prefilter = prefilter_number
  # allow overlapping peaks
  peak_picking_params$mzdiff = -0.001
  
  # IPO retention time correction params
  retcor_params = IPO::getDefaultRetGroupStartingParams()
  retcor_params$bw = chromatograph_params[[chromatography]][['bw']]
  
  # Just require 1 sample to define a group, especially for optimization, since you're only using 5-ish samples
  retcor_params$minfrac = 0
  retcor_params$minsamp = 1
  # TODO do I want to optimize gapInit, gapExtend, profStep?
  #retcor_params$profStep = 1

  return(list("peak_pick_params" = peak_picking_params, 
              "retcor_params" = retcor_params))
}


write_final_params <- function(peak_picking_params,
                         retcor_params, 
                         output_file_path) {
	# write out the optimized parameters
  # INPUT - output_file_path - whole-path, including filename
  #   params - named list containing parameters
  general_peak_pick_params = sprintf(
"### Peak Detection Parameters
peak_picking\t%s
ppm\t%s
peak_width\t%s %s
prefilter\t%s %s",
    "CentWave", peak_picking_params$ppm,
    peak_picking_params$min_peak_width, peak_picking_params$max_peakwidth,
    peak_picking_params$prefilter, peak_picking_params$value_of_prefilter
)
  print('Printing shit that will become a file')
  print(general_peak_pick_params)
  print(peak_picking_params$ppm)
}

yaml_path = args$yaml
ouput_path = args$output
local_path = args$local

### Debugging stuff
output_path = '~/Dropbox (MIT)/Alm_Lab/projects/revo_healthcare/user_input/xcms_parameters'
#print(yaml_path)
yaml_path = '~/Dropbox (MIT)/Alm_Lab/projects/revo_healthcare/user_input/organize_raw_data/organize_data_MTBLS315.yaml'

# TODO get local_path programatically - look for .home file or something like that
local_path = '~/Dropbox (MIT)/Alm_Lab/projects/revo_healthcare/'
###

# a named list containing the path to data and the xcms parameters to use
parameters_all_assays = parse_yaml(yaml_path)

# loop through all the assays. write out the parameters
# from initial attempt
# then do the peak-picking optimization, write params
# then do retcor optimization, write all the params,
# then just write the params to be used by xcms? (b/c all params are overkill) or just order them better

study = parameters_all_assays$Study
print(study)
for (assay_name in names(parameters_all_assays[c(-1)])) { # first entry is study name
  print(assay_name)
  initial_params_output = paste(output_path, sprintf('.unoptimized_params_%s_%s.Rdata',
                                   study, assay_name), sep='/')
  
  print(parameters_all_assays[[assay_name]])  # Write the initial parameters as Rdata format, since you don't really need them that much
  #saveRDS(parameters_all_assays[assay_name], initial_params_output)
  
  # select files to use
  # TODO make this os-nonspecific (don't use forward/backslashes)
  data_path = paste(local_path, parameters_all_assays[[assay_name]]$data_path, sep='/')
  file_list = list.files(data_path)
  
  # Run IPO on peak_picking
  set.seed(1)
  num_files = 2 # use 2 when debugging
  random_files = paste(data_path, sample(file_list, num_files), sep='')
  print(random_files)
  print('Starting to optimize peak_picking_params')
  optimized_params_peak_picking = system.time(IPO::optimizeXcmsSet(files = random_files,
                                                       params = parameters_all_assays[[assay_name]]$peak_pick_params,
                                                       plot=TRUE,
                                                       nSlaves=0))
  saveRDS(optimized_params_peak_picking, 'optimized_peak_params.Rdata')
  # Run IPO on retcor from the same random set of files
  optimized_params_retention_correction = system.time(IPO::optimizeRetGroup(xset = optimized_params_peak_picking$best_settings$xset,
                                                                params = parameters_all_assays[[assay_name]]$retcor_params,
                                                                plot=TRUE,
                                                                nSlaves=0))
  saveRDS(optimized_params_retention_correction, 'optimized_retcor_params.Rdata')
  
}


