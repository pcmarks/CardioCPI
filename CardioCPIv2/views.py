__author__ = 'pcmarks'
"""
    The functions in this module implement the Django "View". That is, URLs are mapped (see urls.py)
    to a function here.

    Data is retrieved by calling functions omt geo_data.py module.

    NOTA BENE: PLEASE ADJUST os.environ["HOME"] (see below) to point to the home directory of the user that has
    imported the MNE statistical library. Apache messes up the environment variable HOME which MNE is
    dependent upon. NOT A GOOD WAY TO FIX THIS PROBLEM.

"""

import csv
import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from numpy import array, reshape, zeros
from pandas import DataFrame, Series
from scipy.stats import ttest_ind

#TODO: It would be nice to not have to do the following:
# We need to do the following so that the mne library can load. Apparently Apache
# deletes the HOME variable
import os
os.environ["HOME"] = "/home/pcmarks"

from mne.stats import fdr_correction

import plots
import geo_data

dataset_is_available = False

# When this file is loaded by Python, open up the expression database via SSDB.
# Show an error if the dataset cannot be opened
try:
    geo_data.db_open()
    dataset_is_available = True
except TypeError:
    pass


def home(request):
    """
    This is the "Home page" for the CardioCPI web application.

    :param request:
    :return:
    """

    return render(request, 'index.html', {"dataset_is_available": dataset_is_available})


def platform_selection(request):
    """
    The client has chosen a new platform. The old and new platform values are passed with
    a Javascript AJAX call. The geo database is asked to switch to the new platform so that the
    symbols for the new platform are loaded.

    :rtype : HttpResponse
    :param request:
    :return:
    """
    _, study, display_profile = request.GET.get("study_profile").split("|")
    profile = display_profile.replace('_', '-')
    new_platform = request.GET.get('new')
    old_platform = request.GET.get('old')
    # Called for its side effects - caching of a platform's symbols in session storage.
    geo_data.switch_platform(request, study, profile, new_platform, old_platform)
    return HttpResponse("HUH?")


def gene_selection(request):
    """
    The user has typed in some characters in the gene/mri symbol input fields. They are used
    to search the current set of symbols (found in session storage) for a match. Matches are
    made on any portion of the symbol. We got here via an AJAX javascript action initiated by
    Javascript Select2 library function.
    :param request:
    :return:
    """
    display_profile = request.GET.get('profile')
    profile = display_profile.replace('_', '-')
    symbols = request.GET.get('symbols')
    # Call on the backend datastore via SSDB
    gene_list = geo_data.match_symbols(request, profile, symbols)
    return HttpResponse(gene_list, content_type='text/json')


def all_plots(request):

    """
    The Plot button on the client web page has been pushed. Plotting parameters are passed
    as arguments in the HTTP request. Use these to determine what plots are to be drawn.
    The plots are drawn locally and stored in a temporary file. The names of these files are
    passed back to the client where a Javascript function will place them in the proper position
    within the web page.
    :param request:
    :return:
    """

    # Plot parameters are sent as JSON-encoded strings.
    import json
    spps = json.loads(request.GET.get(u'study_profile_platforms'))
    symbols_selected = json.loads(request.GET.get(u'symbols_selected'))
    combined_plot = json.loads(request.GET.get(u'combined_plot'))
    max_plots = int(json.loads(request.GET.get(u'max_plots')))
    #TODO: The following is completely arbitrary for now:
    # If this is a combined plot then choose half the symbols from each platform
    if combined_plot:
        max_plots /= 2

    # These file names are sent back to the client web page.
    figure_file_names = {'correlation': [], 'heatmap': []}
    # Are combined plots called for?
    if not combined_plot:
        # Not a combined plot, so create two plots per selected platform.
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
            for j in range(len(sample_ids)):
                attribute = json.loads(sample_attributes[j])
                if attribute['control']:
                    augmented_sample_ids.append('C-%s' % sample_ids[j])
                else:
                    augmented_sample_ids.append('D-%s' % sample_ids[j])

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
        # A combined plot is called for. This requires the extra step of merging the
        # symbols that are in common amongst the platforms.
        #TODO: We can only handle two platforms - sets of symbols. This should be fixed for more than two.
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

    # Pass back the names of the files containing all the plots to the client side javascript code.
    response = HttpResponse(json.dumps(figure_file_names), content_type='text/json')
    return response


def match_and_merge(spps, symbols_selected):
    """
    The function is called only when combined plots are selected. Only expression values from
    samples that have been measured for all of the selected platforms are used.

    The function also builds a list of sample ids and symbols that will be used as plotting labels

    TODO: NOTA BENE: The function can only handle two platforms. More than two should be allowed.

    :param spps:
    :return: the expression matrix, a list of samples (columns), a list of symbols (rows)
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
    filter0 = []
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
    This function is called when the Statistics button is pressed by the user. It's purpose is to
    take the selected platforms as well as some statistical parameters and perform two
    statistical functions: a T-Test and an FDR analysis

    :param request:
    :return: a rendered HTML page.
    """
    cutoff_type = request.GET.get('cutoff_type')
    cutoff_value = float(request.GET.get('cutoff_value'))
    display_values = request.session.get('display_values', {})
    spps = request.GET.get('spps')
    spps = spps.split(',')
    combined_series = []
    display_profile = None
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

        # Perform the the t-test and create a pandas Series
        t_statistics, p_values = ttest_ind(control_df.T, diseased_df.T)
        p_values_series = Series(p_values, index=genes)

        # Perform the fdr analysis, create a pandas Series and sort the series
        reject_fdr, pval_fdr = fdr_correction(p_values_series, method='indep')
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

        display_values[display_profile] = combined_series

    request.session['display_values'] = display_values
    response = render_to_string('statistics.html',
                                {display_profile: combined_series})

    return HttpResponse(response)


def export(request):

    """

    :param request:
    :return:
    """
    id_parameter = request.GET.get('id')
    _, profile = id_parameter.split('|')
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
