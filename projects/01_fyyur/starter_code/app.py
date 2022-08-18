#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import datetime
from random import randint
from sqlite3 import Date
from tokenize import String
from unicodedata import name
from xmlrpc.client import DateTime
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for


import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os

from models import app, Show, Venue, Artist, db
import sqlalchemy.types as types;

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

  #NOTE: This was the most FRUSTRATING error I have ever encountered
  #      Show.start_time > datetime.now() when used in filter for a join gives the error: "No operator matches the given name and argument types. You might need to add explicit type casts."
  #      casting it to ANYTHING would lead to this error: "Parser must be a string or character stream, not InstrumentedAttribute" it seems that Show.start_time is an InstrumentedAttribute. 
  #      I have searched far and wide for any information on why this is the case, but to no avail on finding an actual solution. 
  #      I have spoken with session leads for some help and there seems to be no final solution.
  #      Therefore any attempts to use a JOIN query involving filtering with Show.start_time are impossible. 
  #      I still used join queries, however it was limited.

  #JOIN queries:
  # upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time > datetime.now()).all();
  # upcoming_shows = []
  # for show in upcoming_shows_query:
  #   upcoming_shows.append(show)

  # past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time <= date).all()   
  # past_shows = []
  # for show in past_shows_query:
  #   past_shows.append(show)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all();
  
  cities = []
  city_venues = {}
  
  #Loops through the venues and adds them to the 'cities' list if the city is NOT already in the list
  for venue in venues:
    if len(cities) == 0:
      cities.append({"city": venue.city, "state": venue.state, "venues": []})
    elif not any(city["city"] == venue.city for city in cities):
      cities.append({"city": venue.city, "state": venue.state, "venues": []})

  #Loops through cities and venues and adds the corresponding ones to 'city_venues' as well as counts the shows according to the venues
  for city in cities:
    for venue in venues:
      num_upcoming_shows = 0;
      if venue.city == city["city"]:
        
        shows = Show.query.filter_by(venue_id = venue.id )
        for show in shows:

          #https://dateutil.readthedocs.io/en/stable/parser.html
          time = dateutil.parser.parse(show.start_time) 
          if time > datetime.now():
            num_upcoming_shows += 1

        city_venues = {"id": venue.id, "name": venue.name, "num_upcoming_shows": num_upcoming_shows};
        city["venues"].append(city_venues);
            
  return render_template('pages/venues.html', areas=cities);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term') 

  # Loops thorugh venues to list and then corresponding shows to find corresponding upcoming shows. 
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all();
  data = []
  num_upcoming_shows = 0;

  for venue in venues:
    num_upcoming_shows = 0;
    shows = Show.query.filter_by(venue_id = venue.id ).all()

    for show in shows:
      
      time = dateutil.parser.parse(show.start_time)
      
      if time > datetime.now():
        num_upcoming_shows += 1

    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows,
    })

  response={
    "count": len(data),
    "data": data,
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue_data = []
  upcoming_shows = []
  past_shows = []
  genres = []

  venue = Venue.query.filter_by(id = venue_id).first()

  venue_shows_query = db.session.query(Show.artist_id, Show.start_time, Show.venue_id, Artist.name, Artist.image_link).join(Artist).join(Venue).filter(Show.venue_id == venue.id).all();

  for show in venue_shows_query:
    if dateutil.parser.parse(show.start_time) > datetime.now():
      upcoming_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.name,
          "artist_image_link": show.image_link,
          "start_time": show.start_time
      })
    else:
      past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.name,
          "artist_image_link": show.image_link,
          "start_time": show.start_time
      })

  if venue.genres != None:
    #https://www.w3schools.com/python/ref_string_maketrans.asp
    trans = (venue.genres).maketrans({ "{" : "", "}" : ""})
    genres = (venue.genres).translate(trans).split(",")

  venue_data.append({
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  })


  data = list(filter(lambda d: d['id'] == venue_id, venue_data))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    name = request.form['name']
    city = request.form.get('city')
    state = request.form.get('state')
    address= request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website_link= request.form.get('website_link')

    if request.form.get('seeking_talent') == 'y':
      seeking_talent= True
    else: 
      seeking_talent = False

    seeking_description = request.form.get('seeking_description')

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link,
    website_link=website_link, seeking_talent=seeking_talent, seeking_description = seeking_description)
    
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  finally:
    db.session.close();

  #http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id = venue_id).delete();
    db.session.commit();
    flash('Venue ' + Venue.query.filter_by(id = venue_id).first().name + ' was successfully deleted!')
  except:
    # db.session.rollback()
    flash('An error occurred. Venue ' + Venue.query.filter_by(id = venue_id).first().name + ' could not be deleted.')
  finally:
    # db.session.close();
    None
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data =[]
  artists = Artist.query.all();

  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term') 

  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all();
  data = []
  num_upcoming_shows = 0;

  # Loops through found artists in order to loop through corresponding shows in order to determine how many upcoming shows they have
  for artist in artists:
    num_upcoming_shows = 0;
    shows = Show.query.filter_by(artist_id = artist.id ).all()

    for show in shows:
      
      time = dateutil.parser.parse(show.start_time)
      
      if time > datetime.now():
        num_upcoming_shows += 1

    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
    })

  response={
    "count": len(data),
    "data": data,
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist_data = []
  upcoming_shows = []
  past_shows = []
  genres = []

  artist = Artist.query.filter_by(id = artist_id).first();

  artist_shows_query = db.session.query(Show.artist_id, Show.start_time, Show.venue_id, Venue.city, Venue.name, Venue.image_link).join(Venue).join(Artist).filter(Show.artist_id == artist.id).all();

  for show in artist_shows_query:
    if dateutil.parser.parse(show.start_time) > datetime.now():
      upcoming_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.name,
          "venue_image_link": show.image_link,
          "start_time": show.start_time
      })
    else:
      past_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.name,
          "venue_image_link": show.image_link,
          "start_time": show.start_time
      })


  if artist.genres != None:
  #https://www.w3schools.com/python/ref_string_maketrans.asp
    trans = (artist.genres).maketrans({ "{" : "", "}" : ""})
    genres = (artist.genres).translate(trans).split(",")

  artist_data.append({
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
    })

  data = list(filter(lambda d: d['id'] == artist_id, artist_data))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
# LABEL: ARTISTS
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id = artist_id).first();
  form = ArtistForm()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.filter_by(id = artist_id).first();

    artist.name=request.form.get('name'), 
    artist.city=request.form.get('city'), 
    artist.state=request.form.get('state'), 
    artist.phone=request.form.get('phone'), 
    artist.genres=request.form.get('genres'), 
    artist.facebook_link=request.form.get('facebook_link'),
    artist.image_link=request.form.get('image_link'),
    artist.website_link=request.form.get('website_link'), 
    artist.seeking_description = request.form.get('seeking_description')
    if request.form.get('seeking_venue') == 'y':
      artist.seeking_venue= True
    else: 
      artist.seeking_venue = False

    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully changed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be changed.')
    print('Adding failed')
  finally:
    db.session.close();
  return redirect(url_for('show_artist', artist_id=artist_id))


#LABEL: Venues
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id = venue_id).first();
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.filter_by(id = venue_id).first();

    venue.name=request.form.get('name'), 
    venue.city=request.form.get('city'), 
    venue.state=request.form.get('state'), 
    venue.phone=request.form.get('phone'), 
    venue.genres=request.form.get('genres'), 
    venue.facebook_link=request.form.get('facebook_link'),
    venue.image_link=request.form.get('image_link'),
    venue.website_link=request.form.get('website_link'), 
    venue.seeking_description = request.form.get('seeking_description')
    if request.form.get('seeking_talent') == 'y':
      venue.seeking_talent= True
    else: 
      venue.seeking_talent = False

    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully changed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be changed.')
  finally:
    db.session.close();
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    name = request.form['name']
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website_link= request.form.get('website_link')

    if request.form.get('seeking_venue') == 'y':
      seeking_venue= True
    else: 
      seeking_venue = False

    seeking_description = request.form.get('seeking_description')

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link,
    website_link=website_link, seeking_venue=seeking_venue, seeking_description = seeking_description)

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  finally:
    db.session.close();

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data=[]

  shows_query = db.session.query(Show.artist_id, Show.start_time, Show.venue_id, Venue.name, Artist.image_link, Artist.name).join(Artist).join(Venue).all();

  for show in shows_query:
    data.append({
        "venue_id": show.venue_id,
        "venue_name": show[3],
        "artist_id": show.artist_id,
        "artist_name": show[5],
        "artist_image_link": show.image_link,
        "start_time": show.start_time
    })
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:

    artistId = request.form.get('artist_id');
    venueId = request.form.get('venue_id');
    startTime = str(request.form.get('start_time'));

    show = Show(artist_id = artistId,venue_id = venueId,start_time= startTime)
    db.session.add(show)
    db.session.commit();
    flash('Show was successfully listed!');
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close();
  return render_template('pages/home.html')
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)