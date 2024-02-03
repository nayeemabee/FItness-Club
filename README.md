# Fitness-Club

Description :-
This project is a paid membership site built using Django and integrates with the Stripe dashboard using the Stripe library. Users can register, sign in, and subscribe to premium plans on a monthly or yearly basis. Additionally, users have the flexibility to cancel their membership, with access to the plan available until the plan's expiration.

Setup Steps :-
To use this project, follow these setup steps.

Clone the Project :-
git clone https://github.com/your-username/your-project.git

Generate Virtual Environment :-
python -m venv venv

Generate Requirements.txt :-
pip freeze > requirements.txt

Install Requirements :-
pip install -r requirements.txt

Migrate Database :-
python manage.py makemigrations,
python manage.py migrate

Load Initial Data :-
python manage.py loaddata plans.json

Run Development Server :-
python manage.py runserver


After Server is Running.
Once the server is up, follow these steps :-

Register :-
Open the browser and navigate to the registration page.
Provide necessary details to register yourself.

Sign In :-
After registration, sign in using your credentials.

Get a Premium Plan :-
Go to the "Get Premium" section.
Choose a plan (monthly or yearly) and make the payment.

Cancel Plan :-
To cancel your membership, go to the "Settings" section.
Click on "Cancel Membership."
