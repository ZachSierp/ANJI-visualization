import os
import xml.etree.cElementTree as ET
import experiment
from specie import Specie

def parse(exper, job_count):
# loop throught the number of jobs and parse each filepath
    for i in range(1, job_count):
    # we do not want to alter our original source filepath, so we create a local variable
        curr_dir = exper.source_file
        curr_props = exper.properties_file
        # if we are using label props, gather properties data
        if exper.label_props:
            exper.parse_properties(curr_props, i)
    # we need to add the job directory so we can access the xml file
        curr_dir += 'job_%i/run/' % i
        # get the complete file path of the working xml file
        path = os.path.join(curr_dir, 'run0.xml')
        # setup the tree
        tree = ET.parse(path)

        # get the root of the tree
        root = tree.getroot()

        # array of all the maximum fitness values in the document
        max_fitvals = []
        # array of all the minimum fitness values in the doc
        min_fitvals = []
        # array of all the average fitness values in the doc
        avg_fitvals = []

        # array of all the champion complexity values in the document
        champ_compvals = []
        # array of all the maximum complexity values in the document
        max_compvals = []
        # array of all the minimum complexity values in the document
        min_compvals = []
        # array of all the average complexity values in the document
        avg_compvals = []

        # array of species for this job
        job_species = []

        # keep track of whether or not we are at the proper epoch to pull or skip information
        epoch_index = 0
        if exper.generation_count is None:
            # search paramaters contains all the information on population size and generation size
            search_parameters = root.findall('search-parameters')
            # look at search-paramaters to get the given generation size
            for param in search_parameters:
                for child in param.getchildren():
                    if child.tag == 'generations':
                       exper.generation_count = int(child.text)
        # get all the generation elements so we can walk through them and process data
        gen_list = root.findall('generation')
        # get the last generation element so we can check it and make sure we dont miss the final data point, regardless of epoch modifier
        last_gen = gen_list[-1]

    # go through each generation tag in the xml file for parsing
        for generation in gen_list:
            # need to create a list of species for this generation
            gen_species = []
            # check to see if we are a multiple of the epoch modifier
            if epoch_index % exper.epoch_modifier == (exper.epoch_modifier - 1) or epoch_index == 0 or generation == last_gen:
                # loop through the generation elements subchildren to find fitness and complexity
                for genchild in generation.getchildren():
                    # identify fitness element using .tag
                    if genchild.tag == 'fitness':
                        # loop through children of fitness to find the max fitness
                        for fitchild in genchild:
                            # check if element is max using .tag
                            if fitchild.tag == 'max':
                                # add the value of the max fitness to the array
                                max_fitvals.append(int(fitchild.text))
                            # check if element is min
                            if fitchild.tag == 'min':
                                min_fitvals.append(int(fitchild.text))
                            # check if element is avg
                            if fitchild.tag == 'avg':
                                avg_fitvals.append(float(fitchild.text))
        # repeat above process for complexity
                    if genchild.tag == 'complexity':
                        for compchild in genchild:
                            if compchild.tag == 'champ':
                                champ_compvals.append(int(compchild.text))
                            # check if element is max
                            if compchild.tag == 'max':
                                max_compvals.append(int(compchild.text))
                            # check if element is min
                            if compchild.tag == 'min':
                                min_compvals.append(int(compchild.text))
                            # check if element is avg
                            if compchild.tag == 'avg':
                                avg_compvals.append(float(compchild.text))
                    # get the species of the exper
                    if genchild.tag == 'specie':
                        # create a new specie and add it to the list of species for this generation
                        specie = Specie(genchild.get('id'), genchild.get('count'))
                        # loop through the chromosomes in the specie and create add them to the specie list of chromosomes
                        for schild in genchild:
                            specie.add_chromosome(schild.get('id'), schild.get('fitness'))

                        gen_species.append(specie)

                # increment the epoch_index after we've pulled the data
                epoch_index += 1
            else:
                # even if we don't pull data we still want to increment the epoch_index to keep track of where we are
                epoch_index += 1
            # need to add the list of this generations species to the list of this jobs species by generation
            if len(gen_species) > 0:
                job_species.append(gen_species)
    # add parsed values to global arrays declared in the init function
        exper.max_fit_by_job.append(max_fitvals)
        exper.min_fitness_by_job.append(min_fitvals)
        exper.avg_fitness_by_job.append(avg_fitvals)

        exper.champ_comp_by_job.append(champ_compvals)
        exper.max_comp_by_job.append(max_compvals)
        exper.min_comp_by_job.append(min_compvals)
        exper.avg_comp_by_job.append(avg_compvals)

        exper.species_by_job.append(job_species)
