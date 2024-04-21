# Workshop Service book for G-bikes

## Video to Demo: (https://www.youtube.com/watch?v=_b9vFSvlR_8)

### Link to App:  This site is stored on [Heroku](https://final-project-dany.herokuapp.com/)

#### Description

Workshop Service book is an end-user web application available for use on the web on a large screen or mobile device.
The main idea of the app is to replace the "Service writer" role in any bike shop service workshop.
The main features (use flow) of the app:

Workshop Service book is an end-user web application available for use on the web on a large screen or mobile device.
The main idea of the app is to replace the "Service writer" role in any bike shop service workshop.
The main features (use flow) of the app:

1. Prevent users to use the app if not logged-in to the app database. Although some basic service info displayed through Iframe in main page.
2. Allow the users to get registered to the app's database and edit their credentials later on the "Account" page. The app sends a custom One-time generated password to the user's Email to verify that the Email is valid.
3. Forces users to add some bikes to their user ticket if it is their first login time and allows them to add or remove bikes later through the "Get service page".
4. Allow user to pick and book multi-services for each of their bikes on the "Get service" page.
5. Summarize and display the end service time for each bike and specific + total service costs on the "cart" page.
6. Displays logged user live service status for every bike and service for that user with an EET timer on the "Pick up" page. As the bike is fully ready, the app sends an Email notification to the user to inform him that his particular bike is ready for pickup.
7. On the "Pick up" page logged user can choose what bike or bikes to pick from service and redirects user for payment.
8. The "Payment page" displays chosen pickup bikes and user info and verifies that the user's credit card number is valid. As paid, the app stores fully finished services per user in the service history database in MySql and displays that history on the "Pick up" page.

The main Dir contains two Python files, app.py and helpers.py. The "app.py" controls app's traffic and usage flow. "helpers.py", contains most calculation functions.
"Workshop Service book" can handle multi users at once and keep track of the service orders in specific workshop considering it's adjustable working hours (Example: from 9am to 21pm) and scheduled prior services. It reads all workshop's offered services from an attached csv "Services" file that could be edited in Excel by the app owner. In that file service name, service cost and service time should be defined by the workshop owner.
Another helpful CSV file is the "Bikes" list; it contains a list of all bike brands that are updated dynamically to and from the app. Every time the app is loaded, it compares the number of bikes in that file versus the app's MySql database if new bikes were added to the app by the end-user or in the CSV file by the owner. It is being repopulated in both locations. *Because of Heroku's disability to write to an external file, writing to a CSV file is disabled in the code and could be easily switched on.
The Workshop Service book is connected to a MySql database to handle and keep track of the service orders in the workshop. The app recalculates and displays the correct time and date for a workshop's location, considering the (IL) time zone (+3 GMT).
The main Dir folder contains two subfolders, "static" and "templates". "static" folder contains all page HTML templates as well as "static" folder contains the JavaScript, CSS and graphic files.
The app is connected to the MySQL database. It can fully establish required tables in the connected MySQL database if they do not exist during the first run cycle. From there on, it stores and manages all required app information through six different tables:

1. The user table stores user info.
2. bikes table: stores bikes per user information.
3. all_bikes table: keep track of all existing bike models.
4. services table: keep track of all existing available workshop services offered by the owner.
5. service_order table: manages all "in progress" services by the user.
6. orders_histors table: stores info of past finished services and user's service history.
