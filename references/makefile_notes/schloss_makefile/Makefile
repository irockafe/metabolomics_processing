# Globals
STUDIES = baxter escobar hmp ross schubert turnbaugh wu zupancic goodrich zeevi
REFS = data/references
PROC = data/process

################################################################################
#
#	Part 2: Get shared file, taxonomy data, representative sequence, distance
#	matrix, and metadata from individual studies
#
################################################################################

STUB = $(foreach S, $(STUDIES), data/$(S)/$(S))

ALPHA = $(addsuffix .groups.ave-std.summary,$(STUB))
BETA = $(addsuffix .braycurtis.0.03.lt.ave.dist,$(STUB))
SHARED = $(addsuffix .0.03.subsample.shared,$(STUB))
FASTA = $(addsuffix .rep.fasta,$(STUB))
TAXONOMY = $(addsuffix .taxonomy,$(STUB))
METADATA = $(addsuffix .metadata,$(STUB))

poop:
data/%.groups.ave-std.summary\
	data/%.braycurtis.0.03.lt.ave.dist\
	data/%.0.03.subsample.shared\
	data/%.rep.fasta\
	data/%.taxonomy\
	data/%.metadata : code/$$(notdir $$*).batch code/$$(notdir $$*).R\
			$(REFS)/silva.seed.align $(REFS)/silva.v4.align\
 			$(REFS)/trainset14_032015.pds.fasta\
			$(REFS)/trainset14_032015.pds.tax
	bash $<
