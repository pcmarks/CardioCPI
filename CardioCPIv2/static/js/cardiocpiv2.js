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
        var show_top = $("#shot-top").val();
        var p_value_cutoff = $("#p-value-cutoff").val();
        var fdr_value_cutoff = $("#fdr-value-cutoff").val();
        $('#statistics').load('statistics?spp=' + args[0]);
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
        });
    });

    /*
    Attach a function to the plot button.
    Determine the number of studies that have been chosen, assemble the symbols
    to be analyzed, and call for the plotting of the correlation plots and heatmaps.
    If a combined plot is being asked for, handle differently. 
     */
    $('#test-plot-btn').click(function(e) {
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study.")
            $("#plot_btn").removeAttr("disabled");
            return false;
        }
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

        $.getJSON('/plots',
            {no_of_studies: JSON.stringify(no_of_studies),
             combined_plot: JSON.stringify($('#combined-plot').prop("checked")),
             study_profile_platforms: JSON.stringify(study_profile_platforms),
             symbols_selected: JSON.stringify(symbols_selected)
            },
            function(data) {
                $.each(data, function(index, element) {
                    $('body').append($('<div>', { text: element.name}))
            })
        })
    });

    $('#plot-btn').click(function(e) {
        // Disable the button whilst processing..
        $('#plot_btn').attr('disabled', 'disabled');
        // Need to have chosen at least one study. Count the number of checkboxes that are checked.
        var no_of_studies = $("input[id$='CB']").filter(":checked").length;
        if (no_of_studies == 0) {
            alert("You must choose at least one study.")
            $("#plot_btn").removeAttr("disabled");
            return false;
        }
        // Remove previous images if there were any
        $('#heatmaps').empty();
        $('#correlation-plots').empty();

        if ($('#combined-plot').prop("checked")) {
          plot_combined();
          // Re-enable the button.
          $("#plot_btn").removeAttr("disabled");
          return
        }
        // Set aside div's to hold all of the plots
        for (var i = 1; i <= no_of_studies; i++) {
            $("#heatmaps").append("<div id='heatmap-" +
                                    i +
                                    "' class='plot'> </div>");
            $("#correlation-plots").append("<div id='correlation-plot-" +
                                            i +
                                            "' class='plot'> </div>");
        }
        var genes_selected = $("#symbols_Expression-Genes").val();
        var mirnas_selected = $("#symbols_Expression-miRNA").val();
        var args = [];
        $('select').each(function() {
          if (this.value != 'none') {
            args.push(this.id + '|' + this.value);
          }
        });
        for (i = 0; i < args.length; i++) {
          var tokens = args[i].split('|');
          var symbols_selected = $("#symbols_" + tokens[1]).val();
          $("#correlation-plot-" + (i + 1)).append(
              '<img src="chart/correlation?spp=' + args[i] + '&symbols=' + symbols_selected + '">')
            sleep(4000);
        }
        // TODO: Delay for four seconds. This may or may not allow both plots to be drawn without one
        // interfering with the other.
        // Could be removed possibly if mod_wsgi and daemon mode are used.
        for (i = 0; i < args.length; i++) {
          var tokens = args[i].split('|');
          var symbols_selected = $("#symbols_" + tokens[1]).val();
            $("#heatmap-" + (i + 1)).append(
                '<img src="chart/heatmap?spp=' + args[i] + '&symbols=' + symbols_selected + '">')
            sleep(4000);
        }

        // Re-enable the button.
        $("#plot_btn").removeAttr("disabled");
    });
    
    plot_combined = function() {
        // Set aside  1 div for each plot
        $("#heatmaps").append("<div id='heatmap-1' class='plot'></div>");
        $("#correlation-plots").append("<div id='correlation-plot-1' class='plot'></div>")
        var genes_selected = $("#symbols_Expression-Genes").val();
        var mirnas_selected = $("#symbols_Expression-miRNA").val();
        var args = [];
        $('select').each(function() {
          if (this.value != 'none') {
            var tokens = this.id.split('|');
            var symbols = $("#symbols_" + tokens[1]).val();
            symbols = symbols.replace(/,/g,' ');
            args.push(this.id + '|' + this.value + '|' + symbols);
          };
        });
        // For a combined plot we want all of the symbols
        var symbols_selected = [];
        $("[id^='symbols']").each(function() {
          symbols_selected.push(this.value);
        })
        $("#correlation-plot-1").append(
            '<img src="chart/combined_correlation?spp=' + args + '&symbols=' + symbols_selected + '">'
        )
//        var jqxhr_correlation = $("#correlation-plot-1").r_fun_plot(
//                          "plot_combined_correlation2",
//                          {study_profile_platform_symbols: args,
//                           symbols: symbols_selected
//                          }
//                      ).fail(function(){
//                        alert("Failure: " + jqxhr_correlation.responseText)});

        $("#heatmap-1").append(
            '<img src="chart/combined_heatmap?spp=' + args + '&symbols=' + symbols_selected + '">'
        )
//        var jqxhr_correlation = $("#heatmap-1").r_fun_plot(
//                          "plot_combined_heatmap",
//                          {study_profile_platform_symbols: args,
//                           symbols: symbols_selected
//                          }
//                      ).fail(function(){
//                        alert("Failure: " + jqxhr_correlation.responseText)});
    };

});
//"plot_combined_heatmap",
//                          {study_profile_platform_symbols: args,
//                           symbols: symbols_selected
//                          }
//                      ).fail(function(){
//                        alert("Failure: " + jqxhr_correlation.responseText)});
//    };
//
//});