import configparser as cp
import os
import sys
import matplotlib
import math
import re

# take a string, and determine if it is empty. If it is empty, return None. If it contains characters, replace spaces with underscores and return the string.
def parse_name(s):
    # check to see if the string s contains any letters
    if re.search('[a-zA-Z]', s):
        s = s.strip()
        # remove any special characters
        s = re.sub(r"[^a-zA-Z]+", ' ', s)
        print('CUSTOM NAME: %s' % s)
        return s
    # if it doesn't, we return None
    else:
        print("INVALID OR NO CUSTOM NAME DETECTED.")
        return None


class Config:
    def __init__(self, config_file):
        # create configparser object
        config = cp.ConfigParser()
        # read the input config file
        config.read(config_file)
########DEFINE CONFIG VARIABLES########
        # get the offset
        self.offset = int(config['OffsetOptions']['offset'])

        # determine whether or not we want to use error bars
        self.shaded_region = self.string_to_bool(config['OffsetOptions']['shaded_region'])

        self.bar_graphs = self.string_to_bool(config['LabelOptions']['plot_bar_comparison'])
        self.bar_ecolor = config['LabelOptions']['bar_ecolor']
        self.agg_ls = config['LabelOptions']['agg_ls']

        self.save_path = config['OutputSection']['plot_output_filename']
        # get the custom name
        self.custom_name = parse_name(config['OutputSection']['custom_name'])
        # whether we show the plots or save them
        self.show_plots = self.string_to_bool(config['OutputSection']['show_plot_output'])
        self.save_plots = self.string_to_bool(config['OutputSection']['save_plot_output'])
        # labeling properties
        self.use_legend = self.string_to_bool(config['LabelOptions']['use_legend'])
        self.use_properties = self.string_to_bool(config['LabelOptions']['use_legend'])
        # We need to make sure we don't pass the simplify legend as a None value later, so we initialize it to false here.
        self.simple_legend = False
        # the boolean value for plotting the aggregate data of a properties group
        self.plot_group_agg_fit = False
        # read in our color groups for plotting
        self.colors = config['LabelOptions']['colors']
        if self.colors is not None:
            self.parse_colors()
        # if we want to use properties, try to parse the properties groups
        if self.use_properties:
            self.properties_groups = config['LabelOptions']['properties_groups']
            # parse the properties groups into a list 
            self.parse_prop_groups(self.properties_groups)
            # reiterate the propertie groups to the user so they are aware of their selection if it needs changes.
            print("GROUPING BY PROPERTIES: " + str(self.properties_groups))
            # Get the bool for simplifying the legend
            self.simple_legend = self.string_to_bool(config['LabelOptions']['simplify_legend'])
            # we are using properties groups, so we need to get the boolean value
            self.plot_groups = self.string_to_bool(config['LabelOptions']['plot_subgroups'])
        #parse fitness variables
        self.show_max_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_max_fitness'])
        self.show_mean_max_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_mean_max_fitness'])
        self.show_min_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_min_fitness'])
        self.show_mean_min_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_mean_min_fitness'])
        self.show_avg_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_avg_fitness'])
        self.show_mean_avg_fitness = self.string_to_bool(config['PlotOptionsFitness']['show_mean_avg_fitness'])

        # parse complexity variables
        self.show_champ_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_champ_complexity'])
        self.show_mean_champ_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_mean_champ_complexity'])
        self.show_max_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_max_complexity'])
        self.show_mean_max_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_mean_max_complexity'])
        self.show_min_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_min_complexity'])
        self.show_mean_min_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_mean_min_complexity'])
        self.show_avg_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_avg_complexity'])
        self.show_mean_avg_comp = self.string_to_bool(config['PlotOptionsComplexity']['show_mean_avg_complexity'])

        # parse species variables
        self.show_species_count = self.string_to_bool(config['PlotOptionsSpecies']['show_species_count'])
        self.show_percent_max = self.string_to_bool(config['PlotOptionsSpecies']['show_percent_max_threshold'])
        self.show_percent_avg = self.string_to_bool(config['PlotOptionsSpecies']['show_percent_avg_threshold'])
        self.show_percent_min = self.string_to_bool(config['PlotOptionsSpecies']['show_percent_min_threshold'])
        self.show_aggregate_species = self.string_to_bool(config['PlotOptionsSpecies']['species_comparison'])
        self.max_thresh = int(config['PlotOptionsSpecies']['max_threshold'])
        self.avg_thresh = int(config['PlotOptionsSpecies']['avg_threshold'])
        self.min_thresh = int(config['PlotOptionsSpecies']['min_threshold'])

        # parse comparison variables
        self.plot_mean_fitness_vals = self.string_to_bool(config['PlotComparisonOptions']['plot_mean_all_fitness']) # plot comparison of all mean fitness values per experiment
        self.plot_mean_comp_vals = self.string_to_bool(config['PlotComparisonOptions']['plot_mean_all_complexity']) # plot comparison of all mean complexity values per experiment
        self.compare_min_fit = self.string_to_bool(config['PlotComparisonOptions']['compare_min_fitness'])
        self.compare_avg_fit = self.string_to_bool(config['PlotComparisonOptions']['compare_avg_fitness'])
        self.compare_champ_comp = self.string_to_bool(config['PlotComparisonOptions']['compare_champ_complexity'])
        self.compare_max_comp = self.string_to_bool(config['PlotComparisonOptions']['compare_max_complexity'])
        self.compare_min_comp = self.string_to_bool(config['PlotComparisonOptions']['compare_min_complexity'])
        self.compare_avg_comp = self.string_to_bool(config['PlotComparisonOptions']['compare_avg_complexity'])
        self.compare_max_fit = self.string_to_bool(config['PlotComparisonOptions']['compare_maximum_fitness'])
        self.plot_significance = self.string_to_bool(config['PlotComparisonOptions']['plot_significance'])

        #parse standard deviation variables
        self.continuous_lines = self.string_to_bool(config['PlotDeviationComparisonOptions']['continuous_lines'])
        self.point_size = config['PlotDeviationComparisonOptions']['point_size']
        self.cap_size = int(config['PlotDeviationComparisonOptions']['error_cap_size'])
        self.transparency = float(config['PlotDeviationComparisonOptions']['significance_transparency'])

        # get the epoch modifier
        self.epoch_modifier = int(config['PlotOptionsEpoch']['epoch_size'])
        # check for any config parsing errors
        self.check_errors()
    
    # custom function to split the colors string into a list
    def split_colors(self, s):
        # final array of individual colors
        array = []
        # what bracket level are we working in (should never exceed 1)
        bracket_lvl = 0
        # an array of characters to build the current string
        current_string = []
        # loop through characters in string to find colors and brackets
        # add the comma at the end to ensure we dont miss the final chars
        for c in (s + ","):
            # make sure we don't pick up spaces UNLESS we are dealing with an rgb tuple
            if c == " " and bracket_lvl == 0:
                continue 
            if c == "," and bracket_lvl == 0:
                # convert our list of characters into a string
                array.append("".join(current_string))
                # reset current to empty array for next string
                current_string = []
            else:
                if c == "(":
                    bracket_lvl += 1
                elif c == ")":
                    bracket_lvl -= 1
                current_string.append(c)
        return array

    # we need to look through the list of colors for rgb tuples
    def find_tuples(self):
        # loop through the strings in self.colors
        for i in range(len(self.colors)):
            s = self.colors[i]
            if s.startswith("(") and s.endswith(")"):
                c = s.strip("()")
                array = c.split(",")
                if len(array) == 3:
                    try:
                        array = list(map(int, array))
                        color = tuple(array)
                        self.colors[i] = color
                    except:
                        print("INVALID RGB GROUP IN CUSTOM COLORS: %s. PLEASE USE INTEGERS BETWEEN 1 AND 255.")
                        quit(1)
                else:
                    if len(array) > 3:
                        print("INVALID RGB GROUP IN CUSTOM COLORS: %s. TOO MANY VALUES." % s)
                    if len(array) < 3:
                        print("INVALID RGB GROUP IN CUSTOM COLORS: %s. TOO FEW VALUES." %s)
                    quit(1)

    def parse_colors(self):
        self.colors = self.split_colors(self.colors)
        print("COLORS: " + str(self.colors))
        self.find_tuples()
    
    def string_to_bool(self, s):
        return s.lower() in ('yes', 'true', 't', '1', 'y')

    def parse_prop_groups(self, s):
        if len(s) > 0:
            group_list = s.split(',')
            for i in range(len(group_list)):
                group_list[i] = group_list[i].strip()
            self.properties_groups = group_list
        else:
            proceed = input("'use_properties' is set to true, but no groups have been provided. Would you like to continue without grouping by properties? (y/n)")
            proceed = self.string_to_bool(proceed)
            if not proceed:
                sys.exit()

    def get_new_offset(self):
        # get the new offset
        # prompt the user for input
        new_offset = input("The offset must be less than %i, the epoch size. Please enter new offset, or q to exit.\n" % self.epoch_modifier)
        if new_offset == "q":
            print("Exiting")
            sys.exit()
        new_offset = int(float(new_offset))
        if new_offset > self.epoch_modifier:
            return self.get_new_offset()

        elif new_offset == self.epoch_modifier:
            print("The offset you have selected (%i) is the same as the epoch modifier (%i).\n" % (new_offset, self.epoch_modifier))
            answer = self.string_to_bool(input("Is this correct?\n"))
            if answer:
                print("Setting offset to %i" % new_offset)
                return new_offset
            else:
                return self.get_new_offset()
        else:
            print("Setting offset to %i" % new_offset)
            return new_offset
                  

    def check_errors(self):
        if not self.show_plots:
            matplotlib.use('Agg')
        # check transparency
        trans = self.transparency
        if trans < 0:
            new_trans = trans * -1
            print("Warning! Negative transparency value of %f corrected to positive number %f." % (trans, new_trans))
            self.transparency = new_trans
        if trans > 1 and trans < 100:
            self.transparency = float(trans/100)
        if trans > 100:
            print("Warning! Transparency value of %f greater than 100. Converting to percentage." % trans)
            num_digits = int(math.log10(trans)) + 1
            div = math.pow(10, num_digits)
            self.transparency = trans/div
        # check for the save path
        path = self.save_path
        if not os.path.exists(path):
            os.makedirs(path)
            print("New directory '%s' created." % path)
        # check epoch modifier
        if self.epoch_modifier%1 != 0 or self.epoch_modifier < 0:
            print("epoch_size must be a natrual number.")
            sys.exit()
        # check to make sure the offset is less than the epoch
        if self.offset > self.epoch_modifier:
            # prompt the user for input to insure that they have the proper offset
            self.offset = self.get_new_offset()
        elif self.offset == self.epoch_modifier:
            answer = self.string_to_bool(input("The offset is the same as the epoch. Is this correct?"))
            if not answer:
                self.offset = self.get_new_offset()

    def get_plot_format(self):
        return [self.continuous_lines, self.point_size, self.cap_size, self.transparency]

    def get_species_plot_options(self):
        return [self.show_percent_max, self.show_percent_min, self.show_percent_avg]

    def get_thresholds(self):
        return [self.max_thresh, self.min_thresh, self.avg_thresh]
    
    def get_standard_plot_options(self):
        return [self.show_max_fitness, self.show_mean_max_fitness, self.show_min_fitness, self.show_mean_min_fitness, self.show_avg_fitness, self.show_mean_avg_fitness, self.show_champ_comp, self.show_mean_champ_comp, self.show_max_comp, self.show_mean_max_comp, self.show_min_comp, self.show_mean_min_comp, self.show_avg_comp, self.show_mean_avg_comp]

    def get_deviation_plot_options(self):
        return [self.compare_max_fit, self.compare_min_fit, self.compare_avg_fit, self.compare_champ_comp, self.compare_max_comp, self.compare_min_comp, self.compare_avg_comp]
