This is a fastapi service created to query train information stored in a postgresql db. 

The app is containerised with a local Postgres DB of your choice and a pytest module that will run tests on the api using test.py everytime the docker container is created.

You may want to create a virtual env, you can do so using the venv library in python:
python3 -m venv path/to/venv
source path/to/venv/bin/activate (macOS) OR path\to\venv\Scripts\activate (Windows)

Please define your own .env file with the following entries:
POSTGRES_DB=your-db-name
POSTGRES_USER=your-role-to-access-db
POSTGRES_PASSWORD=your-role-password-to-access-db
POSTGRES_HOST=5432 (by default)

Data for the train information are stored in a table with columns:
- id SERIAL NOT NULL
- train_date DATE NOT NULL
- platform INTEGER NOT NULL
- start_point VARCHAR(10) NOT NULL
- end_point VARCHAR(10) NOT NULL
- arrival_time TIME NOT NULL (ADD CONSTRAINT CHECK (arrival_time BETWEEN '00:00:00' AND '23:59:59'))
- departure_time TIME NOT NULL (ADD CONSTRAINT CHECK (arrival_time BETWEEN '00:00:00' AND '23:59:59'))

Some sample data are attached in the "sample_data.csv" file.

To run the container, do 
"docker-compose up --build", server is hosted on port 8000.

Valid query paths are 
GET ("/trains") - retrieve all train information from the db
GET ("/trains/id/{id}") - retrieve train with a specific id
GET ("/trains/end_point/{end_point}) - retrieve trains with a specific end_point
GET ("/trains/platform/{platform}) - retrieve trains that passed through a specific platfrom
POST ("/trains) - add a row of train data
PUT ("/trains/id/{id}) - update train data based on id
DELETE ("/trains/id/{id}) - delete train data based on id







