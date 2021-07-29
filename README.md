# BookShelf
## Description
 It is a book review website built using Flask where the user can search for over 5000 books, provide reviews and view reviews from other users.\
 Note: The site uses book data from [goodreads.com](https://www.goodreads.com/) by via an API.
 
 This website is made for Project 1 of Harvard's CS50w: [Web Programming with Python and JavaScript course](https://learning.edx.org/course/course-v1:HarvardX+CS50W+Web/home)
 
 ## Technologies
 Project is created with:
 * Flask version: 1.1.2
 * Python version: 3.9.1
 * HTML5
 * CSS 3
 * Bootstrap 4
 * SQLAlchemy 
 * Javascript
 * Jinja 2
 
 Visit the [Youtube link](https://www.youtube.com/watch?v=V8valiqV7kY) for website walkthrough video
 
 ## Features
 * Gives recommendations based on the top 10 highest rated books
 * Search feature to find a book based on its title/author name/ISBN from a list of over 5000 books
 * User can view ratings and reviews provided by other readers for any book
 * Users can rate the book on a scale of 1 to 5. They can also post reviews for the book
 * A personalized profile section to keep a record of previously rated books
 
 ## Setup
 After cloning the repository, run the following commands
 ```
$ pip install -r requirements.txt
$ export FLASK_APP=application.py
$ export FLASK_DEBUG=1
$ export DATABASE_URL=postgresql://dlkkgmphzhihlp:18331f4277b582ca38f7846105023305f7c380188af46a8e7081d6786bd58319@ec2-52-207-25-133.compute-1.amazonaws.com:5432/dan942feio1fe6
$ flask run
 ```
