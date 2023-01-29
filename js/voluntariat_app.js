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
}