__author__ = 'pcmarks'

from django.http import HttpResponse
from django.shortcuts import render
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import array, reshape


import requests
import plots


GEO_SERVER = 'http://mri-deux.mmc.org:8082'

def home(request):

    return render(request, 'index.html')


def platform_selection(request):
    """

    :rtype : HttpResponse
    :param request:
    :return:
    """
    tokens = request.GET.get("study_profile").split("|")
    path = '/'.join(["/geo", tokens[0], tokens[1], 'platforms'])
    requests.post(GEO_SERVER + path, files=request.GET.dict())
    return HttpResponse("HUH?")


def gene_selection(request):
    profile = request.GET.get('profile')
    symbols = request.GET.get('symbols')
    path = '/'.join(['/geo', 'study', profile, 'platform', 'gene_symbols'])
    payload = {'q': symbols}
    r = requests.get(GEO_SERVER + path, params=payload)
    data = r.text
    return HttpResponse(data, content_type='text/json')


def correlation_chart(request):
    """

    :param request:
    :return:
    """
    # csvfile = open("/home/pcmarks/profile_data.csv")
    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    symbols = request.GET.get('symbols')
    # Get the profile data for these symbols
    profile_data = get_profile_data(study, profile, platform, symbols)
    symbols = symbols.split(',')
    sample_ids = profile_data['sample_ids']
    an_array = array(profile_data['values'])
    fig = plots.correlation_plot(an_array, study, platform, sample_ids, symbols)
    canvas = FigureCanvas(fig)

    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response


def get_profile_data(study, profile, platform, symbols):
    path = '/'.join(['/geo', study, profile, platform, 'expressions'])
    payload = {'genes': symbols}
    r = requests.get(GEO_SERVER + path, params=payload)
    data = r.json()
    return data

def heatmap_chart(request):
    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    symbols = request.GET.get('symbols')
    # Get the profile data for these symbols
    profile_data = get_profile_data(study, profile, platform, symbols)
    an_array = array(profile_data['values'])
    sample_count = profile_data['sample_count']
    a_matrix = reshape(an_array, (sample_count, len(an_array) / sample_count))
    col_labels = symbols.split(',')
    row_labels = profile_data['sample_ids']

    fig = plots.heatmap(a_matrix, study, platform, row_labels, col_labels)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response

