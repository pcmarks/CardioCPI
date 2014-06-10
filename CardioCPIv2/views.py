import csv

__author__ = 'pcmarks'

import json

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from numpy import array, reshape, zeros
from pandas import DataFrame, Series
from scipy.stats import ttest_ind

# import os
# os.environ["HOME"] = "/home/pcmarks"

from mne.stats import fdr_correction

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
    _, study, display_profile = request.GET.get("study_profile").split("|")
    profile = display_profile.replace('_', '-')
    new_platform = request.GET.get('new')
    old_platform = request.GET.get('old')
    # Called for its side effects - caching of a platform's symbols in session storage.
    geo_data.new_switch_platform(request, study, profile, new_platform, old_platform)
    return HttpResponse("HUH?")


def gene_selection(request):
    """

    :param request:
    :return:
    """
    display_profile = request.GET.get('profile')
    profile = display_profile.replace('_', '-')
    symbols = request.GET.get('symbols')
    gene_list = geo_data.new_match_symbols(request, profile, symbols)
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
    max_plots = int(json.loads(request.GET.get(u'max_plots')))
    # If this is a combined plot then choose half the symbols from each platform
    if combined_plot:
        max_plots = max_plots / 2
    # print spps, symbols_selected, combined_plot
    figure_file_names = {'correlation': [], 'heatmap': []}
    if not combined_plot:
        for i in range(len(spps)):
            spp = spps[i]
            _, study, display_profile, platform = spp.split('|')
            profile = display_profile.replace('_', '-')
            symbols = (symbols_selected[i].split(','))[:max_plots]
            if len(symbols) == 0:
                break
            profile_data = geo_data.get_profile_data(study, profile, platform, symbols, False)
            sample_ids = profile_data['sample_ids']
            sample_attributes = profile_data['sample_attributes']
            augmented_sample_ids = []
            for i in range(len(sample_ids)):
                attribute = json.loads(sample_attributes[i])
                if attribute['control']:
                    augmented_sample_ids.append('C-%s' % sample_ids[i])
                else:
                    augmented_sample_ids.append('D-%s' % sample_ids[i])

            an_array = array(profile_data['values'])
            a_matrix = reshape(an_array, (len(sample_ids), len(an_array) / len(sample_ids)))

            figure_file_names['correlation'].append(plots.new_correlation_plot(i,
                                                                               a_matrix,
                                                                               study,
                                                                               platform,
                                                                               augmented_sample_ids,
                                                                               symbols))
            row_labels = augmented_sample_ids
            col_labels = symbols
            figure_file_names['heatmap'].append(plots.new_heatmap(i, a_matrix,
                                                                  study,
                                                                  platform,
                                                                  row_labels,
                                                                  col_labels,
                                                                  False))
    else:
        # Adjust the number of symbols to use: half and half
        symbols_selected[0] = ','.join((symbols_selected[0].split(','))[:max_plots])
        symbols_selected[1] = ','.join((symbols_selected[1].split(','))[:max_plots])
        result_matrix, row_labels, col_labels = match_and_merge(spps, symbols_selected)
        study = 'Combined'
        platforms = ''
        for spp in spps:
            _, _, _, platform = spp.split('|')
            platforms += platform + " "
        filename = plots.new_correlation_plot(0, result_matrix, study, platforms, row_labels, col_labels)
        figure_file_names['correlation'].append(filename)
        filename = plots.new_heatmap(0, result_matrix, study, platforms, row_labels, col_labels, True)
        figure_file_names['heatmap'].append(filename)

    response = HttpResponse(json.dumps(figure_file_names), content_type='text/json')
    return response


def match_and_merge(spps, symbols_selected):
    """

    :param spps:
    :return:
    """
    profile_data_list = []
    co_samples_list = []
    symbols_list = []
    for i in range(len(spps)):
        spp = spps[i]
        symbols = symbols_selected[i]
        _, study, display_profile, platform = spp.split('|')
        profile = display_profile.replace('_', '-')
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
    """

    :param request:
    :return:
    """
    cutoff_type = request.GET.get('cutoff_type')
    cutoff_value = float(request.GET.get('cutoff_value'))
    display_values = request.session.get('display_values', {})
    show_top = 140;
    spps = request.GET.get('spps')
    spps = spps.split(',')
    for spp in spps:
        _, study, display_profile, platform = spp.split('|')
        profile = display_profile.replace('_', '-')
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
        from geo_data import db_open, db_close
        db_open()
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

        db_close()
        control_df = DataFrame(control_exprs, index=genes, columns=control_sample_ids)
        diseased_df = DataFrame(diseased_exprs, index=genes, columns=diseased_sample_ids)

        # Perform the the t-test
        t_statistics, p_values = ttest_ind(control_df.T, diseased_df.T)

        p_values_series = Series(p_values, index=genes)

        # Perform the fdr analysis
        #reject_bonferroni, pval_bonferroni = bonferroni_correction(p_values_series, alpha=p_value_cutoff)
        reject_fdr, pval_fdr = fdr_correction(p_values_series, method='indep')

        # bonferroni_p_values = p_values_series[reject_bonferroni]
        # fdr_p_values = p_values_series[reject_fdr]
        fdr_values_series = Series(pval_fdr, index=genes)
        p_values_series.sort(ascending=True)
        combined_series = []
        for i in range(len(p_values_series)):
            symbol = p_values_series.index[i]
            p_value = p_values_series[i]
            if cutoff_type == 'p-value' and p_value > cutoff_value:
                break
            fdr_value = fdr_values_series.get(symbol)
            if cutoff_type == 'fdr-value' and fdr_value > cutoff_value:
                break
            combined_series.append([symbol, p_value, fdr_value])
        # fdr_values_series.sort(ascending=True)
        display_values[display_profile] = combined_series
        # display_values = [(p_values_series.index[i].split('_')[0], p_values_series[i]) for i in range(10)]
        # display_values[display_profile] = [(p_values_series.index[i], p_values_series[i]) for i in range(show_top)]
        # display_fdr_values[display_profile] = [(fdr_values_series.index[i], fdr_values_series[i]) for i in range(show_top)]
    request.session['display_values'] = display_values
    response = render_to_string('statistics.html',
        {display_profile: combined_series})
                                # {"display_p_values": display_p_values,
                                #  "display_fdr_values": display_fdr_values})

    return HttpResponse(response)

def export(request):

    id = request.GET.get('id')
    _, profile = id.split('|')
    display_profile = profile.replace('-', '_')
    try:
        stats = request.session['display_values']
    except KeyError:
        return HttpResponse()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s-stats.csv"' % profile
    writer = csv.writer(response)
    values = stats[display_profile]
    for line in values:
        writer.writerow(line)
    return response

