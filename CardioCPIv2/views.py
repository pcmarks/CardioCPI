__author__ = 'pcmarks'

from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from numpy import array, reshape, zeros, shape, transpose, sort

from pandas import DataFrame, Series

from scipy.stats import ttest_ind

import json
import requests
import plots

import geo_data

GEO_SERVER = settings.GEO_SERVER        # E,G, 'http://mri-deux.mmc.org:8082'

def home(request):

    """

    :param request:
    :return:
    """
    return render(request, 'index.html')


def platform_selection(request):
    """

    :rtype : HttpResponse
    :param request:
    :return:
    """
    study, profile = request.GET.get("study_profile").split("|")
    new_platform = request.GET.get('new')
    old_platform = request.GET.get('old')
    # Called for its side effects - caching of a platform's symbols,
    geo_data.switch_platform(study, profile, new_platform, old_platform)
    # path = '/'.join(["/geo", tokens[0], tokens[1], 'platforms'])
    # requests.post(GEO_SERVER + path, files=request.GET.dict())
    return HttpResponse("HUH?")


def gene_selection(request):
    """

    :param request:
    :return:
    """
    profile = request.GET.get('profile')
    symbols = request.GET.get('symbols')
    gene_list = geo_data.match_symbols(profile, symbols)
    # path = '/'.join(['/geo', 'study', profile, 'platform', 'gene_symbols'])
    # payload = {'q': symbols}
    # r = requests.get(GEO_SERVER + path, params=payload)
    # data = r.text
    return HttpResponse(gene_list, content_type='text/json')


def correlation_chart(request):
    """

    :param request:
    :return:
    """
    # csvfile = open("/home/pcmarks/profile_data.csv")
    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    symbols = request.GET.get('symbols').split(',')
    # Get the profile data for these symbols; combined = False
    # profile_data = get_profile_data(study, profile, platform, symbols, False)
    profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
    sample_ids = profile_data['sample_ids']
    an_array = array(profile_data['values'])
    a_matrix = reshape(an_array, (len(sample_ids), len(an_array) / len(sample_ids)))

    fig = plots.correlation_plot(a_matrix, study, platform, sample_ids, symbols)
    canvas = FigureCanvas(fig)

    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response

def combined_correlation_chart(request):
    """

    :param request:
    :return:
    """
    spp_arg = request.GET.get('spp')
    spps = spp_arg.split(',')
    study_list = []
    profile_list = []
    platform_list = []
    for spp in spps:
        study, profile, platform, symbols = spp.split('|')
        study_list.append(study)
        profile_list.append(profile)
        platform_list.append(platform)

    result_matrix, row_labels, col_labels = match_and_merge(spp_arg)

    fig = plots.correlation_plot(result_matrix, study, platform, row_labels, col_labels)
    canvas = FigureCanvas(fig)

    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response


def get_profile_data(study, profile, platform, symbols, combined):
    """

    :param study:
    :param profile:
    :param platform:
    :param symbols:
    :return:
    """
    if combined:
        path = '/'.join(['/geo', study, profile, platform, 'combined-expressions'])
    else:
        path = '/'.join(['/geo', study, profile, platform, 'expressions'])

    payload = {'genes': symbols}
    r = requests.get(GEO_SERVER + path, params=payload)
    data = r.json()
    return data

def heatmap_chart(request):
    """

    :param request:
    :return:
    """
    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    symbols = request.GET.get('symbols').split(',')
    # Get the profile data for these symbols; combined = False
    # profile_data = get_profile_data(study, profile, platform, symbols, False)
    profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
    an_array = array(profile_data['values'])
    sample_count = profile_data['sample_count']
    a_matrix = reshape(an_array, (sample_count, len(an_array) / sample_count))
    col_labels = symbols
    row_labels = profile_data['sample_ids']

    fig = plots.heatmap(a_matrix, study, platform, row_labels, col_labels, False)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response


def combined_heatmap_chart(request):
    """

    :param request:
    :return:
    """
    spp_arg = request.GET.get('spp')
    spps = spp_arg.split(',')
    study_list = []
    profile_list = []
    platform_list = []
    for spp in spps:
        study, profile, platform, symbols = spp.split('|')
        study_list.append(study)
        profile_list.append(profile)
        platform_list.append(platform)

    result_matrix, row_labels, col_labels = match_and_merge(spp_arg)

    fig = plots.heatmap(result_matrix, study_list, platform_list, row_labels, col_labels, True)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response


def match_and_merge(spp_arg):
    spps = spp_arg.split(',')
    profile_data_list = []
    co_samples_list = []
    symbols_list = []
    for spp in spps:
        study, profile, platform, symbols = spp.split('|')
        symbols = symbols.split(' ')
        # Get the profile data for these symbols; combined = True
        # profile_data = get_profile_data(study, profile, platform, ','.join(symbols), True)
        profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
        symbols_list.append(symbols)
        co_samples_list.append([json.loads(co_sample) for co_sample in profile_data['sample_attributes']])
        profile_data_list.append(profile_data)

    an_array0 = array(profile_data_list[0]['values'])
    sample_count0 = profile_data_list[0]['sample_count']
    a_matrix0 = reshape(an_array0, (sample_count0, len(an_array0) / sample_count0))
    col_labels0 = symbols_list[0]
    no_of_symbols0 =len(col_labels0)

    an_array1 = array(profile_data_list[1]['values'])
    sample_count1 = profile_data_list[1]['sample_count']
    a_matrix1 = reshape(an_array1, (sample_count1, len(an_array1) / sample_count1))
    col_labels1 = symbols_list[1]

    result_matrix = zeros((sample_count0, len(col_labels0) + len(col_labels1)))
    row_labels = []
    for index1, attribute in enumerate(co_samples_list[0]):
        control = attribute['control']
        co_sample_id = attribute['co_sample']
        if control:
            row_labels.append('C-' + co_sample_id)
        else:
            row_labels.append('D-' + co_sample_id)
        sample_index = profile_data_list[1]['sample_ids'].index(co_sample_id)
        result_matrix[index1,0:no_of_symbols0] = a_matrix0[index1]
        result_matrix[index1,no_of_symbols0:] = a_matrix1[sample_index]

    col_labels0.extend(col_labels1)

    return result_matrix, row_labels, col_labels0

def t_tests(request):
    # 1. Get all sample ids for given study, profile and platform
    # 2. Get all gene symbols for given study, profile and platform
    # 3. For each sample and for each gene symbol get expression value

    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    # path = '/'.join(['/geo', study, profile, platform, 'sample_ids'])
    # r = requests.get(GEO_SERVER + path)
    # sample_ids = r.json()
    sample_ids = geo_data.get_sample_ids(study, profile, platform)
    no_of_samples = len(sample_ids)
    control_sample_ids = []
    diseased_sample_ids = []
    for sample_id in sample_ids:
        sample_attributes = geo_data.get_sample_attributes(study, profile, platform, sample_id)
        if sample_attributes['control']:
            control_sample_ids.append(sample_id)
        else:
            diseased_sample_ids.append(sample_id)

    genes = geo_data.get_all_gene_symbols(study, profile, platform)
    # path = '/'.join(['/geo', study, profile, platform, 'gene_symbols'])
    # r = requests.get(GEO_SERVER + path)
    # genes = r.json()
    no_of_genes = len(genes)
    control_exprs = zeros((no_of_genes, len(control_sample_ids)))
    diseased_exprs = zeros((no_of_genes, len(diseased_sample_ids)))
    for (g_index, gene) in enumerate(genes):
        gene_exprs = zeros(len(control_sample_ids))
        for (s_index, sample_id) in enumerate(control_sample_ids):
            # path = '/'.join(['/geo', study, profile, platform, sample_id, gene])
            # r = requests.get(GEO_SERVER + path)
            # expr_value = r.text
            expr_value = geo_data.get_gene_expression_value(study, profile, platform, sample_id, gene)
            if expr_value == 'None':
                continue
            gene_exprs[s_index] = expr_value
        control_exprs[g_index] = gene_exprs

        gene_exprs = zeros(len(diseased_sample_ids))
        for (s_index, sample_id) in enumerate(diseased_sample_ids):
            # path = '/'.join(['/geo', study, profile, platform, sample_id, gene])
            # r = requests.get(GEO_SERVER + path)
            # expr_value = r.text
            expr_value = geo_data.get_gene_expression_value(study, profile, platform, sample_id, gene)
            if expr_value == 'None':
                continue
            gene_exprs[s_index] = expr_value
        diseased_exprs[g_index] = gene_exprs

    control_df = DataFrame(control_exprs, index=genes, columns=control_sample_ids)
    diseased_df = DataFrame(diseased_exprs, index=genes, columns=diseased_sample_ids)

    t_statistics, p_values = ttest_ind(control_df.T, diseased_df.T)

    p_values_series = Series(p_values, index=genes)

    from mne.stats import bonferroni_correction, fdr_correction
    reject_bonferroni, pval_bonferroni = bonferroni_correction(p_values_series, alpha=0.05)
    reject_fdr, pval_fdr = fdr_correction(p_values_series,alpha=0.05, method='indep')

    bonferroni_p_values = p_values_series[reject_bonferroni]
    fdr_p_values = p_values_series[reject_fdr]

    no_of_values = 40
    p_values_series.sort(ascending=True)
    print p_values_series[:25]

    fig = plots.t_test_histogram(p_values_series, no_of_values)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response
