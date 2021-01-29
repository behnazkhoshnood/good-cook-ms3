   // to avoid chossing duplicate value in marks when editing a recipe
$(document).ready(function () {
var marks = document.getElementById("mark");

[].slice.call(marks.options)
  .map(function(a){
    if(this[a.value]){ 
      marks.removeChild(a); 
    } else { 
      this[a.value]=1; 
    } 
  },{});
});