__author__ = 'pcmarks'

import json

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from numpy import array, reshape, zeros
from pandas import DataFrame, Series
from scipy.stats import ttest_ind

import plots
import geo_data


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
    return HttpResponse("HUH?")


def gene_selection(request):
    """

    :param request:
    :return:
    """
    profile = request.GET.get('profile')
    symbols = request.GET.get('symbols')
    gene_list = geo_data.match_symbols(profile, symbols)
    return HttpResponse(gene_list, content_type='text/json')


def all_plots(request):

    """

    :param request:
    :return:
    """
    import json
    spps = json.loads(request.GET.get(u'study_profile_platforms'))
    symbols_selected = json.loads(request.GET.get(u'symbols_selected'))
    combined_plot = json.loads(request.GET.get(u'combined_plot'))
    # print spps, symbols_selected, combined_plot
    figure_file_names = {'correlation': [], 'heatmap': []}
    if not combined_plot:
        for i in range(len(spps)):
            spp = spps[i]
            study, profile, platform = spp.split('|')
            symbols = symbols_selected[i].split(',')
            profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
            sample_ids = profile_data['sample_ids']
            an_array = array(profile_data['values'])
            a_matrix = reshape(an_array, (len(sample_ids), len(an_array) / len(sample_ids)))

            figure_file_names['correlation'].append(plots.new_correlation_plot(i,
                                                                               a_matrix,
                                                                               study,
                                                                               platform,
                                                                               sample_ids,
                                                                               symbols))
            row_labels = profile_data['sample_ids']
            col_labels = symbols
            figure_file_names['heatmap'].append(plots.new_heatmap(i, a_matrix,
                                                                  study,
                                                                  platform,
                                                                  row_labels,
                                                                  col_labels,
                                                                  False))
    else:
        result_matrix, row_labels, col_labels = match_and_merge(spps, symbols_selected)
        study = 'Combined'
        platforms = ''
        for spp in spps:
            _, _, platform = spp.split('|')
            platforms += platform + " "
        filename = plots.new_correlation_plot(0, result_matrix, study, platforms, row_labels, col_labels)
        figure_file_names['correlation'].append(filename)
        filename = plots.new_heatmap(0, result_matrix, study, platforms, row_labels, col_labels, True)
        figure_file_names['heatmap'].append(filename)

    response = HttpResponse(json.dumps(figure_file_names), content_type='text/json')
    return response

def match_and_merge(spps, symbols_selected):
    """

    :param spp_arg:
    :return:
    """
    profile_data_list = []
    co_samples_list = []
    symbols_list = []
    for i in range(len(spps)):
        spp = spps[i]
        symbols = symbols_selected[i]
        study, profile, platform = spp.split('|')
        symbols = symbols.split(',')
        # Get the profile data for these symbols; combined = True
        # profile_data = get_profile_data(study, profile, platform, ','.join(symbols), True)
        profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
        symbols_list.append(symbols)
        co_samples_list.append([json.loads(co_sample) for co_sample in profile_data['sample_attributes']])
        profile_data_list.append(profile_data)

    # From these results we need to find only those samples that have co-samples
    filter0 =  []
    for index1, attribute in enumerate(co_samples_list[0]):
        co_sample_id = attribute['co_sample']
        if co_sample_id != '':
            filter0.append(index1)

    an_array0 = array(profile_data_list[0]['values'])
    sample_count0 = profile_data_list[0]['sample_count']
    a_matrix0 = reshape(an_array0, (sample_count0, len(an_array0) / sample_count0))
    col_labels0 = symbols_list[0]
    no_of_symbols0 = len(col_labels0)

    an_array1 = array(profile_data_list[1]['values'])
    sample_count1 = profile_data_list[1]['sample_count']
    a_matrix1 = reshape(an_array1, (sample_count1, len(an_array1) / sample_count1))
    col_labels1 = symbols_list[1]

    result_matrix = zeros((len(filter0), len(col_labels0) + len(col_labels1)))
    row_labels = []
    result_index = 0
    for index in filter0:
        attribute = (co_samples_list[0])[index]
        control = attribute['control']
        co_sample_id = attribute['co_sample']
        if control:
            row_labels.append('C-' + co_sample_id)
        else:
            row_labels.append(('D-' + co_sample_id))
        sample_index = profile_data_list[1]['sample_ids'].index(co_sample_id)
        result_matrix[result_index, 0:no_of_symbols0] = a_matrix0[index]
        result_matrix[result_index, no_of_symbols0:] = a_matrix1[sample_index]
        result_index += 1

    col_labels0.extend(col_labels1)

    return result_matrix, row_labels, col_labels0


def statistics(request):
    # 1. Get all sample ids for given study, profile and platform
    # 2. Get all gene symbols for given study, profile and platform
    # 3. For each sample and for each gene symbol get expression value

    fdr_value_cutoff = float(request.GET.get('fdr_value_cutoff'))
    p_value_cutoff = float(request.GET.get('p_value_cutoff'))
    show_top = int(request.GET.get('show_top'))
    spp = request.GET.get('spp')
    study, profile, platform = spp.split('|')
    sample_ids = geo_data.get_sample_ids(study, profile, platform)
    control_sample_ids = []
    diseased_sample_ids = []
    for sample_id in sample_ids:
        sample_attributes = geo_data.get_sample_attributes(study, profile, platform, sample_id)
        if sample_attributes['control']:
            control_sample_ids.append(sample_id)
        else:
            diseased_sample_ids.append(sample_id)

    genes = geo_data.get_all_gene_symbols(study, profile, platform)
    no_of_genes = len(genes)
    control_exprs = zeros((no_of_genes, len(control_sample_ids)))
    diseased_exprs = zeros((no_of_genes, len(diseased_sample_ids)))
    for (g_index, gene) in enumerate(genes):
        gene_exprs = zeros(len(control_sample_ids))
        for (s_index, sample_id) in enumerate(control_sample_ids):
            expr_value = geo_data.get_gene_expression_value(study, profile, platform, sample_id, gene)
            if expr_value == 'None':
                continue
            gene_exprs[s_index] = expr_value
        control_exprs[g_index] = gene_exprs

        gene_exprs = zeros(len(diseased_sample_ids))
        for (s_index, sample_id) in enumerate(diseased_sample_ids):
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

    reject_bonferroni, pval_bonferroni = bonferroni_correction(p_values_series, alpha=p_value_cutoff)
    reject_fdr, pval_fdr = fdr_correction(p_values_series, alpha=fdr_value_cutoff, method='indep')

    bonferroni_p_values = p_values_series[reject_bonferroni]
    fdr_p_values = p_values_series[reject_fdr]
    fdr_values_series = Series(pval_fdr, index=genes)
    p_values_series.sort(ascending=True)
    fdr_values_series.sort(ascending=True)

    # display_values = [(p_values_series.index[i].split('_')[0], p_values_series[i]) for i in range(10)]
    display_p_values = [(p_values_series.index[i], p_values_series[i]) for i in range(show_top)]
    display_fdr_values = [(fdr_values_series.index[i], fdr_values_series[i]) for i in range(show_top)]
    response = render_to_string('statistics.html',
                                {"display_p_values": display_p_values,
                                 "display_fdr_values": display_fdr_values})

    return HttpResponse(response)

