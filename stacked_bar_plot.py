"""
This code generates a stacked bar plot. The plot uses the electricity production dataset for 
demonstration. The appearance of the plot is customized and the final figure is saved.
"""
import os
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns
import pypalettes

from preprocessing import Preprocessor


def get_seeded_shuffle(my_list, seed_value):
    """
    Shuffle a list in a reproducible way using a specified seed value. 
    """
    # Create a copy so we don't mutate the original list
    shuffled_list = my_list.copy()
    # Initialize the random number generator with the specified seed
    random.seed(seed_value)
    # Shuffle the list in-place
    random.shuffle(shuffled_list)
    return shuffled_list


def generate_plot(y, **plot_kwargs):
    """ 
    Generate a stacked bar plot with the provided data and customization options.
    """

    # set new font
    plt.rcParams['font.family'] = ['Arial']
    # set font size
    plt.rcParams.update({'font.size': 20})

    # default bin names if not provided
    if 'bin_names_list' not in plot_kwargs:
        plot_kwargs['bin_names_list'] = [str(i) for i in range(1, len(y[0]) + 1)]

    # default dependent variable names if not provided
    if 'dependent_variable_names' not in plot_kwargs:
        plot_kwargs['dependent_variable_names'] = [str(i) for i in range(1, len(y) + 1)]
    criteria_counts = \
        {key: np.array(value) for key, value in zip(plot_kwargs['dependent_variable_names'], y)}

    # default color palette assignment if not provided
    if 'palette_list' not in plot_kwargs:
        plot_kwargs['palette_list'] = sns.color_palette("Blues", len(y))

    fig, ax = plt.subplots(figsize=(13, 8))

    # set y ranges
    y_max = max([sum(elements) for elements in zip(*y)])
    ax.set(ylim=(0 - 0.05 * y_max, y_max + 0.05 * y_max))

    # plot bars in stack manner
    count = 0
    bottom = np.zeros(len(y[0]))
    for boolean, criteria_counts in criteria_counts.items():
        plt.bar(plot_kwargs['bin_names_list'], criteria_counts, label=boolean, bottom=bottom,
                color=plot_kwargs['palette_list'][count])
        bottom += criteria_counts
        count += 1

    # loop over the bars, and adjust the width (and position, to keep the bar centred)
    new_value = 0.9
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value
        patch.set_width(new_value)
        patch.set_x(patch.get_x() + diff * .5)

    # hide right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    # change spines
    for axis in ['left', 'bottom']:
        ax.spines[axis].set_linewidth(2)
    # increase tick width
    ax.tick_params(width=2)

    # set x and y labels
    ax.set_xlabel('')
    if 'dependent_variable_label' in plot_kwargs:
        ax.set_ylabel(plot_kwargs['dependent_variable_label'])
    ax.tick_params(axis='x', rotation=90)

    # adjust subplots spacing
    # if subplots are added, can include, for e.g., 'wspace=0.4, hspace=0.4'
    # to control padding between subplots
    plt.subplots_adjust(bottom=0.35, top=0.85, left=0.2, right=0.6)

    # add global title
    if 'super_title' in plot_kwargs:
        fig.suptitle(plot_kwargs['super_title'], fontsize="large", color="black")

    # add legend
    colors = dict(zip(plot_kwargs['dependent_variable_names'], plot_kwargs['palette_list']))
    labels = list(colors.keys())
    circle_handles = [Line2D([0], [0], marker='o', color='w',
                           markerfacecolor=colors[label], markersize=16) for label in labels]
    plt.legend(circle_handles, labels, frameon=False, bbox_to_anchor=(1.65, 0.98), ncol=1)


if __name__ == '__main__':

    # --- read data ---
    EXAMPLE_DATA_PATH = r'.\electricity-prod-source-stacked.csv'
    example_data_df = pd.read_csv(EXAMPLE_DATA_PATH)
    # specify and modify dependent variable names (optional)
    example_data_df = \
        Preprocessor.modify_column_names(example_data_df,
                                         ['other renewables', 'bioenergy', 'solar', 'wind',
                                          'hydro', 'nuclear', 'oil', 'gas', 'coal'],
                                         list(range(3, len(example_data_df.columns))))
    example_data = \
        Preprocessor(example_data_df, example_data_df.columns[0], example_data_df.columns[2])
    # preprocessing (location bins example)
    example_data.get_dependent_results('location_bins',
                                        global_variable_list=['Chile', 'Japan', 'Norway',
                                                              'Senegal', 'Thailand',
                                                              'Turkey', 'Uruguay'],
                                        group_variable_range=[2005, 2019])
    # # preprocessing (time bins example)
    # example_data.get_dependent_results('time_bins',
    #                                    bin_num=7,
    #                                    global_value='Canada',
    #                                    group_variable_range=[2005, 2019])
    # specify plotting result to assign dependent variable label (optional)
    # ('dependent_result' or 'percentage_result')
    example_data.select_result('percentage_result')

    # palette setup (optional)
    cmap = pypalettes.load_cmap('rauw')
    # if palette contains enough colors, assign first colors to palette list
    if cmap.N >= len(example_data.prep_results["dependent"]):
        # return colors as a list of hexadecimal values
        pypalettes_list = cmap.colors[:len(example_data.prep_results["dependent"])]
        # adjust palette color order as needed
        pypalettes_list = get_seeded_shuffle(pypalettes_list, 193)
    else:
        raise ValueError("Selected palette size smaller than dependent result.")

    # --- plot data ---
    generate_plot(example_data.prep_results["selected"],
                  bin_names_list=example_data.bin_data["names_list"],
                  dependent_variable_names=example_data.data_df.columns.tolist()[3:],
                  dependent_variable_label=example_data.prep_results["dependent_label"],
                  palette_list=pypalettes_list)

    # save figure
    FILE_DESTINATION = r'.\figure'
    plt.savefig(os.path.join(FILE_DESTINATION + '.pdf').replace("\\", "/"), format="pdf")
    plt.savefig(os.path.join(FILE_DESTINATION + '.png').replace("\\", "/"), dpi=300)
    plt.close()
