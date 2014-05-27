/**
 * Created with IntelliJ IDEA.
 * User: pcmarks
 * Date: 12/5/13
 * Time: 11:15 AM
 * To change this template use File | Settings | File Templates.
 */

/*
 * toggle_platforms(study)
 *
 * Look for platform ids starting with study + "-platform" and toggle them on and off
 * Triggered by selecting/deselecting a study/cancer checkbox.
 */
var toggle_platforms = function(study) {
    $('select[id^=' + study +']').get(0).selectedIndex = 0;
    $("div[id^=" + study + "-platform]").each(function(){
        $(this).toggle();
    });
}
var eg_values_select_all = function(all_checkbox){
    if (all_checkbox.checked) {
        $("input[id^=checkbox-eg]").each(function() {
            if (!$(this).prop("checked")) {
                $(this).click();
            }
        });
    } else {
        $("input[id^=checkbox-eg]").each(function() {
            if ($(this).prop("checked")) {
                $(this).click();
            }
        })
    }
};

var mi_values_select_all = function(all_checkbox){
    if (all_checkbox.checked) {
        $("input[id^=checkbox-mi]").each(function() {
            if (!$(this).prop("checked")) {
                $(this).click();
            }
        });
    } else {
        $("input[id^=checkbox-mi]").each(function() {
            if ($(this).prop("checked")) {
                $(this).click();
            }
        })
    }
};

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
};

$(document).ready(function () {

//    // Initialize the datatables
//    $('#eg-stats').DataTable({
//        "processing": true,
//        "serverSide": true,
//        "ajax": "cardiocpi/statspage?platform=eg"
//    });
//    $('#mi-stats').DataTable({
//        "processing": true,
//        "serverSide": true,
//        "ajax": "cardiocpi/statspage?platform=mi"
//    });

    $('#statistics-btn').click(function() {
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study and platform.")
            return false;
        }

        // Execute an AJAX request for the statistics
        var args = [];
        $('select').each(function () {
            if (this.value != 'none') {
                args.push(this.id + '|' + this.value);
            }
        });
        if (args.length == 0) {
            alert("At least one platform must be selected.")
            return false;
        }
        var show_top = $("#show-top").val();
        var p_value_cutoff = $("#p-value-cutoff").val();
        var fdr_value_cutoff = $("#fdr-value-cutoff").val();
        $('#statistics').load('cardiocpi/statistics?' +
                'spps=' + args +
                '&show_top=' + show_top +
                '&p_value_cutoff=' + p_value_cutoff +
                '&fdr_value_cutoff=' + fdr_value_cutoff);
    });

    $('.btn-group').button();
  /*
   * Attach a function to the platform select elements. Selecting an element results in a 
   * server request to load or unload that platform's symbols.
   */
   $('select').change(function(e) {
      var chosen_one = $(this).val()
      // release current symbol set
      var hidden = $(this).siblings('#platform');
       $.ajax({
           type: 'GET',
           dataType: 'json',
           url: 'cardiocpi/platform_selection',
           data: {study_profile: this.id, new: chosen_one, old: hidden.val()}
       })
      hidden.val(chosen_one);
    });

    /*
    Attach select2 functionality to the gene symbol input boxes.
    A call is made to an R functions, via opencpu, that will return a list of
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
                url: 'cardiocpi/gene_selection',
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
     * Attach a function to the clear symbols button
     */
    $('#clear-symbols').click(function(e) {
        $('#symbols_Expression_Genes').select2("val", "");
        $('#symbols_Expression_miRNA').select2("val", "");
        $("input[id^=all-p-values]").each(function() {
            if ($(this).prop('checked')) {
                $(this).click();
            }
        });
        $("input[id^=checkbox-eg]").each(function() {
            if ($(this).prop('checked')) {
                $(this).click();
            }
        });
        $("input[id^=checkbox-mi]").each(function() {
            if ($(this).prop('checked')) {
                $(this).click();
            }
        });
    });

    /*
    Attach a function to the plot button.
    Determine the number of studies that have been chosen, assemble the symbols
    to be analyzed, and call for the plotting of the correlation plots and heatmaps.
    If a combined plot is being asked for, handle differently. 
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
        $('select').each(function() {
            if (this.value != 'none') {
                var study_profile_platform = this.id + '|' + this.value;
                var tokens = study_profile_platform.split('|')
                var symbols = $("#symbols_" + tokens[1]).val();
                if (typeof symbols != 'undefined') {
                    study_profile_platforms.push(study_profile_platform);
                    symbols_selected.push(symbols);
                }
            }
        });
        if (study_profile_platforms.length == 0) {
            alert("At least one platform must be selected.")
            return false;
        }
        var no_symbols = false;
        for (var i = 0; i < study_profile_platforms.length; i++) {
            if (symbols_selected[i] == "") {
                no_symbols = true;
                var tokens = study_profile_platforms[i].split('|');
                alert("No symbols selected for the " + tokens[2] + " platform.");
            }
        }
        if (no_symbols) {
            return false;
        }
        // Set aside div's to hold all of the plots
        for (var i = 0; i < no_of_studies; i++) {
            $("#heatmaps").append("<div id='heatmap-plot-" + i +
                "' class='plot'> </div>");
            $("#correlation-plots").append("<div id='correlation-plot-" + i +
                "' class='plot'> </div>");
        }

        var request = $.ajax({
            dataType: "json",
            url: 'cardiocpi/plots',
            data: {no_of_studies: JSON.stringify(no_of_studies),
                combined_plot: JSON.stringify($('#combined-plot').prop("checked")),
                study_profile_platforms: JSON.stringify(study_profile_platforms),
                symbols_selected: JSON.stringify(symbols_selected)
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
