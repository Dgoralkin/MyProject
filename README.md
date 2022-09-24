# Workshop Service book for B-bike

## Video Demo:  [Link to YouTube demo](https://video.com/)

### Link to App:  This site stored on [Heroku](https://final-project-dany.herokuapp.com/)

#### Description

Workshop Service book is an end user web application available for use on the web on large screen or mobile device.
The main idea of the app is to replace the "Service writer" role in any bike shop service workshop.
The main idea (use flow) of the app:

1. Prevent users to use the app if not logged-in to the app database. Although some basic service info displayed through Iframe in main page.
2. Allow user to get registered to app's database and edit it's credentials later in "Account" page. The app sends custom One time generated password to users Email to verify users Email.
3. Forces user to add some bikes to their user ticket if it their first login time and allows to add or remove bikes later through "Get service page".
4. Allow user to pick and book multi services for each their bike on the "Get service" page.
5. Summarizes and displays end service time for each bike and specific + total service costs on the cart page.
6. Displays logged user live service status for every bike and service for that user with a EET timer on the "Pick up" page. As bike fully ready the app sends an Email notification to the user to inform him that his particular bike is ready for pick up.
7. On the "Pick up" page logged user can choose what bike or bikes to pick from service and redirects user for payment.
8. "Payment page" displays chosen pickup bikes and user info and verifies user's credit-card number that is valid. As paid, the app stores fully finished services per user in the service history database in MySql and displays that history on the "Pick up" page.

The Dir contains two Python files, app.py and helpers.py. The "app.py" controls app's traffic and usage flow. "helpers.py", contains most calculation functions.
"Workshop Service book" can handle multi users at once and keep track of the service orders in specific workshop considering it's adjustable working hours (Example: from 9am to 21pm) and scheduled prior services. It reads all workshop's offered services from an attached csv "Services" file that could be edited in Excel by the app owner. In that file service name, service cost and service time should be defined by the workshop owner.
Another helpful CSV file is the "Bikes" list, it contains a list of all bike brands witch being updated dynamically to and from the app. Every time app is being loaded it compares the amount of bikes in that file VS the app's MySql database. If new bikes were added in the app by the end user or in the csv file by the owner it being repopulated in both locations. *Because Heroku's disability to write to an external file, writing to a csv file disabled in the code and could be easily switched on.
Workshop Service book is connected to a MySql database to handle and keep track of the service order in the workshop. The app recalculating and displaying the correct time and date for a workshop's location considering (IL) time zone (+3 GMT).
The Dir folder contains two subfolders, "static" and "templates". "static" folder contains all page HTML templates as well as "static" folder contains the JavaScript, CSS and graphic files.
The app connected to MySQL database. It can fully establish required tables in the connected MySQL’s database if does not exist on the first run cycle. From there on it stores and manages all required app's information through six different tables:

1. users table: stores user info.
2. bikes table: stores bikes per user information.
3. all_bikes table: keep track of all existing bike models.
4. services table: keep track of all existing available workshop services offered by owner.
5. service_order table: manages all "in progress" services by user.
6. orders_histors table: stores info of past finished services, user's service history.
