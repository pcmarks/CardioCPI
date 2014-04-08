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
$(document).ready(function () {
  
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
        $('#t_tests').empty();
        
        if ($('#combined-plot').prop("checked")) {
          plot_combined();
          // Re-enable the button.
          $("#plot_btn").removeAttr("disabled");
          return
        }
        // Set aside div's to hold all of the plots
        for (var i = 1; i <= no_of_studies; i++) {
            $("#heatmaps").append("<div id='heatmap-" + i +"'> </div>");
            $("#correlation-plots").append("<div id='correlation-plot-" + i +"'> </div>");
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
        }
        // TODO: Delay for four seconds. This may or may not allow both plots to be drawn without one
        // interfering with the other.
        // Could be removed possibly if mod_wsgi and daemon mode are used.
        sleep(4000);
        for (i = 0; i < args.length; i++) {
          var tokens = args[i].split('|');
          var symbols_selected = $("#symbols_" + tokens[1]).val();
            $("#heatmap-" + (i + 1)).append(
                '<img src="chart/heatmap?spp=' + args[i] + '&symbols=' + symbols_selected + '">')
        }
        // TODO: Another sleep that could be removed
        sleep(4000)
        $("#t_tests").append('<img src="chart/t_tests?spp=' + args[0] + '">')

        // Re-enable the button.
        $("#plot_btn").removeAttr("disabled");
    });
    
    plot_combined = function() {
        // Set aside  1 div for each plot
        $("#heatmaps").append("<div id='heatmap-1'></div>");
        $("#correlation-plots").append("<div id='correlation-plot-1'></div>")
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