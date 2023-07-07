# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
import psycopg2
from flask import render_template, request, Response, flash, redirect, url_for, abort, jsonify
import logging
from logging import Formatter, FileHandler
from forms import *
from models import *
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

# TODO: connect to a local postgresql database
conn = psycopg2.connect(
    host="localhost",
    database="Fyyur",
    user="postgres",
    password="admin"
)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

    # Retrieve all venues from the database
    venues = Venue.query.all()

    # Create a list to store venue data
    data = []
    area_data = []

    for venue in venues:
        # Get the upcoming shows for the venue
        upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).all()

        if len(area_data) == 0:
            area_data.append({
                'city': venue.city,
                'state': venue.state,
                'num_upcoming_shows': len(upcoming_shows),
                'venues': [{
                    'id': venue.id,
                    'name': venue.name,
                    'image_link': venue.image_link
                }]
            })

        for area in area_data:
            if area['city'] == venue.city:
                for ven in area['venues']:
                    if ven['id'] != venue.id:
                        area['venues'].append({
                            'id': venue.id,
                            'name': venue.name,
                            'image_link': venue.image_link
                        })
            else:
                area_data.append({
                    'city': venue.city,
                    'state': venue.state,
                    'num_upcoming_shows': len(upcoming_shows),
                    'venues': [{
                        'id': venue.id,
                        'name': venue.name,
                        'image_link': venue.image_link
                    }]
                })
        

    data = area_data

    # Render the venues template with the venue data
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    response = {
        'count': len(venues),
        'data': [{
            'id': venue.id,
            'name': venue.name,
        } for venue in venues]
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    # Retrieve the venue from the database using the venue_id
    venue = Venue.query.get(venue_id)

    if venue is None:
        abort(404)  # Venue not found

    past_shows = Show.query.join(Venue).filter(Show.venue_id == venue.id, Show.start_time < datetime.now()).all()
    upcoming_shows = Show.query.join(Venue).filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).all()

    past_shows_data = []
    for show in past_shows:
        past_shows_data.append({
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    upcoming_shows_data = []
    for show in upcoming_shows:
        upcoming_shows_data.append({
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    response = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website_link': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows_data,
        'upcoming_shows': upcoming_shows_data,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    # Render the venue page with the venue data
    return render_template('pages/show_venue.html', venue=response)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try:
        form = VenueForm(request.form)

        # Create a new Venue object with the form data
        venue = Venue(
            name=form.name.data,
            genres=form.genres.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            website_link=form.website_link.data,
            facebook_link=form.facebook_link.data,
            seeking_talent=bool(form.seeking_talent.data),
            seeking_description=form.seeking_description.data,
            image_link=form.image_link.data
        )

        # Add the new venue to the database
        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + venue.name + ' was successfully listed!')
    except Exception as ex:
        # If an error occurs, rollback the session and show an error message
        db.session.rollback()

        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Venue ' +
              venue.name + ' could not be listed.')
    finally:
        # Close the session
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)  # Venue not found
    try:
        db.session.delete(venue)
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        abort(500)  # Internal server error

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database

    # Query the database to get all the artists
    artists = Artist.query.all()

    # Convert the list of artists to a list of dictionaries
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {
        'count': len(artists),
        'data': [{
            'id': artist.id,
            'name': artist.name,
        } for artist in artists]
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    # Retrieve the artist from the database using the artist_id
    artist = Artist.query.get(artist_id)

    if artist is None:
        abort(404)  # Artist not found

    past_shows = Show.query.join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time < datetime.now()).all()
    upcoming_shows = Show.query.join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time > datetime.now()).all()

    past_shows_data = []
    for show in past_shows:
        past_shows_data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    upcoming_shows_data = []
    for show in upcoming_shows:
        upcoming_shows_data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    response = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website_link': artist.website_link,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows_data,
        'upcoming_shows': upcoming_shows_data,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    form = ArtistForm()

    # TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)
    if artist is None:
        abort(404)  # Artist not found

    # Populate the form with fields from the artist
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website_link
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # Retrieve the artist from the database using the artist_id
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form)

    if artist is None:
        abort(404)  # Artist not found

    # Update the artist record with the new attributes from the form submission
    artist.name = form.name
    artist.genres = form.genres
    artist.city = form.city
    artist.state = form.state
    artist.phone = form.phone
    artist.website_link = form.website_link
    artist.facebook_link = form.facebook_link
    artist.seeking_venue = bool(form.seeking_venue)
    artist.seeking_description = form.seeking_description
    artist.image_link = form.image_link

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # Create an instance of the VenueForm
    form = VenueForm()

    # TODO: populate form with values from venue with ID <venue_id>
    # Retrieve the venue from the database using the venue_id
    venue = Venue.query.get(venue_id)

    if venue is None:
        abort(404)  # Venue not found

    # TODO: Populate the form with values from the venue
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website_link
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)  # Venue not found

    # Retrieve the values from the form submitted
    name = form.name.data
    genres = form.genres.data
    address = form.address.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    website_link = form.website_link.data
    facebook_link = form.facebook_link.data
    seeking_talent = bool(form.seeking_talent.data)
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data

    # Update the venue record with the new attributes
    venue.name = name
    venue.genres = genres
    venue.address = address
    venue.city = city
    venue.state = state
    venue.phone = phone
    venue.website_link = website_link
    venue.facebook_link = facebook_link
    venue.seeking_talent = seeking_talent
    venue.seeking_description = seeking_description
    venue.image_link = image_link

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try:
        form = ArtistForm(request.form)
        
        # Create a new Artist object with the form data
        new_artist = Artist(
            name=form.name.data,
            genres=form.genres.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            website_link=form.website_link.data,
            facebook_link=form.facebook_link.data,
            seeking_venue=bool(form.seeking_venue.data),
            seeking_description=form.seeking_description.data,
            image_link=form.image_link.data
        )

        # Add the new artist record to the database
        db.session.add(new_artist)
        db.session.commit()

        # Flash a success message
        flash('Artist ' + new_artist.name + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        # Handle any errors that occur during the database insertion
        db.session.rollback()
        flash('An error occurred. Artist ' +
              new_artist.name + ' could not be listed.')
    finally:
        # Close the database session
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    # Query the database to get the show information
    shows = Show.query \
        .join(Venue, Venue.id == Show.venue_id) \
        .join(Artist, Artist.id == Show.artist_id) \
        .all()

    # Convert the query result to the desired format
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    try:
        form = ShowForm(request.form)
    
        # Retrieve the form data
        artist_id = form.artist_id.data
        venue_id = form.venue_id.data
        start_time = form.start_time.data

        # Create a new Show record with the form data
        show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

        # on successful db insert, flash success
        # Add the new Show record to the database
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
