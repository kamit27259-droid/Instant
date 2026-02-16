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
    if 'user_id' not in session:
        return redirect('/login')
    user = User.query.get(session['user_id'])
    # Show posts from followed users or self
    following_ids = [f.following_id for f in user.following]
    following_ids.append(user.id)
    posts = Post.query.filter(Post.user_id.in_(following_ids)).order_by(Post.timestamp.desc()).all()
    # Show stories from followed users
    stories = Story.query.filter(Story.user_id.in_(following_ids)).all()
    return render_template('index.html', user=user, posts=posts, stories=stories)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Username already exists!"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/post', methods=['GET','POST'])
def post():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        content = request.form['content']
        image_file = request.files.get('image')
        video_file = request.files.get('video')
        image_filename = ""
        video_filename = ""
        if image_file:
            image_filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename))
        if video_file:
            video_filename = video_file.filename
            video_file.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], video_filename))
        new_post = Post(content=content, image=image_filename, video=video_filename, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        return redirect('/')
    return render_template('post.html')

@app.route('/story', methods=['GET','POST'])
def story():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        image_file = request.files.get('image')
        video_file = request.files.get('video')
        image_filename = ""
        video_filename = ""
        if image_file:
            image_filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename))
        if video_file:
            video_filename = video_file.filename
            video_file.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], video_filename))
        new_story = Story(image=image_filename, video=video_filename, user_id=session['user_id'])
        db.session.add(new_story)
        db.session.commit()
        return redirect('/')
    return render_template('story.html')

@app.route('/like/<int:post_id>')
def like(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    existing = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
    if not existing:
        new_like = Like(user_id=session['user_id'], post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
    return redirect('/')

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    content = request.form['comment']
    new_comment = Comment(content=content, user_id=session['user_id'], post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect('/')

@app.route('/follow/<int:user_id>')
def follow(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    existing = Follow.query.filter_by(follower_id=session['user_id'], following_id=user_id).first()
    if not existing:
        new_follow = Follow(follower_id=session['user_id'], following_id=user_id)
        db.session.add(new_follow)
        db.session.commit()
    return redirect(f'/profile/{user_id}')

@app.route('/unfollow/<int:user_id>')
def unfollow(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    existing = Follow.query.filter_by(follower_id=session['user_id'], following_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return redirect(f'/profile/{user_id}')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    current_user_id = session.get('user_id')
    is_following = Follow.query.filter_by(follower_id=current_user_id, following_id=user_id).first() is not None
    followers_count = user.followers.count()
    following_count = user.following.count()
    return render_template('profile.html', user=user, posts=posts, is_following=is_following,
                           followers_count=followers_count, following_count=following_count)

if __name__ == '__main__':
    # Ensure upload folders exist
    # (commented out if manually created)
    # os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
    # os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)

    # Create DB inside app context
    with app.app_context():
        db.create_all()

    # Run Flask
    import os

if __name__ == "_main_":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)