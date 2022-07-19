// Validate password and send verification Email 

$(document).ready(function(){
    $("#Sub1").click(function(){
        if ($("#password").val() != $("#password2").val()){
            alert("Passwords does not match");
        }
        else if ($("#password").val() == $("#password2").val()){
          sendMail()
          alert("Please check your mailbox. We sent you an Email with verification code.");
        }
    });
});


// Send Verification Email with unique code

function sendMail(){
  console.log("Sending");
  verCode = getRndInteger(1000,9999)
  Email.send({
    SecureToken : "5351027b-fe2d-49d4-ad43-29b37dde54b0",
    Host : "smtp.elasticemail.com",
    Username : "gbikes.customer.service@gmail.com",
    Password : "D360E0BFB939E840E5D18DB2BF786E980F77",
    To : 'Goralkin@gmail.com',
    From : "gbikes.customer.service@gmail.com",
    Subject : "We are just testing the mailbox",
    Body : `This is your unique code to use on Login: ${verCode} .`
  }).then(
    message => alert(message)
  );
  console.log("Email sent", verCode);
}

// Code generator

function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}


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



