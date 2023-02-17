$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

$(function() {
    $('.truncate').click(function() {
      $(this).toggleClass('truncate-yes');
    });
});

function copy_to_clipboard(element) {
    // Copy the text inside the text field
    navigator.clipboard.writeText(element.innerHTML);
    return false;
};

function update_count(checkbox_name) {
    var x = $("." + checkbox_name + ":checked").length;
    document.getElementById(checkbox_name).innerHTML = x;
};