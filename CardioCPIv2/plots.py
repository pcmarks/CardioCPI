__author__ = 'pcmarks'

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import pdist
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from matplotlib import rcParams, colors
from numpy import reshape, arange


def correlation_plot(expr_values, study, platform, sample_ids, symbols):
    """
    """
    sample_count = len(sample_ids)
    a_matrix = reshape(expr_values, (sample_count, len(expr_values) / sample_count))

    rho, pval = spearmanr(a_matrix)

    rcParams.update({'figure.autolayout': True})
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('white')
    # heatmap = ax.pcolor(rho, cmap=plt.cm.Blues)
    heatmap = ax.pcolor(rho)
    ax.set_yticks(arange(rho.shape[0])+0.5, minor=False)
    ax.set_xticks(arange(rho.shape[0])+0.5, minor=False)
    ax.set_yticklabels(symbols, minor=False, size='small')
    ax.set_xticklabels(symbols, minor=False, size='small')
    plt.colorbar(heatmap)
    title = "Study: %s Platform: %s" % (study, platform,)
    fig.suptitle(title, y=0.99, fontsize=9)

    return fig


def heatmap(expr_values, study, platform, sample_ids, symbols):
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
    fig.patch.set_facecolor('white')
    heatmap_GS = gridspec.GridSpec(3, 2, wspace=0.0, hspace=0.0, width_ratios=[0.25, 1],
                                    height_ratios=[0.05, 0.25, 1])

    # Perform a cluster analysis on column distances using the complete method.
    # Create and draw a dendrogram
    # Save the reordering values ('leaves') for the columns
    column_cluster = sch.complete(column_distances)
    column_dendrogram_axis = fig.add_subplot(heatmap_GS[1,1])
    column_dendrogram = sch.dendrogram(column_cluster, orientation='top')
    column_indexes = column_dendrogram['leaves']
    clean_axis(column_dendrogram_axis)

    # Perform a cluster analysis on row distances using the complete method-
    # Create and draw a dendrogram.
    # Save the reordering values ('leaves') for the rows
    row_cluster = sch.complete(row_distances)
    row_dendrogram_axis = fig.add_subplot(heatmap_GS[2,0])
    row_dendrogram = sch.dendrogram(row_cluster, orientation='right')
    row_indexes = row_dendrogram['leaves']
    clean_axis(row_dendrogram_axis)

    # Reorder the normalized expression value array based on the clustering indexes
    # Create and draw the heatmap. The image itself is used to create the colorbar (below)
    expr_values_transposed = expr_values_transposed[:, column_indexes]
    expr_values_transposed = expr_values_transposed[row_indexes, :]
    heat_map_axis = fig.add_subplot(heatmap_GS[2,1])
    image = heat_map_axis.matshow(expr_values_transposed, aspect='auto', origin='lower',
                                #  cmap=RedBlackGreen())
                                  cmap=plt.cm.BrBG)
    clean_axis(heat_map_axis)

    # Prepare the heatmap row labels based on the gene symbols
    heat_map_axis.set_yticks(np.arange(symbols.shape[0]))
    heat_map_axis.yaxis.set_ticks_position('right')
    heat_map_axis.set_yticklabels(symbols[row_indexes])

    # Prepare the heatmap column labels based on the sample ids
    # Rotate them 90 degrees
    heat_map_axis.set_xticks(np.arange(sample_ids.shape[0]))
    heat_map_axis.xaxis.set_ticks_position('bottom')
    xlabels = heat_map_axis.set_xticklabels(sample_ids[column_indexes])
    for label in xlabels:
        label.set_rotation(90)

    # Create and draw a scale colorbar. It is based on the values used in the
    # heatmap image.
    scale_cbGSSS = gridspec.GridSpecFromSubplotSpec(1,2,subplot_spec=heatmap_GS[1,0],
                                                    wspace=0.0, hspace=0.0)
    scale_cb_axis =fig.add_subplot(scale_cbGSSS[0,0])
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
    title = "Study: %s Profile: %s" % (study, platform,)
    fig.suptitle(title)

    return fig

def clean_axis(axis):
    """Remove ticks, tick labels from axis"""
    axis.set_xticks([])
    axis.set_yticks([])

def RedBlackGreen():
    cdict = {'red':   ((0.0, 0.0, 0.0),
                       (0.5, 0.0, 0.1),
                       (1.0, 1.0, 1.0)),

             'blue': ((0.0, 0.0, 0.0),
                      (1.0, 0.0, 0.0)),

             'green':  ((0.0, 0.0, 1.0),
                        (0.5, 0.1, 0.0),
                        (1.0, 0.0, 0.0))
    }

    my_cmap = colors.LinearSegmentedColormap('my_colormap',cdict,256)
    return my_cmap