/**
 * Created with IntelliJ IDEA.
 * User: pcmarks
 * Date: 12/5/13
 * Time: 11:15 AM
 */

/*
 * toggle_platforms(study)
 *
 * Look for platform ids starting with study + "-platform" and toggle them on and off
 * Triggered by selecting/deselecting a study/cancer checkbox.
 */
var toggle_platforms = function(study) {
    $("select[id^='platform|" + study +"']").get(0).selectedIndex = 0;
    $("div[id^=" + study + "-platform]").each(function(){
        $(this).toggle();
    });
}

/*
 The function to execute when a statistic table entry checkbox is checked/unchecked
 */
var p_value_checked = function(the_checkbox){
    var tokens = the_checkbox.id.match(/checkbox-(..)-t-(.+)/);
    if (tokens.length != 3) {
        alert("Internal error: 1");
        return false;
    }
    var profile = tokens[1];
    var gene_symbol = tokens[2];
    if (profile == 'eg') {
        var flattened_list = $('#symbols_Expression_Genes').val()
    } else {
        var flattened_list = $('#symbols_Expression_miRNA').val()
    }

    var current_list = []
    if (flattened_list.length > 0) {
        current_list = flattened_list.split(',')
    }
    if (the_checkbox.checked) {
        current_list.push(gene_symbol);
        var new_list = current_list.join(',');
        if (profile == 'eg') {
            $('#symbols_Expression_Genes').val(new_list).trigger("change");
        } else {
            $('#symbols_Expression_miRNA').val(new_list).trigger("change");
        }
    } else {
        var ix = current_list.indexOf(gene_symbol)
        if (ix >= 0) {
            current_list.splice(ix,1)
        }
        var new_list = current_list.join(',')
        if (profile == 'eg') {
            $('#symbols_Expression_Genes').val(new_list).trigger("change");
        } else {
            $('#symbols_Expression_miRNA').val(new_list).trigger("change");
        }
    }
}

// This function is executed when the Export as CSV button is pushed
var export_statistics = function(id) {
    window.location = 'export?id='+id;
}


$(document).ready(function () {

    // The Statistics button will call the server side function to prepare
    // statistical analyses. Arguments to this function include platform names
    // and a cutoff for p-values or fdr values.
    $("[id^='statistics-btn']").click(function() {
        // extract the data to use from the button's id
        var tokens = (this.id).split('-');
        var data_profile = tokens[2];

        // Don't do any statistics calculation if there are no studies chosen
        // because this means no platforms are chosen.
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study and platform.")
            return false;
        }

        // Build the arguments to the server-side statistical routines. There must
        // be at least one platform chosen.
        var args = [];
        $("select[id^='platform|']").each(function () {
            if (data_profile == 'eg' && (this.id).search('Expression_Genes') >= 0) {
                if (this.value != 'none') {
                    args.push(this.id + '|' + this.value);
                }
            }
            if (data_profile == 'mi' && (this.id).search('Expression_miRNA') >= 0) {
                if (this.value != 'none') {
                    args.push(this.id + '|' + this.value);
                }
            }
        });
        if (args.length == 0) {
            alert("At least one platform must be selected.")
            return false;
        }
        var cutoff_type = $("#cutoff-type-"+data_profile).val();
        var cutoff_value = $("#cutoff-value-"+data_profile).val();

        // Show the spinner whilst we compute the statistics
        $('#loading').show();
        // Clear any previous statistics
        $('#statistics-'+data_profile).empty();
        // Place the statistical tables in an area that has been set aside.
        // Turn off (hide) the spinner.
        $('#statistics-'+data_profile).load('statistics?' +
                'data_profile=' + data_profile +
                '&spps=' + args +
                '&cutoff_type=' + cutoff_type +
                '&cutoff_value=' + cutoff_value,
            function() {$('#loading').hide();});
    });

    $('.btn-group').button();
  /*
   * Attach a function to the platform select elements. Selecting an element results in a 
   * server request to load or unload that platform's symbols.
   */
   $("select[id^='platform|']").change(function(e) {
      var chosen_one = $(this).val();
      // release current symbol set
      var hidden = $(this).siblings('#platform');
       $.ajax({
           type: 'GET',
           dataType: 'json',
           url: 'platform_selection',
           data: {study_profile: this.id, new: chosen_one, old: hidden.val()}
       })
      hidden.val(chosen_one);
    });

    /*
    Attach select2 functionality to the gene symbol input boxes.
    An ajax request is made to the server which will return a list of
    symbols that contain the typed in characters.
     */
    $("[id^='symbols_']").each(function() {
        var thisId = this.id;
        var profile = thisId.replace('symbols_','')
        $(this).select2({
            minimumInputLength: 2,
            maximumInputLength: 6,
            multiple: true,
            ajax: {
                url: 'gene_selection',
                dataType: 'json',
                data: function(term, page) {
                    return {
                        profile: profile,
                        symbols: term
                    }
                },
                results: function(data, page) {
                    var selections = []
                    $(data).each(function(key, symbol) {
                        selections.push({id: symbol, text: symbol});
                    });
                    return {more: false, results: selections};
                }
            },
            initSelection : function (element, callback) {
                var data = [];
                $(element.val().split(",")).each(function () {
                    data.push({id: this, text: this});
                });
                callback(data);
            }
        });
    });

    /*
     * Attach a function to the Clear symbols button
     */
    $('#clear-symbols').click(function(e) {
        $('#symbols_Expression_Genes').select2("val", "");
        $('#symbols_Expression_miRNA').select2("val", "");
    });

    /*
    Attach a function to the Plot button.
    Determine the number of studies that have been chosen, assemble the symbols
    to be analyzed, and call for the plotting of the correlation plots and heatmaps.
    Note whether a combined plot is being asked for.
     */
    $('#plot-btn').click(function(e) {
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study.")
            $("#plot_btn").removeAttr("disabled");
            return false;
        }
        // Remove previous images if there were any
        $('#heatmaps').empty();
        $('#correlation-plots').empty();

        var study_profile_platforms = [];
        var symbols_selected = [];

        $("select[id^='platform|']").each(function() {
            if (this.value != 'none') {
                var study_profile_platform = this.id + '|' + this.value;
                var tokens = study_profile_platform.split('|')
                var symbols = []
                var xsymbols = $("#symbols_" + tokens[2]).val();
                if (typeof xsymbols != 'undefined') {
                    study_profile_platforms.push(study_profile_platform);
                }
                if (tokens[2] == "Expression_Genes") {
                    var oTT = TableTools.fnGetInstance('eg-stats');
                } else {
                    var oTT = TableTools.fnGetInstance('mi-stats');
                }
                if (oTT && typeof oTT != 'undefined') {
                    var aData = oTT.fnGetSelectedData();
                    var ysymbols = [];
                    for (var i = 0; i < aData.length; i++) {
                        ysymbols.push(aData[i][0]);
                    }
                    if (xsymbols != '') {
                        if (ysymbols.length > 0) {
                            symbols = xsymbols + ',' + ysymbols.join(',');
                        } else {
                            symbols = xsymbols
                        }
                    } else {
                        if (ysymbols.length > 0)
                        symbols = ysymbols.join(',');
                    }
                } else {
                    symbols = xsymbols;
                }
                symbols_selected.push(symbols);
            }
        });
        if (study_profile_platforms.length == 0) {
            alert("At least one platform must be selected.")
            return false;
        }
        var symbols_chosen = []
        for (var i = 0; i < study_profile_platforms.length; i++) {
            if (symbols_selected[i] == "") {
                symbols_chosen.push(false)
                var tokens = study_profile_platforms[i].split('|');
                alert("No symbols selected for the " + tokens[2] + " platform.");
            } else {
                symbols_chosen.push(true)
            }
        }
        var any_symbols_chosen = false
        for (var i = 0; i < study_profile_platforms.length; i++) {
            if (symbols_chosen[i]) {
                any_symbols_chosen |= true
            } else {
                any_symbols_chosen |= false
                study_profile_platforms.splice(i, 1);
                symbols_selected.splice(i, 1);
            }
        }
        if (!any_symbols_chosen) {
            return false;
        }
        // Set aside div's to hold all of the plots
        for (var i = 0; i < no_of_studies; i++) {
            $("#heatmaps").append("<div id='heatmap-plot-" + i +
                "' class='plot'> </div>");
            $("#correlation-plots").append("<div id='correlation-plot-" + i +
                "' class='plot'> </div>");
        }
        // If this is a combined plot then at least two sets of symbols must be
        // selected
        if ($('#combined-plot').prop('checked') && study_profile_platforms.length < 2) {
            alert("At least two sets of data required for combined plot.")
            return false;
        }
        // Some symbols have been chosen, now limit the number that will be plotted
        var max_plots = Number($('#max-plots').val());
        for (var i = 0; i < study_profile_platforms.length; i++) {
            symbols_selected[i] = symbols_selected[i].split(',').splice(0, max_plots).join(',')
        }
        var request = $.ajax({
            dataType: "json",
            url: 'plots',
            data: {no_of_studies: JSON.stringify(no_of_studies),
                combined_plot: JSON.stringify($('#combined-plot').prop("checked")),
                study_profile_platforms: JSON.stringify(study_profile_platforms),
                symbols_selected: JSON.stringify(symbols_selected),
                max_plots: JSON.stringify($('#max-plots').val())
                }
        });
        request.done(function(result) {
            var filenames = result['correlation']
            $.each(filenames, function(i, element) {
                $("#correlation-plot-" + i).append('<img src="' + element + '">')
            });
            filenames = result['heatmap']
            $.each(filenames, function(i, element) {
                $("#heatmap-plot-" + i).append('<img src="' + element + '">')
            });
        });
        request.fail(function(jqXHR, textStatus) {
            alert("Server side failure: " + textStatus);
        });
    });

 });
