"""
Copyright (c) 2014, Peter C Marks and Maine Medical Center Research Institute
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

__author__ = 'pcmarks'

from matplotlib.figure import Figure

# The following is necessary to prevent threading issues (warnings) with QtPixmap
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import pdist
import matplotlib.gridspec as gridspec
from scipy.stats import spearmanr
from matplotlib import colors, cm
from numpy import arange

from django.conf import settings
import os
import re
import tempfile

def new_correlation_plot(figure_number, expr_values, study, platform, sample_ids, symbols):
    """

    :param expr_values:
    :param study:
    :param platform:
    :param sample_ids:
    :param symbols:
    """
    rho, p_value = spearmanr(expr_values)

    fig, ax = plt.subplots()

    ax = fig.add_subplot(111)
    fig.patch.set_facecolor('white')
    correlation = ax.pcolor(rho, cmap=plt.cm.Blues)
    genes = []
    for symbol in symbols:
        match_result = re.match(r"(.+)(_\d+)", symbol)
        if match_result:
            genes.append(match_result.group(1))
        else:
            genes.append(symbol)
    ax.set_yticks(arange(rho.shape[0]) + 0.5, minor=False)
    ax.set_xticks(arange(rho.shape[0]) + 0.5, minor=False)
    ax.set_yticklabels(genes, minor=False, size='small')
    ax.set_xticklabels(genes, minor=False, size='small')
    x_labels = ax.get_xticklabels()
    for label in x_labels:
        label.set_rotation(90)
    plt.colorbar(correlation)
    title = "Study: %s Platform(s): %s" % (study, platform,)
    fig.suptitle(title, y=0.99, fontsize=10)
    fig.set_size_inches(12.0, 10.5)
    canvas = FigureCanvas(fig)
    plot_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    file_name = plot_file.name.split('/')[-1]
    canvas.print_figure(plot_file)

    return settings.MEDIA_URL+file_name


def new_heatmap(figure_number, expr_values, study, platform, sample_ids, symbols, combined):
    """
    Create a heatmap with row and column dendrograms for the array of expression values. The expression
    values are normalized before clustering is performed.
    The Euclidean distance method is used.
    The Complete clustering method is used.

    This code is based on the iPython notebook located here:
        nbviewer.ipython.org/github/ucsd-scientific-python/user-group/blob/master/presentations/20131016/
        hierarchical_clustering_heatmaps_gridspec.ipynb

    :param expr_values: a numpy array of expression values
    :param study:
    :param platform:
    :param sample_ids:
    :param symbols:
    :param combined: Boolean, is this a combined heatmap?
    """
    symbols = np.array(symbols)
    sample_ids = np.array(sample_ids)

    # Normalize the expression values
    expr_values /= np.max(np.abs(expr_values), axis=0)

    # Get the transpose of the expression array to be used in row
    # distance measurements and hierarchical clustering
    expr_values_transposed = np.transpose(expr_values)

    # Calculate the pairwise distances for the rows and columns
    # The default method is 'euclidean'
    column_distances = pdist(expr_values)
    row_distances = pdist(expr_values_transposed)

    # Create a Figure to hold all of the graphical elements
    # Set its background to white
    # Lay out a GridSpec dividing the figure inot 3 rows and 2 columns
    #   Area [1,1] = column dendrogram
    #   Area [2,0] = row dendrogram
    #   Area [2,1] = the heatmap
    #   Area [1,2] = the colorbar legend

    fig = plt.figure()
    # fig = Figure()
    fig.set_tight_layout(True)
    fig.patch.set_facecolor('white')
    heatmap_GS = gridspec.GridSpec(3, 2, wspace=0.0, hspace=0.0, width_ratios=[0.25, 1],
                                   height_ratios=[0.05, 0.25, 1])

    # Perform a cluster analysis on column distances using the complete method.
    # Create and draw a dendrogram
    # Save the reordering values ('leaves') for the columns
    column_cluster = sch.complete(column_distances)
    column_dendrogram_axis = fig.add_subplot(heatmap_GS[1, 1])
    column_dendrogram = sch.dendrogram(column_cluster, orientation='top')
    column_indexes = column_dendrogram['leaves']
    clean_axis(column_dendrogram_axis)

    # Perform a cluster analysis on row distances using the complete method-
    # Create and draw a dendrogram.
    # Save the reordering values ('leaves') for the rows
    row_cluster = sch.complete(row_distances)
    row_dendrogram_axis = fig.add_subplot(heatmap_GS[2, 0])
    row_dendrogram = sch.dendrogram(row_cluster, orientation='right')
    row_indexes = row_dendrogram['leaves']
    clean_axis(row_dendrogram_axis)

    # Reorder the normalized expression value array based on the clustering indexes
    # Create and draw the heatmap. The image itself is used to create the colorbar (below)
    expr_values_transposed = expr_values_transposed[:, column_indexes]
    expr_values_transposed = expr_values_transposed[row_indexes, :]
    heat_map_axis = fig.add_subplot(heatmap_GS[2, 1])
    image = heat_map_axis.matshow(expr_values_transposed, aspect='auto', origin='lower',
                                  #  cmap=RedBlackGreen())
                                  cmap=cm.BrBG)
    clean_axis(heat_map_axis)

    # Prepare the heatmap row labels based on the gene symbols
    gene_symbols = []
    for symbol in symbols:
        match_result = re.match(r"(.+)(_\d+)", symbol)
        if match_result:
            gene_symbols.append(match_result.group(1))
        else:
            gene_symbols.append(symbol)
    genes = np.array(gene_symbols)
    heat_map_axis.set_yticks(np.arange(len(genes)))
    heat_map_axis.yaxis.set_ticks_position('right')
    heat_map_axis.set_yticklabels(genes[row_indexes])

    # Prepare the heatmap column labels based on the sample ids
    # Rotate them 90 degrees
    heat_map_axis.set_xticks(np.arange(sample_ids.shape[0]))
    heat_map_axis.xaxis.set_ticks_position('bottom')
    xlabels = heat_map_axis.set_xticklabels(sample_ids[column_indexes])
    for label in xlabels:
        label.set_rotation(90)

    # Create and draw a scale colorbar. It is based on the values used in the
    # heatmap image.
    scale_cbGSSS = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=heatmap_GS[1, 0],
                                                    wspace=0.0, hspace=0.0)
    scale_cb_axis = fig.add_subplot(scale_cbGSSS[0, 0])
    colorbar = fig.colorbar(image, scale_cb_axis)
    colorbar.ax.yaxis.set_ticks_position('left')
    colorbar.ax.yaxis.set_label_position('left')
    colorbar.outline.set_linewidth(0)
    tick_labels = colorbar.ax.yaxis.get_ticklabels()
    for tick_label in tick_labels:
        tick_label.set_fontsize(tick_label.get_fontsize() - 4)

    # "Tighten" up the whole figure, separating the sub plots by horizontal and vertical spaces
    # Add a title - placed at the very top
    heatmap_GS.tight_layout(fig, h_pad=0.1, w_pad=0.5)

    title = "Study: %s Platform(s): %s" % (study, platform,)
    fig.suptitle(title)

    fig.set_size_inches(12.0, 8.0)

    canvas = FigureCanvas(fig)
    # plot_file_name = 'heatmap%s.png' % figure_number
    # plot_file = os.path.join(settings.MEDIA_ROOT, plot_file_name)
    # canvas.print_figure(plot_file)
    #
    # return '/media/' + plot_file_name
    plot_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    file_name = plot_file.name.split('/')[-1]
    canvas.print_figure(plot_file)

    return settings.MEDIA_URL+file_name

def clean_axis(axis):
    """Remove ticks, tick labels from axis

    :param axis:
    """
    axis.set_xticks([])
    axis.set_yticks([])


def RedBlackGreen():
    """


    :return:
    """
    cdict = {'red': ((0.0, 0.0, 0.0),
                     (0.5, 0.0, 0.1),
                     (1.0, 1.0, 1.0)),

             'blue': ((0.0, 0.0, 0.0),
                      (1.0, 0.0, 0.0)),

             'green': ((0.0, 0.0, 1.0),
                       (0.5, 0.1, 0.0),
                       (1.0, 0.0, 0.0))
    }

    my_cmap = colors.LinearSegmentedColormap('my_colormap', cdict, 256)
    return my_cmap


def t_test_histogram(sorted_p_values, no_of_values):
    """

    :param sorted_p_values:
    :param no_of_values:
    :return:
    """
    figure = plt.figure()
    a_plot = sorted_p_values[:no_of_values].plot(kind='bar')
    figure.add_subplot(a_plot)

    canvas = FigureCanvas(figure)
    return canvas