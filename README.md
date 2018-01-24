# ANJI Visualization

## What is ANJI-visualization?
ANJI-visualization is a plotting tool for ANJI Neural Networks and is built around the specific format of ANJI output directories and XML data files. It was created by Zach Sierp to assist in the performance evaluation of Neural Networks evolved using ANJI.

## Using ANJI-Visualization
The visualization tool can be used directly from the command line. The program requires **at least two** inputs:
1. An ANJI output XML directory containing the data to be plotted
1. A config file of type .ini specifying different settings. (Examples are provided in the "Example_Config" folder as well as a template.)

To run the program *(the order of the config file and directory do not matter)*:
```
$python xparse.py your_config.ini your_directory
```

Two experiment directories can be given to the program for performance comparisons using standard deviation and significance:
```
$python xparse.py your_config.ini directory#1 directory#2
```

Again, the order of the input config file and directories does not matter.

## Example Plot Outputs
![alt text](/Example_Plots/aggregate_plots/jasoyode_2017-04-27_cpg_10_4_arch_act_bias_NO_CHOMOSOMES_Max_Fitness_aggregate.png "Aggregate Max Fitness Plot")

![alt text](/Example_Plots/subgroup_plots/Max_Fitness_deviation.png "Max Fitness Standard Deviation Plot")
