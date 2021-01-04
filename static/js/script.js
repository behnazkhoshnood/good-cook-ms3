$(document).ready(function () {
    $(".sidenav").sidenav();
    $('.collapsible').collapsible();
    $(".tooltipped").tooltip();
    $("input#username, input#password, input#confirm-password, input#first_name, input#last_name").characterCounter();
    $("select").formSelect();
});