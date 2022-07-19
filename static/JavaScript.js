
$(document).ready(function(){
    $("#Sub1").click(function(){
        if ($("#password").val() != $("#password2").val()){
            alert("Passwords does not match");
        }   
    });
});


// Show Password Function
function showPsswrd() {
    var x = document.getElementById("password");
    var y = document.getElementById("password2");
    if (x.type === "password") {
      x.type = "text";
      y.type = "text";
    } else {
      x.type = "password";
      y.type = "password";
    }
}



