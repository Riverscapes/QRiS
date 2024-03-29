# Name:     Plotting
#
# Purpose:  Support methods for generating various MatPlotLib charts.
#           The main use is for validation.
#
# Author:   Philip Bailey
#
# Date:     15 Aug 2019
# -------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from scipy import stats
import os


def validation_chart(values, chart_title):

    if len(values) < 1:
        raise Exception('No data values to chart.')

    file_path = os.path.join('docs/assets/images/validation', chart_title.replace(' ', '_').lower() + '.png')
    xyscatter(values, 'BRAT 3', 'BRAT 4', chart_title, file_path, True)


def xyscatter(values, xlabel, ylabel, chart_title, file_path, one2one=False):
    """
    Generate an XY scatter plot
    :param values: List of tuples containing the pairs of X and Y values
    :param xlabel: X Axis label
    :param ylabel: Y Axis label
    :param chart_title: Chart title (code appends sample size)
    :param file_path: RELATIVE file path where the figure will be saved
    :return: none
    """

    x = [x for x, y in values]
    y = [y for x, y in values]

    plt.clf()
    plt.scatter(x, y, c='#DA8044', alpha=0.5, label='{} (n = {:,})'.format(chart_title, len(x)))
    plt.title = chart_title
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    # TODO: add timestamp text element to the chart (to help when reviewing validation charts)

    if one2one:
        if len(x) < 3:
            raise Exception('Attempting linear regression with less than three data points.')

        m, c, r_value, _p_value, _std_err = stats.linregress(x, y)

        min_value = min(x)  # min(min(x), min(y))
        max_value = max(x)  # max(max(x), max(y))
        plt.plot([min_value, max_value], [m * min_value + c, m * max_value + c], 'blue', lw=1, label='regression m: {:.2f}, r2: {:.2f}'.format(m, r_value))
        plt.plot([min_value, max_value], [min_value, max_value], 'red', lw=1, label='1:1')

    plt.legend(loc='upper left')
    plt.tight_layout()

    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    plt.savefig(file_path)


def box_plot(values, ylabel, chart_title, file_path):

    _fig1, ax1 = plt.subplots()
    ax1.set_title(chart_title)
    ax1.boxplot(values)

    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    plt.savefig(file_path)


def pie_chart(values, labels, file_path, title=None):
    fig1, ax1 = plt.subplots()

    ax1.pie(values, autopct='%1.1f%%')

    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if title is not None:
        ax1.set_title(title)
    ax1.legend(title='Legend', labels=labels, bbox_to_anchor=(1.0, 1.0))

    plt.savefig(file_path, bbox_inches='tight')


def histogram(values, bins, file_path):

    plt.clf()
    plt.hist(values, bins)

    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    plt.savefig(file_path)


def line(x_values, y_values, xlabel, ylabel, chart_title, file_path):

    plt.clf()
    plt.plot(x_values, y_values)

    plt.title = chart_title
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    plt.savefig(file_path)


def bar_chart(y_values, x_values, file_path, x_label, y_label, title=None):
    fig1, ax1 = plt.subplots()
    color_map = plt.get_cmap("tab10").colors
    x = []
    for i in range(0, len(x_values)):
        x.append(i + 1)
    ax1.bar(x, y_values, color=color_map)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)
    y_values_patch = [str(y_values) + str(i) for i in range(0, len(y_values))]
    cmap = dict(zip(y_values_patch, color_map))

    patches = [Patch(color=v, label=k) for k, v in cmap.items()]

    ax1.legend(title='Legend', labels=x_values, handles=patches, bbox_to_anchor=(1.0, 1.0))
    ax1.set_xticks([])
    if title is not None:
        ax1.set_title(title)
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    plt.savefig(file_path, bbox_inches='tight')
