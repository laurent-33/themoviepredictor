"""
app.py by laurent
"""


print("zedz")
#import sqlalchemy
#print(sqlalchemy.__version__)
#engine = sqlalchemy.create_engine('mysql://predictor:predictor@localhost:3306/database/predictor', echo=True)

import mysql.connector
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import locale

locale.setlocale(locale.LC_ALL, locale='fr_FR')

r = requests.get("https://fr.wikipedia.org/wiki/Joker_(film,_2019)")
soup = BeautifulSoup(r.text, 'html.parser')

# récupérer élément html dont id = fiche technique
fiche = soup.find(id="Fiche_technique")

# remonter un niveau (parent) pour obtenir l'élément h2 (heading de niveau 2)
h2_tag = fiche.parent

# récupérer le sibling (frère) suivant ul (unordered list)
ul_tag = h2_tag.find_next_sibling("ul")

# récupérer les enfants li (list item)
li_tags = ul_tag.find_all("li", recursive=False)

# récupérer soit l'élément i (italic) ou a (normal)

for li_tag in li_tags:

    li_split = li_tag.text.split(sep=":")
    data_type = li_split[0].strip()
    data_value = li_split[1].strip()

    if data_type == "Titre original":
        title = data_value
        
    if data_type == "Durée":
        duration = data_value.replace("minutes", "").strip()
        
    if data_type == "Dates de sortie":
        release_dates_list = li_tag.find_all("li")
        for release_date_li in release_dates_list:
            release_date_splitted = release_date_li.text.split(sep=":")
            release_country = release_date_splitted[0].strip()
            release_date_as_string = release_date_splitted[1].strip() # 9 octobre 2019
            if release_country == "France":
                release_date_object = datetime.strptime(release_date_as_string, '%d %B %Y')
                release_date = datetime.strftime(release_date_object, '%Y-%m-%d')
                
    if data_type == "Classification":
        ratings_list = li_tag.find_all("li")
        for rating_li in ratings_list:
            rating_splitted = rating_li.text.split(sep=":")
            rating_country = rating_splitted[0].strip()
            rating_string = rating_splitted[1].strip() # Interdit aux moins de 12 ans avec avertissement
            if rating_country == "France":
                if rating_string.find("12") != -1:
                    rating = '-12'

print(title)
print(duration)
print(release_date)
print(rating)

exit()

# insérer un people dans database
"""
cnx = mysql.connector.connect(user='predictor', password='predictor',
                                                            host='127.0.0.1',
                                                            database='predictor')
cursor = cnx.cursor()

# visualiser données
query = ("SELECT id, title, release_date FROM movies ")

cursor.execute(query)

for (id, title, release_date) in cursor:
    print("{}, {} was released on {:%d %b %Y}".format(
        id, title, release_date))

# insérer people
add_people = ("INSERT INTO people"
                            "(firstname, lastname)"
                            "VALUES (%s, %s)")

data_people = ('Clint', 'Eastwood')

cursor.execute(add_people, data_people)

# visualiser modif
query = ("SELECT id, firstname, lastname FROM people")
cursor.execute(query)

for (id, firstname, lastname) in cursor:
    print("{}, {}, {}".format(id, firstname, lastname))

#cnx.commit()
#cnx.rollback()
cursor.close()
cnx.close()
"""

#import sys
# for arg in sys.argv:
#   print(arg)

parser = argparse.ArgumentParser(description='Process Movies Predictor data')
parser.add_argument('context', choices=['people', 'movies'], help='La table concernée, people ou movies')

fullaction = parser.add_subparsers(dest='action', help='fullaction',)

parser_find = fullaction.add_parser('find')
parser_find.add_argument('id', type=int)

parser_list = fullaction.add_parser('list')
parser_list.add_argument('--export', type=str)

import_parser = fullaction.add_parser('import', help='Add data from csv file')
import_parser.add_argument('--file' , help='File with data')

insert_parser = fullaction.add_parser('insert', help='Add data in tables')

known_args = parser.parse_known_args()[0]
print("test", known_args)

if known_args.context == "people":
    insert_parser.add_argument('--firstname' , help='Person first name', required=True)
    insert_parser.add_argument('--lastname' , help='Person last name', required=True)

if known_args.context == "movies":
    insert_parser.add_argument('--title' , help='Movie title', required=True)
    insert_parser.add_argument('--duration' , help='Movie duration')
    insert_parser.add_argument('--original-title' , help='Movie original title')
    insert_parser.add_argument('--origin-country' , default=None, help='Movie origin country')
    insert_parser.add_argument('--release-date', default=None , help='Movie release date')
    insert_parser.add_argument('--rating', default=None , help='Movie rating')

args = parser.parse_args()
print(args)

"""
Args example:
$ python app.py movies find 1
$ python app.py people list
$ python app.py people list --export "listing.csv"

$ python app.py people insert --firstname "John" --lastname "Doe"
$ python app.py movies insert --title "Star Wars, épisode VIII : Les Derniers Jedi" --duration 152
                              --original-title "Star Wars: Episode VIII – The Last Jedi" --origin-country US
                              --release-date

$ python app.py movies import --file new_movies.csv

"""

def connectToDatabase():
    return mysql.connector.connect(user='predictor', password='predictor',
                                                            host='127.0.0.1',
                                                            database='predictor')

def createCursor(cnx):
    return cnx.cursor(named_tuple=True)

def disconnectDatabase(cnx, cursor):
    cursor.close()
    cnx.close()

def findQuery(table, id):
    return f"SELECT * FROM {table} WHERE id={id}"

def find(table, id):
    cnx = connectToDatabase()
    cursor = createCursor(cnx)

    query = findQuery(table, id)
    cursor.execute(query)

    results = cursor.fetchall()
    disconnectDatabase(cnx, cursor)
    return results

def findall(table):
    cnx = connectToDatabase()
    cursor = createCursor(cnx)
    cursor.execute(f"SELECT * FROM {table}")
    results = cursor.fetchall()
    
    disconnectDatabase(cnx, cursor)
    return results

def insertPeople(firstname, lastname):
    cnx = connectToDatabase()
    cursor = createCursor(cnx)
    query = f"INSERT INTO `people` (`firstname`, `lastname`) VALUES ('{firstname}', '{lastname}')"
    cursor.execute(query)
    lastId = cursor.lastrowid
    cnx.commit()
    disconnectDatabase(cnx, cursor)
    return lastId

def insertMovie(title='', duration='', original_title='', origin_country='', release_date='', rating=''):
    cnx = connectToDatabase()
    cursor = createCursor(cnx)
    query = "INSERT INTO `movies` (`title`,`duration`,`original_title`,`release_date`,`rating`) VALUES (%s, %s, %s, %s, %s)"
    print(query)
    data = (title, duration, original_title, release_date, rating)
    print(data)
    cursor.execute(query, data)
    lastId = cursor.lastrowid
    cnx.commit()
    disconnectDatabase(cnx, cursor)
    return lastId

def printPerson(person):
    print(f"#{person.id}: {person.firstname} {person.lastname}")

def printMovie(movie):
    print(f"#{movie.id}: {movie.title} released on {movie.release_date}")


import csv

# Utiliser arguments pour afficher des inputs
if args.context == "people":
    print("Mode People")
    
    if args.action == "find":
        peopleId = args.id

        results = find("people", peopleId)
        for person in results:
            print(f"#{person.id}: {person.firstname} {person.lastname}")

    if args.action == "list":
        results = findall("people")

        if args.export:
            with open(args.export, 'w', newline='\n', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(results[0]._fields)
                for person in results:
                    writer.writerow(person)

        else:
            for person in results:
                printPerson(person)

    if args.action == "insert":
        results = insertPeople(
            firstname=args.firstname,
            lastname=args.lastname
            )
        print(results)

if args.context == "movies":
    print("Mode Movies")
    
    if args.action == "find":
        movieId = args.id

        results = find("movies", movieId)
        for movie in results:
            print("")
            print(movie)

    if args.action == "list":
        results = findall("movies")
        for movie in results:
            printMovie(movie)
        
        if args.export:
            with open(args.export, 'w', newline='\n', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(results[0]._fields)
                for movie in results:
                    writer.writerow(movie)

    if args.action == "insert":
        results = insertMovie(
            title=args.title,
            duration=args.duration,
            original_title=args.original_title,
            release_date=args.release_date,
            rating=args.rating
            )
        print(results)

    if args.action == "import":
        with open(args.file, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if reader.line_num == 1:
                    features_names = row
                
                else:
                    insertMovie(
                        title=row['title'],
                        original_title=row['original_title'],
                        duration=row['duration'],
                        rating=row['rating'],
                        release_date=row['release_date']
                        )
