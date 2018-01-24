import os
import xml.etree.cElementTree as ET
import numpy as np
import re
from specie import Specie
from parse_XML import parse


class Experiment:
    def __init__(self, filepath, epoch, use_properties):
        # do we want to use properties as labels
        self.label_props = use_properties
	# define our filepath for parsing using the source file input
        self.source_file = filepath
        # create a source file for the properites file parsing
        self.properties_file = filepath
	# get our name from the experiment name in the filepath, i.e. 'zsierp_04_13_random_experiment'
        self.name = os.path.basename(os.path.normpath(filepath))
	# cat on DATA_DIR manually so we can begin to build our parsing filepath
        self.source_file += 'DATA_DIR/'
        # check to make sure that we have a DATA_DIR inside the current experiment folder
        if not os.path.exists(self.source_file):
            print("WARNING! %s does not exist!" % self.source_file)
            quit(1)
        # cat on JOBS_DIR so we can manually build our properties path
        self.properties_file += 'JOBS_DIR/'
        # check to make sure there is a JOBS_DIR
        if not os.path.exists(self.properties_file):
            print("WARNING! %s does not exist!" % self.properties_file)
            quit(1)
	# set our epoch modifier based on the given input epoch
        self.epoch_modifier = epoch
	# a number to store how many generations there should be (specified by the xml file)
        self.generation_count = None

        self.max_fit_by_job = []  # 2D array to store max fitness values of each job (i.e. index 0 returns max fitness values of job 1
        self.avg_fitness_by_job = [] # 2D array to store average fitness values from each job
        self.min_fitness_by_job = [] # 2D array to store minimum fitness values from each job

        self.champ_comp_by_job = [] # 2D array, same as max_fit_by_job but with champion complexity values
        self.max_comp_by_job = []   # 2D array to store max complexity values from each job
        self.min_comp_by_job = []  # 2D array to store minimum complexity values from each job
        self.avg_comp_by_job = []  # 2D array to store average complexity values from each job

        self.species_by_job = [] # Contains all the species values per job
        self.average_max_species = [] # average arrays for the percent above threshold
        self.average_min_species = []
        self.average_avg_species = []

        self.average_max_fitness = None # 1D array to store the average maximum fitness, calculated using all jobs
        self.average_min_fitness = None # 1D array to store the average minimum fitness values, calculated from all jobs
        self.average_avg_fitness = None # 1D array to store the average of teh average fitness values, calculated from all jobs

        self.average_champ_complexity = None  # Like average_max_fitness but with champion complexity
        self.average_max_complexity = None # 1D array to store the average maximum complexity
        self.average_min_complexity = None # 1D array to store the average minimum complexity
        self.average_avg_complexity = None # 1D array to store the average of the average complexity

        self.max_fitness_deviation = None  # Store the deviation data of average_fitness
        self.min_fitness_deviation = None
        self.avg_fitness_deviation = None

        self.champ_complexity_deviation = None  # Store the deviation data of average_complexity
        self.max_complexity_deviation = None
        self.min_complexity_deviation = None
        self.avg_complexity_deviation = None

        # create an array to store each jobs properties #SUMMARY
        self.job_summaries = []

        # walk the directory to determine the number of jobs we need to parse. walk_dir will automatically call the parse function to extract the data
        self.walk_dir()
	# calculate_data uses the parsed information to calculate averages, std deviation, etc.
        self.calculate_data()

    def parse_properties(self, filepath, job_number):
        path = os.path.join(filepath, 'job_%i.properties' % job_number)
        with open(path) as docfile:
            lines = docfile.readlines()
        # get the first line from the file
        new_line = lines[0]
        new_line.strip()
        # check to make sure we have the right line for processing
        test_line = new_line[0:16]
        if '#SUMMARY' not in test_line:
            self.label_props = False
            return
        # remove the beginning SUMMARY tag and the final comma
        new_line = new_line[16:-2]
        # split the line into sections to remove extra info
        params = new_line.split(',')
        # clear string for later apending
        new_line = ''
        # for every substring, remove everything up to and including the arrow
        for s in params:
            # replace everything up to the arrow with a comma to reduce steps
            s = re.sub('^.+->', ',', s, flags=re.M)
            # append substring on to new_line to build final string
            new_line += s
        # add string to job_summaries for later use
        self.job_summaries.append(new_line)

    # walk_dir : File -> Null
    # pulls data from xml files and adds it to arrays for later calculation
    def walk_dir(self):
        input_directory = self.source_file
        # walk through specific subdirs of input_dir
        # GO INTO DATA_DIR
        # GO INTO EACH JOB
        # GO INTO RUN DIRECTORY
        # PARSE run0.xml

        # walk through all subdirectories, directories, and files in our input directory
        job_count = 1
        for subdir, dirs, files in os.walk(input_directory):
            for directory in dirs:
                if 'job_' in directory:
                    job_count += 1

        if job_count > 1:
            parse(self, job_count)
        else:
            print("No jobs detected in %s" % input_directory)
            quit(1)

    # get aggregate arrays for correction
    def get_aggregates(self):
        return [self.max_fit_by_job, self.min_fitness_by_job, self.avg_fitness_by_job, self.champ_comp_by_job, self.max_comp_by_job, self.min_comp_by_job, self.avg_comp_by_job]

    # return a list of all arrays containing averages for correction in xparse.py
    def get_average_arrays(self):
        return [self.average_max_fitness, self.average_min_fitness, self.average_avg_fitness, self.average_champ_complexity, self.average_max_complexity, self.average_min_complexity, self.average_avg_complexity]

    # return a list of all deviation arrays for correction in xparse.py
    def get_deviation_arrays(self):
        return [self.max_fitness_deviation, self.min_fitness_deviation, self.avg_fitness_deviation, self.champ_complexity_deviation, self.max_complexity_deviation, self.min_complexity_deviation, self.avg_complexity_deviation]

    def correct_outlier(self, array, count):
        # get the final value of the array
        final_value = array[-1]
        # determine if array is a numpy array or list
        if type(array).__module__ == np.__name__:
            # if numpy, array must be appended with another array, so we build a list and convert it into an array for appending
            add_list = []
            for i in range(len(array), count):
                add_list.append(final_value)
            add_array = np.asarray(add_list)
            array = np.append(array, add_array)
            print('%s: correcting number of generations for comparison' % self.name)
            return array
        else:
            # if its a list, we can just append it as normal
            for i in range(len(array), count):
                array.append(final_value)
            print("Correction Successful")

    def find_outliers(self, data_set, count):
        if len(data_set) > 1:
            # get the number of jobs from the length of the first array in data_set, max_fit_by_job
            for i in range(0, len(data_set[0])):
                if len(data_set[0][i]) < count:
                    job = i + 1
                    print("job_%i has insufficient generations. Correcting with final valid data point." % job)
                    self.correct_outlier(self.species_by_job[i], count)
                    for data in data_set:
                        try:
                            self.correct_outlier(data[i], count)
                        except:
                            print("Failed to correct job_%i. Exiting..." % job)
                            sys.exit()

    def calculate_data(self):
        # index 0 - 2 == fitness, 3 - 6 == complexity
        to_be_np = [self.max_fit_by_job, self.min_fitness_by_job, self.avg_fitness_by_job,
                      self.champ_comp_by_job, self.max_comp_by_job, self.min_comp_by_job, self.avg_comp_by_job]

        # find the correct number of generations
        correct_generations = int(self.generation_count/self.epoch_modifier) + 1
        # check to see if we have any jobs with missing data. Automatically corrects them if there are
        self.find_outliers(to_be_np, correct_generations)

        total_data = []
        # create numpy arrays for calculating averages and standard deviations
        for array in to_be_np:
            total_data.append(np.asarray(array))

        if len(total_data) > 1:
            # use numpy to calculate the average fitness and compelxity for the entire experiment
            self.average_max_fitness = np.mean(total_data[0], axis=0)
            self.average_min_fitness = np.mean(total_data[1], axis=0)
            self.average_avg_fitness = np.mean(total_data[2], axis=0)

            self.average_champ_complexity = np.mean(total_data[3], axis=0)
            self.average_max_complexity = np.mean(total_data[4], axis=0)
            self.average_min_complexity = np.mean(total_data[5], axis=0)
            self.average_avg_complexity = np.mean(total_data[6], axis=0)

            # use numpy to calculate the standard deviation of max fitness and champ complexity values for the entire experiment
            self.max_fitness_deviation = np.std(total_data[0], axis=0)
            self.min_fitness_deviation = np.std(total_data[1], axis=0)
            self.avg_fitness_deviation = np.std(total_data[2], axis=0)

            self.champ_complexity_deviation = np.std(total_data[3], axis=0)
            self.max_complexity_deviation = np.std(total_data[4], axis=0)
            self.min_complexity_deviation = np.std(total_data[5], axis=0)
            self.avg_complexity_deviation = np.std(total_data[6], axis=0)

    # takes a threshold value and an array of species, and returns a list of the percentage of species above the threshold at each generation
    def calculate_threshold_percentage(self, threshold, identifier):
        i = identifier.lower()
        percentages_by_job = []
        # each job contains a list of generations
        for job in self.species_by_job:
            percent_by_gen = []
            # each generation contains a list of species
            for gen in job:
                # keep track of how many species have a fitness higher than the threshold
                p_counter = 0
                # loop through species for comparisons
                for specie in gen:
                    # use identifier to determine which values to retrieve for comparison
                    fitness = getattr(specie, "get_%s_chromosome_fitness" % identifier)()
                    if fitness > threshold:
                        p_counter += 1
                # divide by the number of species to get the percentage
                percent = p_counter/len(gen) * 100
                # add this generations percentage to a list
                percent_by_gen.append(percent)
            # add this jobs list of percentages by generation to a list
            percentages_by_job.append(percent_by_gen)
        return percentages_by_job

    def get_species_count(self):
        count_by_job = []
        for job in self.species_by_job:
            count_by_gen = []
            for gen in job:
                count_by_gen.append(len(gen))
            count_by_job.append(count_by_gen)
        return count_by_job
