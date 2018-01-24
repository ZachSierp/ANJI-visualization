# Import the config module so we can create config objects
import config as con
# os gives us the ability to access os console controls and create files
import os
# sys gives us access to files in args
import sys
# matplotlib allows us to plot our data and display it
import matplotlib
# import experiment class to create objects that can store all of our data
import experiment
import numpy as np

# check to make sure we received a config file
config_file = None
for arg in sys.argv:
    if arg.endswith('.ini'):
            config_file = arg
if config_file is None:
    print("Must pass a config file of type .ini!")
    sys.exit()

# create config object
c = con.Config(config_file)

# import plottingfunctions after matplotlib.use has been set
import plottingfunctions as plot

# build our format array so that we can pass it to the plotting tools functions
plot_formats = c.get_plot_format()

# array to store the experiment objects
experiments = []

# go through each input file and create an experiment object
for i in range(1, len(sys.argv)):
    if not sys.argv[i].endswith('.ini'):
        source_file = sys.argv[i]
        source_file.strip()
        if not source_file.endswith('/'):
            source_file += '/'
        experiments.append(experiment.Experiment(source_file, c.epoch_modifier, c.use_properties))

# epoch modifier allows us to step through large datasets quickly, calculating only the values of generations
# divisible by the modifier
# epoch_modifier = 5  epoch modifier should be specified from config file

plot.load(c.show_plots, c.save_plots, c.save_path, c.epoch_modifier, plot_formats, c.use_legend, c.simple_legend, c.plot_groups, c.properties_groups, c.colors, c.custom_name, c.offset, c.shaded_region, c.bar_graphs, c.bar_ecolor, c.agg_ls)

#create list of all the graph labels
labels = ['Max Fitness', 'Minimum Fitness', 'Average Fitness', 'Champion Complexity', 'Max Complexity', 'Minimum Complexity', 'Average Complexity']
# create a list of all the boolean values
show = c.get_standard_plot_options()

# loop through the experiments and plot their data based on parsed config file preferences
for i in range(0, len(experiments)):
    e = experiments[i]
    # get the necessary values from each experiment so we can loop through the bools and plot them
    averages = e.get_average_arrays()
    deviations = e.get_deviation_arrays()
    aggregates = e.get_aggregates()
    name = e.name
    summary = e.job_summaries
    for j in range(len(labels)):
        # there are twice as many bools as labels. This allows us to use the same label for every two bools
        agg = j*2
        mean = agg + 1
        if show[agg]:
            plot.plot_single_experiment_aggregate_data(aggregates[j], labels[j], name, summary)
        if show[mean]:
            plot.plot_std_deviation(averages[j], deviations[j], labels[j], name)
        else:
            continue
    
    # plot all mean fitness values
    if c.plot_mean_fitness_vals:
        plot.plot_all_mean_comparison([averages[0], averages[1], averages[2]], 
                                      ['Mean Max Fitness', 'Mean Min Fitness', 'Mean Avg Fitness'], 'Fitness', name)
    # plot all mean comp values
    if c.plot_mean_comp_vals:
        plot.plot_all_mean_comparison([averages[3], averages[4], averages[5], averages[6]], 
                                       ['Mean Champ Complexity', 'Mean Max Complexity', 'Mean Min Complexity', 'Mean Avg Complexity'], 'Complexity', name)

    # plot the species data
    if c.show_species_count:
        count_by_job = e.get_species_count()
        plot.plot_single_experiment_aggregate_data(count_by_job, "Number of Species per Generation", name, summary)

    # create arrays to store species plotting data for loops
    thresholds = c.get_thresholds()
    species_plots = c.get_species_plot_options()
    identifiers = ['max', 'min', 'avg']
    species_avgs = []
    species_devs = []
    for idx in range(len(species_plots)):
        percent_by_job = e.calculate_threshold_percentage(thresholds[idx], identifiers[idx])
        np_array = np.asarray(percent_by_job)
        species_avgs.append(np.mean(np_array, axis=0))
        species_devs.append(np.std(np_array, axis=0))
        if species_plots[idx]:
            plot.plot_single_experiment_aggregate_data(percent_by_job, "Percent %s Above %i" % (identifiers[idx], thresholds[idx]), name, summary)
        else:
            continue
    if c.show_aggregate_species:
        plot.plot_mean_deviation_comparison(species_avgs, species_devs, ["max", "min", "avg"], e.name, "species_comparison_above_threshold")
 
    # if we are on an odd number experiment we have more than 1 experiment and need to plot comparisons
    if i%2 == 1:
        first = experiments[i]
        second = experiments[i-1]
        # check to see if the average max fitness has same generations for both first and second experiments. If the average max fitness has uneven generations, then all averages and deviations will have uneven generations
        first_length = len(first.average_max_fitness)
        second_length = len(second.average_max_fitness)
        # get all of our average arrays and deviation arrays locally so we can correct them without accessing the object and overriding values. All arrays have matching average and deviation at the same index
        first_averages = first.get_average_arrays()
        first_deviations = first.get_deviation_arrays()
        first_aggregates = first.get_aggregates()
        second_averages = second.get_average_arrays()
        second_deviations = second.get_deviation_arrays()
        second_aggregates = second.get_aggregates()

        if first_length > second_length:
            for i in range(0, len(first_averages)):
                # correct the length difference for each array using the longer length experiment
                second_averages[i] = second.correct_outlier(second_averages[i], first_length)
                second_deviations[i] = second.correct_outlier(second_deviations[i], first_length)
                second.find_outliers(second_aggregates, first_length)
                # print(len(averages[i])) 
        elif second_length > first_length:
            for i in range(0, len(first_averages)):
                first_averages = first.correct_outlier(first_averages[i], second_length)
                first_deviations = first.correct_outlier(first_deviations[i], second_length)
                first.find_outliers(first_aggregates, second_length)

        plot_options = c.get_deviation_plot_options()

        plot_names = ['Max Fitness', 'Minimum Fitness', 'Average Fitness', 'Champion Complexity', 'Max Complexity', 'Minimum Complexity', 'Average Complexity']
        for i in range(len(plot_options)): 
        # plot the comparison standard deviation between the current experiment and previous
            if plot_options[i]:
                plot.plot_deviation_comparison(first_averages[i], first_deviations[i], first.name, second_averages[i], second_deviations[i], second.name, first_aggregates[i], second_aggregates[i], c.plot_significance, plot_names[i])
            else:
                continue
