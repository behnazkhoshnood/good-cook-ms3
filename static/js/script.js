$(document).ready(function () {
    $(".sidenav").sidenav();
    $('.collapsible').collapsible();
    $('select').formSelect();
    $(".tooltipped").tooltip();
    $("input#username, input#password, input#confirm-password, input#first_name, input#last_name").characterCounter();
    $("select").formSelect();
});

$('li').filter(function(){
    return $(this).text().trim() === '';
}).remove();
