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



/*
// Send Verification Email with unique code
function sendMail(receiver, Fname, Lname){
  console.log("Sending");
  verCode = getRndInteger(1000,9999)
  Email.send({
    SecureToken : "5351027b-fe2d-49d4-ad43-29b37dde54b0",
    Host : "smtp.elasticemail.com",
    Username : "gbikes.customer.service@gmail.com",
    Password : "D360E0BFB939E840E5D18DB2BF786E980F77",
    To : receiver,
    From : "gbikes.customer.service@gmail.com",
    Subject : "Your 2-Step verification code just arrived",
    Body : `Hi ${Fname} ${Lname} and wellcome to the G-bikes service app.
    This is your unique 2-step verification code to use when Loging in @ https://final-project-dany.herokuapp.com/login - ${verCode}.`
  }).then(
    message => alert(`${Fname}, Please check your mailbox. We sent you an Email with your verification code. 
    Email sent ${message} to: ${receiver}
    You might check your SPAM folder if it taking too long.`)
  );
}

// Code generator
function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}
*/





