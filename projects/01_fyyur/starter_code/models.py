import datetime
from xmlrpc.client import DateTime
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask import Flask

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

db = SQLAlchemy(app)

migrate=Migrate(app, db)

# shows = db.Table(
#   "shows",
#   db.Column("venue_id", db.ForeignKey('venues.id'), primary_key=True),
#   db.Column("artist_id", db.ForeignKey('artists.id'), primary_key=True),
#   db.Column("start_time", db.String)
# )

class Show(db.Model):
    __tablename__ = "shows"
    venue_id = db.Column(db.ForeignKey("venues.id"), primary_key=True)
    artist_id = db.Column(db.ForeignKey("artists.id"), primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

#https://www.gormanalysis.com/blog/many-to-many-relationships-in-fastapi/

class Venue(db.Model):
  __tablename__ = 'venues'
  __table_args__ = {'extend_existing': True} 

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website_link = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean, default=False)
  seeking_description = db.Column(db.String(120))
  shows =  db.relationship("Show", backref="artist")


class Artist(db.Model):
  __tablename__ = 'artists'
  __table_args__ = {'extend_existing': True} 

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website_link = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
  seeking_description = db.Column(db.String(120))
  shows =  db.relationship("Show", backref="venue")
