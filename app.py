from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER_IMAGES'] = 'static/uploads/images'
app.config['UPLOAD_FOLDER_VIDEOS'] = 'static/uploads/videos'
db = SQLAlchemy(app)

# ----------------- Database Models -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    stories = db.relationship('Story', backref='author', lazy=True)

    # followers = people who follow this user
    followers = db.relationship('Follow', foreign_keys='Follow.following_id',
                                backref='followed_user', lazy='dynamic')
    # following = people this user follows
    following = db.relationship('Follow', foreign_keys='Follow.follower_id',
                                backref='follower_user', lazy='dynamic')
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    image = db.Column(db.String(100))
    video = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100))
    video = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ----------------- Routes -----------------
@app.route('/')
def index():
    return "Working"

with app.app_context():
    db.create_all()
