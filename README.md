# Job Offer Python Web Scraper

Simple job offer web-scraping python app. Contenerized using docker-compose. uses Flask and MongoDB.

![image](https://github.com/andrzejfutrega/web_scraper/assets/137655147/fe2d5c89-5444-4847-83d5-f9e88ed589e3)

## Description
Application lets the user to enter keywords and location to list offers from multiple websites.<br/>
You can also check search history to compare the number of job offers between the searches.<br/><br/>
Creates three Docker containers for:

* Database
* Engine
* Interface
  
Uses asyncio to send asynchronous requests to the websites (you can easily add more in scraper_engine.py file). <br />
Parsing is done using BeautifulSoup. Uses multiprocessing to parse and extract info for effeciency. <br />
Lists basic info for each offer and a hyperlink to the website.

## Getting Started

### Prerequisites

* (Not required) [MongoDBCompass](https://www.mongodb.com/products/tools/compass) to easily monitor the database.
* (Required) [Docker Compose](https://docs.docker.com/compose/install/)

### Executing program

* Pull this repository with GIT or download a ZIP directly from this website.
* Open your terminal and navigate to "aplikacja" directory:
```
cd aplikacja
```
* Build the docker images defined in docker-compose.yml:
```
docker-compose build
```
You only need to use the build command if it's the first time starting the app or if you've made any changes.
* Start the application:
```
docker-compose up
```
* The application's logs will display in the terminal. Look for the hosting address of the app. It will look something like this:
```
flask_app-1  |  * Running on http://127.0.0.1:5000
```
Open the application in your web browser using the provided address. <br /><br />



* To close the application:
```
docker-compose down
```


