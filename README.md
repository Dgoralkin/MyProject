# Workshop Service book for B-bike

## Video Demo:  [Link to YouTube demo](https://video.com/)

### Link to App:  This site stored on [Heroku](https://final-project-dany.herokuapp.com/)

#### Description

Workshop Service book is an end user web application available for use on the web on large screen or mobile device.
The main idea of the app is to replace the "Service writer" role in any bike shop service workshop.
The main idea (use flow) of the app:

1. Prevent users to use the app if not logged-in to the app dtatbase. Although some basic service info dispalyed through Iframe in main page.
2. Allow user to get registered to app's database and edit it's credentials later in "Account" page. The app sends custom One time generated password to users Email to verify users Email.
3. Forces user to add some bikes to their user ticket if it their first login time and allows to add or remove bikes later through "Get service page".
4. Allow user to pick and book multi services for each their bike on the "Get service" page.
5. Summarizes and displays end service time for each bike and specific + total service costs on the cart page.
6. Displays logged user live service status for every bike and service for that user with a EET timer on the "Pick up" page. As bike fully ready the app sends an Email notification to the user to inform him that his particular bike is ready for pick up.
7. On the "Pick up" page logged user can choose what bike or bikes to pick from service and redirects user for payment.
8. "Payment page" displays choosed pickup bikes and user info and verifies user's credit-card number that is valid. As paied, the app stores fully finished services per user in the service history database in MySql and displays that history on the "Pick up" page.

The dir contains two Python files, app.py and helpers.py. The "app.py" controls app's trafic and usage flow. "helpers.py", contains most calculation functions.
"Workshop Service book" can handle multi users at once and keep track of the service orders in specific workshop considering it's udjastable working hours (Example: from 9am to 21pm) and sheduled prior services. It reads all workshop's offered services from an attached csv "Services" file that could be edited in Excell by the app owner. In that file service name, service cost and service time should be defined by the workhop owner.
Another helpfull CSV file is the "Bikes" list, it cotnains a list of all bike brands witch being updated dinamically to and from the app. Every time app is being lodaed it compares the amount of bikes in that file VS the app's MySql database. If new bikes were added in the app by the end user or in the csv file by the owner it being repopulated in both locations. *Because Heroku's disability to write to an external file, writing to a csv file disabled in the code and could be easily switched on.
Workshop Service book is connected to a MySql database to handle and keep track of the service order in the workshop. The app recalculating and displaying the correct time and date for a workshop's location considering (IL) time zone (+3 GMT).
The dir folder contains two subfolders, "static" and "templates". "static" folder contains all page HTML templates as well as "static" folder contains the JavaScript, Css and grafic files.
The app connected to MySql database. It can fully establish required tables in the connected MySql's database if doe's not exist on the first run cycle. From there on it stores and manages all required app's information through six different tables:

1. users table: stores user info.
2. bikes table: stores bikes per user information.
3. all_bikes table: keep track of all existing bike modells.
4. services table: keep track of all existing available workshop services offered by owner.
5. service_order table: manages all "in progress" services by user.
6. orders_histors table: stores info of past finished services, user's service history.
