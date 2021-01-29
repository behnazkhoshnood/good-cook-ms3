$(document).ready(function () {
    $('.sidenav').sidenav();
    $('.collapsible-li:first').addClass('active');
    $('.collapsible').collapsible();
    $('select').formSelect();
    $('.tooltipped').tooltip();
    $('input#username, input#password, input#confirm-password, input#first_name, input#last_name').characterCounter();
    $('select').formSelect();
       // to avoid empty strings
    $('li, .edit-delete-div').filter(function () {
        return $(this).text().trim() === '';}).remove();
       // profile info note
    $('.profile-list').filter(function () {
        return $(this).text().trim() === '';
    }).append("<h6 class='profile-note'>You didn't add any recipe yet. Click on add recipe in the menu to add your recipe.</h6>").removeClass('collapsible');
       // fixing select validation
 validateMaterializeSelect();
    function validateMaterializeSelect() {
        let classValid = { "border-bottom": "1px solid #4527a0", "box-shadow": "0 1px 0 0 #4527a0" };
        let classInvalid = { "border-bottom": "1px solid #ad1457", "box-shadow": "0 1px 0 0 #ad1457" };
        if ($("select.validate").prop("required")) {
            $("select.validate").css({ "display": "block", "height": "0", "padding": "0", "width": "0", "position": "absolute" });
        }
        $(".select-wrapper input.select-dropdown").on("focusin", function () {
            $(this).parent(".select-wrapper").on("change", function () {
                if ($(this).children("ul").children("li.selected:not(.disabled)").on("click", function () { })) {
                    $(this).children("input").css(classValid);
                }
            });
        }).on("click", function () {
            if ($(this).parent(".select-wrapper").children("ul").children("li.selected:not(.disabled)").css("background-color") === "rgba(0, 0, 0, 0.03)") {
                $(this).parent(".select-wrapper").children("input").css(classValid);
            } else {
                $(".select-wrapper input.select-dropdown").on("focusout", function () {
                    if ($(this).parent(".select-wrapper").children("select").prop("required")) {
                        if ($(this).css("border-bottom") != "1px solid rgb(69, 39, 160)") {
                            $(this).parent(".select-wrapper").children("input").css(classInvalid);
                        }
                    }
                });
            }
        });
    }
       // Warrning notes
    $('.delete-btn').click(function () {
        var checkstr = confirm('are you sure you want to delete this recipe?');
        if (checkstr == true) {
        } else {
            return false;
        }
    });
    $('.log-out').click(function () {
        var checkstr = confirm('are you sure you want to log out?');
        if (checkstr == true) {
        } else {
            return false;
        }
    });
        $('.cancel-btn').click(function () {
        var checkstr = confirm('are you sure you want to cancel?');
        if (checkstr == true) {
        } else {
            return false;
        }
    });
   // to make the height of the cards header equal
    var manageTitleHight = 0;

$(".manage-title").each(function(){
   if ($(this).height() > manageTitleHight) { manageTitleHight = $(this).height(); }
});

$(".manage-title").height(manageTitleHight);
   // to avoid copying the link of the delete and edit btns
$(".delete-btn, .edit-btn").contextmenu(function () { return false; });
});


