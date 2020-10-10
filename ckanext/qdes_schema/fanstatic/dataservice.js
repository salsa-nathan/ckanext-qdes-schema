jQuery(document).ready(function () {
    //  Remove any input name="_ckan_phase" fields from the form
    jQuery('input[name="_ckan_phase"]').each(function() {
        jQuery(this).remove();
    });
});