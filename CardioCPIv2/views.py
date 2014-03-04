__author__ = 'pcmarks'

from django.http import HttpResponse
from django.shortcuts import render
from numpy import corrcoef, sum, log, arange, array
from numpy.random import rand
from pylab import pcolor, show, colorbar, xticks, yticks
from scipy.stats import spearmanr
import matplotlib
import matplotlib.pyplot as plt
import csv

from matplotlib import rcParams
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

def home(request):

    return render(request, 'index.html')


def simple(request):
    csvfile = open("/home/pcmarks/profile_data.csv")
    input_file = csv.reader(csvfile)
    row_labels = input_file.next()
    data = []
    for row in input_file:
        data.append(row[1:])
    n_data = array(data)
    rho, pval = spearmanr(n_data)

    rcParams.update({'figure.autolayout': True})
    fig, ax = plt.subplots()
    heatmap = ax.pcolor(rho, cmap=plt.cm.Blues)
    ax.set_yticks(arange(rho.shape[0])+0.5, minor=False)
    ax.set_xticks(arange(rho.shape[0])+0.5, minor=False)
    ax.set_yticklabels(row_labels[1:], minor=False)
    ax.set_xticklabels(row_labels[1:], minor=False)
    plt.colorbar(heatmap)
    canvas = FigureCanvas(fig)

    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response
