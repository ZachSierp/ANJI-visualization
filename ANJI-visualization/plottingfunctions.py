import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy import stats
import experiment
import config
import random as random
import pylab
import os
import re
import warnings
import numpy as np

# we need to define these variables first so we can have access to them in the functions below
show_plots = False
save_plots = False
show_legend =  True
save_path = ''
epoch_modifier = 1
formats = None
line_format = ''
point_size = '3'
cap_size = 4
transparency = 0.5
groups = None
list_of_colors = ['r', 'b', 'g', 'c', 'y', 'm', 'k']
line_type = None
simple_legend = False
group_agg = False
custom_colors = False
colors = {
	"red" : (255,0,0),
	"green" : (0,255,0),
	"blue" : (0,0,255),
	"black" : (0,0,0),
	"white" : (255,255,255),
	"cyan" : (0,255,255),
	"yellow" : (255,255,0),
	"magenta" : (255,0,255),
	"orange" : (155,165,0),
	"brown" : (165,42,42)
}
num_colors = 0
custom_name = None
offset = 0
shaded_region = False
show_bar_graphs = False
# default color is gray
bar_ecolor = (0.82, 0.82, 0.82, 1.0)
agg_ls = 'solid'

# generate the seed for random
random.seed()
# create a list to store currently used colors to ensure we don't plot the same color twice.
# we will need to clear the list at the end of every function in which it is used, or we will fill the list with all possible color values and have an error
colors_in_use = []

# take the config file from xparse.py and load up the global variables with the config values
def load(conf):
	# setup all of the important plotting information using the variables passed by the xparse file
    global show_plots, show_legend, save_path, save_plots, epoch_modifier, formats, line_format, point_size, offset, agg_ls
    global cap_size, transparency, groups, simple_legend, group_agg, custom_colors, list_of_colors, num_colors, custom_name, shaded_region, show_bar_graphs, bar_ecolor

    offset = conf.offset
    shaded_region = conf.shaded_region
    show_bar_graphs = conf.bar_graphs
    agg_ls = conf.agg_ls

    try:
        c = conf.bar_ecolor.strip('()')
        c = c.split(',')
        for i in range(len(c)):
            val = c[i].strip()
            c[i] = int(val)

        col = tuple(c)
        bar_ecolor = normalize(col)
    except:
        pass

    if conf.custom_name is not None:
        custom_name = conf.custom_name
    if conf.colors is not None:
        custom_colors = True
        list_of_colors = conf.colors
    groups = conf.properties_groups
    if groups is not None:
        num_colors = len(groups)
        assign_param_colors()
        group_agg = conf.plot_groups

    show_plots = conf.show_plots
    if not show_plots:
        matplotlib.use('Agg')
    else:
        try:
            plt.figure()
            plt.close('all')
        except:
            quit(1)

    show_legend = conf.use_legend
    simple_legend = conf.simple_legend
    save_plots = conf.save_plots
    save_path = conf.save_path
    epoch_modifier = conf.epoch_modifier
    # array of formatting information
    #[bool, int, int, int, int]
    # [continuous_lines, point_size, cap_size]
    formats = conf.get_plot_format()

    # ensure that save_path ends with a '/'
    if not save_path.endswith('/'):
        save_path += '/'

    # start building our actual format string based on input_format
    if formats[0]:
        line_format += '-'
    # this is the default point format regardless of continuous lines
    line_format += 'o'

    # ensure we have a non default value for other inputs
    if len(formats) > 1:
        if int(formats[1]) > 0:
            point_size = formats[1]
        if formats[2] > 0:
            cap_size = formats[2]
    transparency = formats[3]

# function to check for and create directory for experiments
def get_experiment_dir(name):
    filename = re.sub(" ", "_", name)
    path = save_path + filename + "/"
    return path

# Map colors (0-255) to range 0-1 for matplotlib
def normalize(c):
    r = int(c[0])/255
    g = int(c[1])/255
    b = int(c[2])/255
    return (r,g,b)

# creates a new random color
def create_color():
    r = random.random()
    g = random.random()
    b = random.random()
    c = (r,g,b)
    return c

# the offset adds to the index of the get_custom_color function in the case of duplicates. For every duplicate, we increase the offset once. This allows us to handle jumping ahead in the list index without modifying the groups index input.
color_offset = 0
# returns the custom color from the list of colors with given index
def get_custom_color(idx):
    global color_offset
    try:
        color = list_of_colors[idx + color_offset]
    except:
        print("EXHAUSTED PROVIDED LIST OF COLORS. GENERATING NEW COLOR.")
        color = create_color()
    if isinstance(color, tuple):
        if len(color) == 3:
            # if we are receiving a repeat color from the custom colors list, we create a random color to take its place.
            if color in colors_in_use:
                color_offset += 1
                print("WARNING: DUPLICATE COLORS USED. ACCESSING NEXT COLOR.")
                color = get_custom_color(idx)
            colors_in_use.append(color)
            return color
        else:
            color_offset += 1
            print("INVALID (R,G,B) VALUE. ACCESSING NEXT COLOR.")
            return get_custom_color(idx)
    else:
        try:
            color = colors.get(color)
            assert(color is not None)
            if color in colors_in_use:
                color_offset += 1
                print("WARNING: DUPLICATE COLORS USED. GENERATING NEW COLOR.")
                color = get_custom_color(idx)
            colors_in_use.append(color)
            return color
        except:
            print("INVALID COLOR %s HAS BEEN ENTERED. ACCESSING NEXT COLOR" % list_of_colors[idx + color_offset])
            color_offset += 1
            return get_custom_color(idx)


# function returns normalized (r, g, b) tuple for color plotting
def get_color():
    # create new color
    new_color = create_color()
    if new_color in colors_in_use:
        new_color = get_color()
    # return the color
    return new_color

def clear_colors():
    del colors_in_use[:]

# Takes 2D arrays -> 1D array
# Arrays should be in the format X_by_job, such that the outer array is a list of jobs, and the inner array of each job
# contains the data in ascending order.
# The funciton then sorts through both arrays and gathers the data by generation rather than job, and uses that to get
# significance values
def get_significance(first_ary, second_ary):
    if len(first_ary) != len(second_ary):
        print('significance arrays not equal!')
    # we are passed two 2D arrays containing all fitness values for each experiment
    p_values = []
    # loop through all the generations
    for i in range(len(first_ary[0])):
        # create arrrays to store the value for each job at a specific generations
        first_vals = []
        second_vals = []
        # loop through the jobs to extract values at each generation
        for j in range(len(first_ary)):
            first_vals.append(first_ary[j][i])
            second_vals.append(second_ary[j][i])
        warnings.filterwarnings('error')
        try:
            # calculate significance at each generation
            t, p = stats.ttest_ind(first_vals, second_vals, equal_var=False)
            p_values.append(1-p)
        except:
            p_values.append(0)

    return p_values


# data array passed from experiment object i.e. (experiment.average_fitness) -> plot
# label input variable is the label of the line on the graph, and the name variable is the title of the graph
def plot_single_experiment_data(ary, label, name):
    plt.figure()
    maindir = get_experiment_dir(name)
    save_location = '%ssingle_plots/' % maindir
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    filename = '%s_%s' % (name, label)
    # create x values for plotting
    xlist = []
    xlist.append(1)
    # add x values by epoch
    for i in range(1, len(ary)):
        xlist.append(i * epoch_modifier)

    # check to see if there is a custom name. If there is, we need to reassign name to use it for the title.
    if custome_name is not None:
        name = custom_name

    # plot values
    plt.title(name)
    plt.plot(xlist, ary, 'o')
    plt.plot(xlist, ary, label=label)
    if show_legend:
        plt.legend()
    # if show_plots is true, than show the plot after creation
    # if show_plots:
        # plt.show()
    # if save_plots is true, save the plot
    if save_plots:
        plt.savefig(save_location + filename)
        print('New file "%s" saved to "%s"' % (filename, save_location))
    if show_plots:
        plt.show()
    plt.close('all')

# assign colors to a subset of paramaters
def assign_param_colors():
    global line_type
    line_type = ['solid', 'dashed', 'dotted', 'dashdot']
    if list_of_colors is not None:
        for i in range(len(groups)):
            groups[i] = (groups[i], normalize(get_custom_color(i)))
    else:
        for i in range(len(groups)):
            groups[i] = (groups[i], normalize(get_color()))

def get_param_color(summary):
    if not isinstance(summary, list):
        info = summary.split(',')
    else:
        info = summary
    if groups is not None:
        for param in groups:
            for setting in info:
                if setting == param[0]:
                    return param[1]
    else:
        color = get_color()
        return normalize(color)

def get_param(summary):
    value = summary
    if not isinstance(summary, list):
        info = summary.split(',')
    else:
        info = summary
    if groups is not None:
        for param in groups:
            for setting in info:
                if setting == param[0]:
                    value = param[0]
    return value

def plot_bar_graph(title, save_loc, filename, vals, labels, colors, devs, data_type):
        fig, ax = plt.subplots()
        bar_vals = np.asarray(vals)
        bar_deviation = np.asarray(devs)
        N = np.arange(len(bar_vals))
        rects = ax.bar(N, bar_vals, 0.5, color=colors)
        # loop through graph and draw error bars. This will allow us to ensure that we dont put a black ebar on a black bar
        # we need to keep track of which rect we are looking at
        rect_num = 0
        for x, y, err in zip(N, bar_vals, bar_deviation):
            p_col = bar_ecolor

            ax.errorbar(x, y, err, lw=2, capsize=5, capthick=2, color=p_col)
            rect_num += 1

        rect_num = 0

        ax.set_ylabel(data_type)
        ax.set_title(title)
        ax.set_xticks(N)
        ax.set_xticklabels(labels)
        # rotate every label on the graph
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

        for i in range(len(rects)):
            rect = rects[i]
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., height + bar_deviation[i],
                '%c%d' % (unichr(177),  bar_deviation[i]), ha='center', va='bottom')
            ax.text(rect.get_x(), height, '%d' % height, ha='center', va='bottom')

        # fig.set_size_inches(8, 8)
        plt.tight_layout()

        if save_plots:
            if not os.path.exists(save_loc):
                os.makedirs(save_loc)
            plt.savefig(save_loc + filename)
            print("New file %s saved to %s" % (filename, save_loc))
        if show_plots:
            plt.show()


        plt.close('all')


# TO-DO: change plot_groups so that it plots standard deviation bars
# plot the aggregate group vals
def plot_groups(ary, xvals, data_type, name):
    global offset, shaded_region, show_bar_graphs
    plt.figure()
    maindir = get_experiment_dir(name)
    # check to see if there is a custom name. If so, reassigne name to use it.
    if custom_name is not None:
        name = custom_name
    title = name + ' ' + data_type
    save_location = "%ssubgroup_plots/" % maindir
    filename = data_type + '_deviation'
    # ary is passed as tuple of (data, summary)
    counter = 0
    if show_bar_graphs:
        bar_title = name + ' ' + data_type
        bar_save_location = "%sbar_plots/" % maindir
        bar_filename = data_type + '_bar_deviation'
        bar_vals = []
        bar_labels = []
        bar_colors = []
        bar_deviation = []

    # numpy array allows us to offset each value with a simple math function
    xvals = np.asarray(xvals)
    for data, summary in ary:
        label = get_param(summary[0])
        plot_color = get_param_color(summary[0])
        array = np.asarray(data)
        average = np.mean(array, axis=0)
        deviation = np.std(array, axis=0)
        # plt.plot(xvals + (counter * offset), average, color=plot_color, label=label)
        if not shaded_region:
            plt.errorbar(xvals + (counter * offset), average, yerr=deviation, fmt=line_format, color=plot_color, markersize=point_size, capsize=cap_size, label=label)
        else:
            plt.plot(xvals + (counter * offset), average, color=plot_color, label=label)
            plt.fill_between(xvals + (counter * offset), average-deviation, average+deviation, color=plot_color, alpha = 0.1)
        counter += 1

        if show_bar_graphs:
            bar_avg = average[len(average)-1]
            bar_dev = deviation[len(deviation)-1]
            bar_vals.append(bar_avg)
            bar_labels.append(label)
            bar_colors.append(plot_color)
            bar_deviation.append(bar_dev)


    if show_legend:
        plt.legend(loc='best')
    plt.suptitle(name)
    plt.title(data_type)
    if save_plots:
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        plt.savefig(save_location + filename)
        print("New file %s saved to %s" % (filename, save_location))
    if show_plots:
        plt.show()
    # close all plots so we don't plot to the wrong figure
    plt.close('all')

    if show_bar_graphs:
        plot_bar_graph(bar_title, bar_save_location, bar_filename, bar_vals, bar_labels, bar_colors, bar_deviation, data_type)


# input array should be 2D array, of type x_by_job. Function plots each job on a graph to display aggregate data
# data_type variable is the subtitle, name is the title of the graph. All lines listed will be of name type "job_x"
def plot_single_experiment_aggregate_data(ary, data_type, name, job_summaries):
    figure = plt.figure()
    global line_type
    data_type = re.sub(" ", "_",data_type)
    maindir = get_experiment_dir(name)
    save_location = '%saggregate_plots/' % maindir
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    filename = '%s_%s_aggregate' % (name, data_type)
    # create x values for plotting
    xlist = []
    xlist.append(1)
    if len(ary) >= 1:
        # add x values by epoch
        for i in range(1, len(ary[0])):
            xlist.append(i * epoch_modifier)

    if len(job_summaries) == 0:
        for i in range(0, len(ary)):
            job_summaries.append('')
    # keep track of the starting job value for the legend
    start_job = 1
    # plot values
    ax = plt.axes()
    # create an array to store the group information. Array is 2D, consisting of tuples of type (array_of_vals, array_of_summaries)
    group_array = []
    for i in range(len(ary)):
        # set local variable for current data_set for ease
        data_set = ary[i]
        # get a new color for the plot
        plot_color = get_param_color(job_summaries[i])
        # try:
            # style = line_type[i%4]
        # except:
        style = agg_ls
        if simple_legend:
            # make sure we can access the next plot color to avoid errors
            try:
                # if the next data_set has the same color, we dont want to put down the label yet
                if get_param_color(job_summaries[i+1]) == plot_color:
                    ax.plot(xlist, data_set, color=plot_color, ls=style)
                else:
                    plot_label = "Jobs %i - %i: %s" % (start_job, (i+1), get_param(job_summaries[i]))
                    ax.plot(xlist, data_set, color=plot_color, label=plot_label, ls=style)
                    if group_agg:
                        group_array.append((ary[start_job:i], job_summaries[start_job:i]))
                    start_job = i+2

            # if the next job summarie is none, we are at the end of the data_sets and need to provide the final label
            except:
                plot_label = "jobs %i - %i: %s" % (start_job, (i+1), get_param(job_summaries[i]))
                ax.plot(xlist, data_set, color=plot_color, label=plot_label, ls=style)
                if group_agg:
                    new_group = (ary[start_job:i], job_summaries[start_job:i])
                    group_array.append(new_group)

        # if we are not using simplified legends, we plot normally
        else:
            plot_label = "Job %i: %s" % ((i+1), job_summaries[i])
            ax.plot(xlist, data_set, color=plot_color, label=plot_label, ls=style)
    # check to see if we can use the custom name. Cannot reassign like above because we need the original name for group plotting.
    if custom_name is not None:
        figure.suptitle(custom_name)
    else:
        figure.suptitle(name)
    plt.title(data_type)
    if show_legend:
        plt.legend(loc='best')

    # test idea for separate legend window
    # legend = pylab.figure(figsize = (5, 5))
    # pylab.legend(*ax.get_legend_handles_labels(), loc = 'upper left')
    # legend.tight_layout()

    # show and save plot
    if save_plots:
        plt.savefig(save_location + filename)
        print('New file "%s" saved to "%s"' % (filename, save_location))
    if show_plots:
        plt.show()
    # clear the list of used colors for the next plot
    clear_colors()
    plt.close('all')
    # check to see if we need to plot groups
    if group_agg and group_array is not None:
        plot_groups(group_array, xlist, data_type, name)


# takes array of averages, array of standard deviation values
# label is the label of the line, name variable is the title of the graph
def plot_std_deviation(data_ary, dev_ary, label, name):
    plt.figure()
    maindir = get_experiment_dir(name)
    save_location = '%sstandard_deviation_single/' % maindir
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    filename = '%s_%s_deviation' % (name, label)
    filename = re.sub(" ", "_", filename)
    # create x values for plotting
    xlist = []
    xlist.append(1)
    # add x values by epoch
    for i in range(1, len(data_ary)):
        xlist.append(i * epoch_modifier)

    plt.errorbar(xlist, data_ary, yerr=dev_ary, fmt=line_format, markersize=point_size, capsize=cap_size, label=label)
    # check to see if there is a custom name
    if custom_name is not None:
        name = custom_name
    plt.title(name)
    if show_legend:
        plt.legend(loc='best')

    if save_plots:
        plt.savefig(save_location + filename)
        print('New file "%s" saved to "%s"' % (filename, save_location))
    if show_plots:
        plt.show()

def plot_all_mean_comparison(list_of_means, labels, data_type, name):
    plt.figure()
    maindir = get_experiment_dir(name)
    save_location = '%smean_comparison/' % maindir
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    filename = '%s_%s_comparison' % (name, data_type)
    xlist = []
    xlist.append(1)
    for i in range(1, len(list_of_means[0])):
        xlist.append(i * epoch_modifier)

    for i in range(0, len(list_of_means)):
        plt.plot(xlist, list_of_means[i], label=labels[i])

    # check for a custom name
    if custom_name is not None:
        name = custom_name
    plt.title(name)
    if show_legend:
     plt.legend(loc='best')

    if save_plots:
        plt.savefig(save_location + filename)
        print('New file "%s" save to "%s"' % (filename, save_location) )
    if show_plots:
        plt.show()

    plt.close('all')

# first_data is an array of the averages of the first experiment, first_dev is an array of the deviation values for that experimen
# first_aggregate is the "x_by_jobs" data array of the first experiment, a 2D array of all values of given type. This is
# necessary for calculating significance.
# first_label is the label of the first experiment line; holds true for all variables of "second_x" type
# show_significance variable determines whether or not we calculate the significance and plot the significance
# if show_significance is false, the funciton will only plot a comparison of the two standard deviations
def plot_deviation_comparison(first_data, first_dev, first_label,
                              second_data, second_dev, second_label, first_aggregate, second_aggregate, show_significance, title):
    if len(first_data) != len(second_data):
        print('Invalid data length for %s vs %s' % (first_label, second_label))
        print(len(first_data))
        print(len(second_data))
        quit(1)
    else:
        global offset
        title = '%s Comparison' % title
        # check if there is a custom name and if there is prepend it to the tile
        if custom_name is not None:
            title = '%s %s' % (custom_name, title)
        save_location = '%sdeviation_comparisons/' % save_path
        # make sure save location exists
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        save_name = title.lower()
        save_name = re.sub(" ", "_", save_name)
        filename = '%s_vs_%s_%s' % (first_label, second_label, save_name)
        # create x values for plotting
        xlist = []
        xlist.append(1)
        # add x values by epoch
        for i in range(1, len(first_data)):
            xlist.append(i * epoch_modifier)
        # convert xlist to np array so we can offse tit
        xlist = np.asarray(xlist)
	# if we are going to show the significance of the two plots, we need a second subplot to display the significance line
        if show_significance:
	    # create our subplots for plotting
            fig, ax = plt.subplots()
            if not shaded_region:
	        # plot the two standard deviation graphs passed to us on the original subplot
                ax.errorbar(xlist, first_data, yerr=first_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=first_label)
                ax.errorbar(xlist + offset, second_data, yerr=second_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=second_label)
            else:
                ax.plot(xlist, first_data, label=first_label)
                ax.plot(xlist + offset, second_data, label=second_label)
                ax.fill_between(xlist, first_data - first_dev, first_data + first_dev, alpha=0.1)
                ax.fill_between(xlist, second_data - second_dev, second_data + second_dev, alpha=0.1)
	    # get the p_values for the given data
            p_values = get_significance(first_aggregate, second_aggregate)

	    #ensure that we have a single p_value for every generation
            if len(xlist) == len(p_values):
                # create inset axes
                a = plt.axes([.125, .11, .775, .20], facecolor = 'w', sharex=ax)
                # plot p values
                a.plot(xlist, p_values, color='#000000', alpha=transparency)
                # plot threshold
                a.plot([1, xlist[(len(xlist)-1)]], [0.95, 0.95], 'r--', alpha=transparency)
                plt.title("Significance")
                a.spines['top'].set_visible(False)
                a.yaxis.tick_right()
                a.patch.set_alpha(0)

            fig.suptitle(title)
            if show_legend:
                legend0 = ax.legend(loc='best')

            if save_plots:
                plt.savefig(save_location + filename)
                print('New file "%s" saved to "%s"' % (filename, save_location))
            if show_plots:
                plt.show()

	# if we don't need to show significance we just plot the two lines on the same graph
        else:
            if not shaded_region:
                # plot the two standard deviation graphs passed to us on the original subplot
                plt.errorbar(xlist, first_data, yerr=first_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=first_label)
                plt.errorbar(xlist + offset, second_data, yerr=second_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=second_label)
            else:
                plt.plot(xlist, first_data, label=first_label)
                plt.plot(xlist + offset, second_data, label=second_label)
                plt.fill_between(xlist, first_data - first_dev, first_data + first_dev, alpha=0.1)
                plt.fill_between(xlist, second_data - second_dev, second_data + second_dev, alpha=0.1)

            # plt.errorbar(xlist, first_data, yerr=first_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=first_label)
            # plt.errorbar(xlist, second_data, yerr=second_dev, fmt=line_format, markersize=point_size, capsize=cap_size, label=second_label)

            if show_legend:
                legend = plt.legend(loc='best')
            plt.title(title)

            if save_plots:
                plt.savefig(save_location + filename)
                print('New file "%s" saved to "%s"' % (filename, save_location))
            if show_plots:
                plt.show()

        plt.close('all')

# take a list of averages, deviations, and labels, and plot a comparison of each as a standard deviation
def plot_mean_deviation_comparison(averages, deviations, labels, name, title):
    maindir = get_experiment_dir(name)
    save_location = '%smean_comparison/' % maindir
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    filename= '%s_speices_comparison' % name
    if custom_name is not None:
        name = custom_name
    title = '%s_%s' % (name, title)
    xlist = []
    xlist.append(1)
    for i in range(1, len(averages[0])):
        xlist.append(i*epoch_modifier)

    fig, ax = plt.subplots()
    for i in range(len(averages)):
        ax.errorbar(xlist, averages[i], yerr=deviations[i], fmt=line_format, markersize=point_size, capsize=cap_size, label=labels[i])

    fig.suptitle(title)
    if show_legend:
        legend = ax.legend(loc='best')
    if save_plots:
        plt.savefig(save_location + filename)
        print('New file "%s" saved to "%s"' % (filename, save_location))
    if show_plots:
        plt.show()

    plt.close('all')
