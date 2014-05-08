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
    $("div[id^=" + study + "-platform]").each(function(){
        $(this).toggle();
    });
}
var sleep = function(milliseconds) {
    var start = new Date().getTime();
    for (var i =0; i < 1e7; i++) {
        if ((new Date().getTime() - start) > milliseconds){
            break;
        }
    }
}
var p_values_select_all = function(){

};

var fdr_values_select_all = function(){

};

/*
 The function to execute when a t-test table entry checkbox is checked/unchecked
 */
var p_value_checked = function(the_checkbox){
    var gene_symbol = the_checkbox.id.split('-')[1];
    var flattened_list = $('#symbols_Expression-Genes').val()
    var current_list = []
    if (flattened_list.length > 0) {
        current_list = flattened_list.split(',')
    }
    if (the_checkbox.checked) {
        current_list.push(gene_symbol);
        var new_list = current_list.join(',');
        $('#symbols_Expression-Genes').val(new_list).trigger("change");
    } else {
        var ix = current_list.indexOf(gene_symbol)
        if (ix >= 0) {
            current_list.splice(ix,1)
        }
        var new_list = current_list.join(',')
        $('#symbols_Expression-Genes').val(new_list).trigger("change");
    }
};

$(document).ready(function () {

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
        var show_top = $("#show-top").val();
        var p_value_cutoff = $("#p-value-cutoff").val();
        var fdr_value_cutoff = $("#fdr-value-cutoff").val();
        $('#statistics').load('statistics?' +
                'spp=' + args[0] +
                '&show_top=' + show_top +
                '&p_value_cutoff=' + p_value_cutoff +
                '&fdr_value_cutoff=' + fdr_value_cutoff);
    });

    $('#t-test-collapsible').on('show', function (e) {

        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study.")
            return false;
        }

        // Execute an AJAX request for the t-test tables
        var args = [];
        $('select').each(function () {
            if (this.value != 'none') {
                args.push(this.id + '|' + this.value);
            }
        });
        $('#t-test-values').load('t-tests?spp=' + args[0]);

    });

    $('#fdr-test-collapsible').on('show', function (e) {
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study.")
            $("#plot_btn").removeAttr("disabled");
            return false;
        }
        // Disable the button whilst processing
        $('#t-test-btn').attr('disabled', 'disabled')

        // Execute an AJAX request for the t-test tables
        var args = [];
        $('select').each(function () {
            if (this.value != 'none') {
                args.push(this.id + '|' + this.value);
            }
        });
        $('#fdr-test-values').load('fdr-tests?spp=' + args[0]);
    });

    $('.btn-group').button();

  /*
   * Attach a function to the platform select elements. Selecting an element results in a 
   * server request to load or unload that platform's symbols.
   */
   $('select').change(function(e) {
      var chosen_one = $(this).val()
      console.log(chosen_one)
      // release current symbol set
      var hidden = $(this).siblings('#platform');
      // load new symbol set and save id
      //chosen_one = chosen_one.replace(/\|/g, "/")
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
    A call is made to an R functions, via opencpu, that will return a list of
    symbols that contain the typed in characters.
     */
    $("[id^='symbols_']").each(function() {
        var thisId = this.id;
        var tokens = thisId.split('_')
        $(this).select2({
            minimumInputLength: 2,
            maximumInputLength: 6,
            multiple: true,
            ajax: {
                url: 'gene_selection',
                dataType: 'json',
                data: function(term, page) {
                    return {
                        profile: tokens[1],
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
//            tokenizer: function(input, selection, callback) {
//                if (input.indexOf(',') < 0) return;
//                var parts = input.split(',');
//                for (var i = 0; i < parts.length; i++) {
//                    var part = parts[i];                        yyy, xxx, abc
//                    part = part.trim();
//                    var valid = false;
//                    if (['abc','xxx', 'yyy'].indexOf(part) >= 0) {
//                        valid = true;
//                    }
//                    if (valid) {
//                        callback({id: part, text: part});
//                    }
//                }
//            }
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
                study_profile_platforms.push(study_profile_platform);
                var tokens = study_profile_platform.split('|')
                symbols_selected.push($("#symbols_" + tokens[1]).val());
            }
        });
        // Set aside div's to hold all of the plots
        for (var i = 0; i < no_of_studies; i++) {
            $("#heatmaps").append("<div id='heatmap-plot-" + i +
                "' class='plot'> </div>");
            $("#correlation-plots").append("<div id='correlation-plot-" + i +
                "' class='plot'> </div>");
        }

        var request = $.ajax({
            dataType: "json",
            url: '/plots',
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
