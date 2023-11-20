from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, url_for, redirect, jsonify, current_app, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, MultipleFileField, SubmitField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Optional, Length, EqualTo
from flask_wtf.csrf import CSRFProtect
from flask_login import UserMixin, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from flask_paginate import Pagination, get_page_parameter
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'd5fb8c4fa8bd46638dadc4e751e0d68d'
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('Image', backref='article', lazy=True, cascade="all, delete")

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'images': [image.filename for image in self.images]
        }

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CreateArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    images = MultipleFileField('Images', validators=[Optional()])
    submit = SubmitField('Create Article')

class UpdateArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    images = MultipleFileField('Images', validators=[Optional()])
    # Add a hidden field to store existing image filenames
    existing_images = HiddenField('Existing Images')
    submit = SubmitField('Update Article')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(),
        EqualTo('Confirm Password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is authenticated and has admin privileges
        if not current_user.is_authenticated or not current_user.is_admin:
            # Redirect to the unauthorized page or return an error response
           return render_template('403.html'), 404
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def save_image(image):
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)


        # Save the file in the specified folder
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Return the relative path for storage in the database
        return os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])

    return None

def create_article(title, content, images=None):
    article = Article(title=title, content=content)

    if images:
        for image in images:
            image_path = save_image(image)
            if image_path:
                new_image = Image(filename=image_path)
                article.images.append(new_image)

    db.session.add(article)
    db.session.commit()
    return article

def get_article(article_id):
    article = Article.query.filter_by(id=article_id).first()
    return article


def update_article(article_id, form):
    # Retrieve the article from the database
    article = Article.query.get(article_id)

    # Update the article's title and content
    article.title = form.title.data
    article.content = form.content.data

    # Handle image updates
    if form.images.data:

        # Save uploaded images
        for image_file in form.images.data:
            image_path = save_image(image_file)
            if image_path:
                new_image = Image(filename=image_path)
                article.images.append(new_image)

    # Commit the changes
    db.session.commit()

    # Flash a success message
    flash('Post updated successfully!')

    return article

def update_article_for_put(article_id, data):
    # Retrieve the article from the database
    article = Article.query.get(article_id)

    if article:
        # Update the article fields based on the data from the JSON payload
        if 'title' in data:
            article.title = data['title']

        if 'content' in data:
            article.content = data['content']

        # Handle image updates
        if 'images' in data:

            # Save new images
            for image_filename in data['images']:
                new_image = Image(filename=image_filename)
                article.images.append(new_image)

        # Commit the changes
        db.session.commit()

    else:
        # If the article does not exist, raise a ValueError
        raise ValueError(f"Article with ID {article_id} not found")

def delete_article(article_id):
    article = Article.query.get(article_id)

    if article:
        if article.images:
            for image in article.images:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass  # Ignore if

        db.session.delete(article)
        db.session.commit()
    else:
        raise ValueError(f"Article with ID {article_id} not found")



@app.route('/', methods=['GET'])
def list_articles():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.paginate(page=page, per_page=5)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(articles=[article.to_json() for article in articles])
    else:
        return render_template('articles.html', articles=articles)




@app.route('/create', methods=['GET','POST'])
@login_required
@admin_required
def create_article_route():
    form = CreateArticleForm()

    if form.validate_on_submit():
        # Process the form data and create the article
        title = form.title.data
        content = form.content.data
        images = form.images.data  # Assuming MultipleFileField is used

        create_article(title, content, images)


        # Redirect to a success page or wherever you want
        return redirect(url_for('list_articles'))

    return render_template('create_article.html', form=form)


@app.route('/update/<int:article_id>', methods=['GET', 'POST','PUT'])
@login_required
@admin_required
def update_article_route(article_id):
    article = Article.query.filter_by(id=article_id).first()
    form = UpdateArticleForm(obj=article)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            update_article(article_id, form)
            return redirect(url_for('list_articles'))
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

    if request.method == 'PUT':

        try:
            update_article_for_put(article_id, request.json)
            return jsonify({'message': 'Article updated successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

    return render_template('create_article.html', form=form)


@app.route('/delete/<article_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_article_route(article_id):
    try:
        print(article_id)
        delete_article(article_id)
        return jsonify({'message': 'Article deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete article: {str(e)}'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Check if passwords are equal
        if form.password.data != form.confirm_password.data:
            flash('Passwords must match', 'error')
            print(get_flashed_messages())
            return render_template('register.html', form=form)

        # Continue with registration
        user = User(username=form.username.data)
        user.set_password(form.password.data)

        # Save the user to the database
        db.session.add(user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Assuming you have a LoginForm defined

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('list_articles'))

        flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('list_articles'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404