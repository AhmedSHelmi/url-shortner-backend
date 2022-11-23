from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, verify_jwt_in_request, get_jwt_identity
from .helpers import generate_url
from urllib.parse import urlparse
from flask.ext.autodoc import Autodoc

app = Flask(__name__)
auto = Autodoc(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'jwt.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change on production
app.config['PROPAGATE_EXCEPTIONS'] = True


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)


# DB set up and seeders
@app.cli.command('db_create')
@auto.doc()
def db_create():
    db.create_all()
    print('Database created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped')


@app.cli.command('db_seed')
def db_seed():
    test_user = User(first_name='Stephen',
                     last_name='Hawking',
                     email='admin@admin.com',
                     password='admin')
    test_url = Url(
        url = "linkedin.com",
        shortend = "sadasd3324"
    )
    db.session.add(test_user)
    db.session.commit()
    
    db.session.add(test_url)
    db.session.commit()
    print('Database seeded')



@app.route('/<short>', methods=['GET'])
@auto.doc()
@jwt_required()
def index(short):
    print(short)
    #redirect to url
    site = Url.query.filter().filter_by(
        shortend=short).first().site
    print(site)
    return redirect(site, code=302)


# User routes
@app.route('/register', methods=['POST'])
@auto.doc()
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        response = jsonify(message='That email already exists'), 409
        return response
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name,
                    email=email, password=password)
        db.session.add(user)
        db.session.commit()
        response =  jsonify(message='User created successfully'), 201
        return response


@app.route('/login', methods=['GET'])
@auto.doc()
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        response = jsonify(message='Login Successful', access_token=access_token)
        return response
        
    else:
        return jsonify('Bad email or Password'), 401

# url Routes


@app.route('/api/links/create/', methods=['POST'])
def create_url():
    verify_jwt_in_request()
    identity = get_jwt_identity()
    # if user authorized save to db
    if identity:
        
        url_input = request.json['url']
        
        try:
            result = urlparse(url_input)
        except:
            return jsonify(message="Invalid URL!")
        
        user = User.query.filter().filter_by(
            email=identity).first()
        url = Url(url=generate_url(url_input), user=user)
        db.session.add(url)
        db.session.commit()
        response = jsonify(message="URL Was Saved to your list!")
        return response
    else:
        url = Url(url=generate_url(url_input), user=None)
        db.session.add(url)
        db.session.commit()
        response = jsonify(message=flask.request.host+"/"+generate_url(url_input))
        return response


@app.route('/api/links/', methods=['GET'])
@jwt_required()
def get_users_links():
    identity = get_jwt_identity()
    urls = [request.host+"/"+item.url for item in Url.query.filter(Url.user.has(email=identity)).all()]
    response =  jsonify(message=urls)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# Database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Url(db.Model):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    shortend = Column(String)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=True)
    user = db.relationship("User")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# DB Schemas


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class UrlSchema(ma.Schema):
    class Meta:
        fields = ('id', 'url', 'user_id')


# Marsh mellow db adds
user_schema = UserSchema()
users_schema = UserSchema(many=True)


if __name__ == '__main__':
    app.run()
