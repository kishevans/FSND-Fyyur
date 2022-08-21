#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from msilib import datasizemask
import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template,
  request, 
  Response, 
  flash, 
  redirect, 
  url_for)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from models import *
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

#Database connection created via the config.py file, migrations also enabled
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app,db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
#Separation of concers achieved by creating models in a different file
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


#  Venues
#  ----------------------------------------------------------------
#Get venues from database filtered by state and city, to display upcoming shows 
# compare start time and  cureent time
@app.route('/venues')
def venues():
  locals = []
  venues = Venue.query.all()

  places = Venue.query.distinct(Venue.city, Venue.state).all()

  for place in places:
      locals.append({
          'city': place.city,
          'state': place.state,
          'venues': [{
              'id': venue.id,
              'name': venue.name,
              'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
          } for venue in venues if
              venue.city == place.city and venue.state == place.state]
      })
  return render_template('pages/venues.html', areas=locals)
#Case insensitive searching achived by using ilike method
@app.route('/venues/search', methods=['POST'])
def search_venues():
  input = request.form.get('search_term','')
  search = "%{}%".format(input)
  output = Venue.query.filter(Venue.name.ilike(search)).all()
  responses = {
    "count":len(output),
    "data":output
  }
  
  return render_template('pages/search_venues.html', results=responses, 
                         search_term=request.form.get('search_term', ''))
#Query the database to obtain the id and match with the page id to obtain venue details
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)

  past_shows = []
  upcoming_shows = []

  for show in venue.shows:
      temp_show = {
          'artist_id': show.artist_id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
          past_shows.append(temp_show)
      else:
          upcoming_shows.append(temp_show)

  # object class to dict
  data = vars(venue)

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
    
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
#CREATE operation
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf':False})
  #Check form for errors if no errors are found add and commit data from the form 
  # to the database
  if form.validate():
    try:
      venue = Venue(
        name=form.name.data,
        genres=form.genres.data,
        address=form.address.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        website=form.website_link.data,
        facebook_link=form.facebook_link.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description =form.seeking_description.data,
        image_link=form.image_link.data
      )
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ValueError as e:
      #on unsuccessful db insert, flash an error instead.
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      print(e)  
    finally:
      db.session.close()
  else:
    error_message = []
    for field, err in form.errors.items():
        error_message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(error_message))
    return render_template('forms/new_venue.html', form=form)

  return render_template('pages/home.html')

#Delete Operation for venues with button in the view
@app.route('/venues/<venue_id>/delete', methods=['GET','DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter(Venue.id==venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
#Query database and render artists
@app.route('/artists')
def artists():
  datas=[]
  artists = Artist.query.all()
  for artist in artists:
    datas.append({
        'id': artist.id,
        'name': artist.name
    })
  return render_template('pages/artists.html', artists=datas)

#Case insensitive partial search from the database
@app.route('/artists/search', methods=['POST'])
def search_artists():
  input = request.form.get('search_term','')
  search = "%{}%".format(input)
  output = Artist.query.filter(Artist.name.ilike(search)).all()
  responses = {
    "count":len(output),
    "data":output
  }
  return render_template('pages/search_artists.html', results=responses, 
                         search_term=request.form.get('search_term', ''))

#Query the database to obtain the id and match with the page id to obtain artist details
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)

  past_shows = []
  upcoming_shows = []

  for show in artist.shows:
      temp_show = {
          'artist_id': show.artist_id,
          'artist_name': show.artist.name,
          'venue_image_link': show.venue.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
          past_shows.append(temp_show)
      else:
          upcoming_shows.append(temp_show)

  # object class to dict
  data = vars(artist)

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artiste = Artist.query.filter(Artist.id==artist_id).first()
  form = ArtistForm(obj=artiste)
  return render_template('forms/edit_artist.html', form=form, artist=artiste)

#UPDATE operation to change any field after prepopulation based on artist id
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  try: 
    artist = Artist.query.get(artist_id)
    artist = form.populate_obj(artist)
    db.session.commit()
  except: 
    db.session.rollback()
  finally: 
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter(Venue.id==venue_id).first()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

#UPDATE operation to change any field after prepopulation based on venue id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  try: 
    venue = Venue.query.get(venue_id)
    venue = form.populate_obj(venue)
    db.session.commit()
  except: 
    db.session.rollback()
  finally: 
    db.session.close()
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  try: 
    artist = Artist()
    form.populate_obj(artist)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except: 
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally: 
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  datas=[]
  shows = db.session.query(Show).join(Venue).join(Artist).all()
  for show in shows:
    datas.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_id': show.artist_id,
        'artist_name':show.artist.name,
        'artist_image_link':show.artist.image_link,
        'start_time': str(show.start_time)
    })
  return render_template('pages/shows.html', shows=datas)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

#CREATE operation to add shows to the database 
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try: 
    show = Show()
    form.populate_obj(show)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except: 
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally: 
    db.session.close()
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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
