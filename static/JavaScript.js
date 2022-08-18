// Show Password Function
function showPsswrd(id) {
  if (id == 1){
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
  else if (id == 2){
    var z = document.getElementById("verPasswd");
    if (z.type === "password") {
      z.type = "text";
    } else {
      z.type = "password";
    }
  }
  else if (id == 3){
    var w = document.getElementById("verPasswd3");
    if (w.type === "password") {
      w.type = "text";
    } else {
      w.type = "password";
    }
  }
}



// Validate password and send verification Email 
$(document).ready(function(){
    $("#Sub1").click(function(){
        if ($("#password").val() != $("#password2").val()){
            alert("Passwords does not match");
        }
        /*
        else if ($("#password").val() == $("#password2").val()){
          let email = $("#email").val()
          let Fname = $("#Fname").val()
          let Lname = $("#Lname").val()
          console.log(email);
          // sendMail(email, Fname, Lname)
          alert(`${Fname}, Please check your mailbox. We sent you an Email with your verification code. 
          Email sent ${message} to: ${receiver}
          You might check your SPAM folder if it taking too long.`)
        }
        */
    });
});


// Hide bike from page while DB updates
function remove_bike(bike_id) {
    fetch('/remove_bike?q=' + bike_id);
    let item = '#' + bike_id
    $(item).fadeOut("slow");
    return;
}


// Hide bike from cart page while DB updates
function remove_bike_from_cart(bike_name, service) { 
  fetch('/remove_bike_cart?q=' + bike_name + '&q2=' + service);  
  let item = '#' + bike_name + "_" + service
  $(item).fadeOut("slow");
  return;
}









