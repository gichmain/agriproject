from flask import render_template,redirect,Flask,flash,url_for,session,request
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import SubmitField,StringField,PasswordField, BooleanField
from wtforms.validators import required, DataRequired
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from datetime import datetime
from flask.ext.moment import Moment
import time
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from twilio.rest import TwilioRestClient
from flask_login import LoginManager, login_required,login_user
import datetime
from flask_login import UserMixin
#from sms import sendmessage

app= Flask("__name__")
app.config['SECRET_KEY']="hard to guess string"
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:gichmain@localhost/finalproject'
db=SQLAlchemy(app)
#manager=Manager(app)
moment = Moment(app)
bootstrap=Bootstrap(app)
admin = Admin(app, name = 'extend', template_mode= 'bootstrap3')

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "logingin"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
	return User.query.get(int(userid))



class LoginForm(Form):
	username = StringField("username/emailadddress", validators = [DataRequired()])
	password = PasswordField("your password",validators = [DataRequired()])
	remember_me = BooleanField('Keep me loged in')
	submit = SubmitField("submit")

class QueryForm(Form):
	thequery = StringField("please enter comma separated symptoms")
	enter = SubmitField("send query")

class SendMessageForm(Form):
	message = StringField("Please enter your short message here:")
	recipients = StringField("Please enter recipients(farmer/officer):")
	submitmessage = SubmitField("SendMessage")

class IssueForm(Form):
	issue = StringField("Please raise any issue or suggest improvements:")
	submit = SubmitField("send suggestion")

class Issue(db.Model):
	__tablename__ = "Issue"

	id = db.Column(db.Integer, primary_key = True)
	issue = db.Column(db.String(560))
	time = db.Column(db.DateTime, default = datetime.datetime.now())

	def __init__(self,issue):
		self.issue = issue


class  User(db.Model,UserMixin):
	__tablename__="User"

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128),index = True)
	email_username = db.Column(db.String(64),unique=True, index=True)
	password = db.Column(db.String(64))
	location = db.Column(db.String(64), index = True)
	occupation = db.Column(db.String(64))
	phone_number = db.Column(db.String(64),unique=True, index=True)

	#def __init__(self,name,email,location,occupation, phone_number, password):
	#	self.name=name
	#	self.email_username=email
	#	self.location=location
	#	self.occupation=occupation
	#	self.phone_number = phone_number 
	#	self.password = password

class Message(db.Model):
	__tablename__ = "Message"

	id=db.Column(db.Integer,primary_key=True)
	message_text=db.Column(db.String(400))
	time_sent=db.Column(db.DateTime,default=datetime.datetime.now())

	def __init__(self,text):
		self.message_text=text

class Query(db.Model):
	__tablename__="Query"

	id=db. Column(db.Integer,primary_key=True)
	text=db.Column(db.String(400))
	sender_id=db.Column(db.Integer,db.ForeignKey("User.id"))
	time_sent=db.Column(db.DateTime,default = datetime.datetime.now())
	#sender=db.relationship('User', backref=db.backref('author', lazy='dynamic'))

	def __init__(self,text,sender):
		self.text=text
		self.sender=session["id"]

	
class Diseases(db.Model):
	__tablename__ = 'Diseases'

	id=db. Column(db.Integer,primary_key=True)
	disease_name = db.Column(db.String(64))
	disease_symptoms = db.Column(db.String(700))
	disease_cure = db.Column(db.String(6000))

	def symptoms(self):
		mysymptoms=list(self.disease_symptoms.split(','))
		#print mysymptoms
		return mysymptoms

	def cure(self):
		mycure=list(self.disease_cure.split(','))
		return mycure

	#def __init__(self, disease_name, cure, *symptoms):
	#	self.disease_name = disease_name
	#	self.disease_symptoms = str(symptoms)
	#	self.disease_cure = cure

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Query, db.session))
admin.add_view(ModelView(Diseases, db.session))
admin.add_view(ModelView(Issue, db.session))
admin.add_view(ModelView(Message, db.session))

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'),500

@app.route('/home/')
def gohome():
	return render_template("home.html")

@app.route('/')
def hometwo():
	return render_template("home.html")


@app.route('/login/',methods=['GET','PoST'])
def logingin():
    form= LoginForm()
    if request.method=='POST':
        session["username"]=form.username.data
        session["password"]=form.password.data
        #flash("bwahaha")
        user=User.query.filter_by(email_username=session.get("username")).first()
        if user == None:
        	flash("Incorrect username!!")
        else:
        	if session.get('password') == user.password:
        		flash("logged in")
        		session["id"] = user.id
        		session['occupation'] = user.occupation
        		session['name'] = user.name
        		login_user(user)
        		return redirect(request.args.get('next') or url_for('gohome'))

        	else:
        		flash("wrong password")
        		return render_template("login.html",form = form)
    return render_template("login.html",form=form)

@app.route('/home/diagnose',methods=['GET','PoST'])
def diagnose():
	form = QueryForm()

	if request.method == 'POST':
		searchterm = form.thequery.data
		disease = Diseases.query.filter_by(disease_name = searchterm).first()
		#print disease.symptoms()
		if disease == None:
			flash("NO RESULT: Check the spelling and try again...")
			thisquery = Query(searchterm)
			db.session.add(thisquery)
			db.session.commit()
		else:
			thisquery = Query(searchterm, None)
			db.session.add(thisquery)
			db.session.commit()
			return render_template('results.html', disease = disease)
	return render_template("diagnose.html", form = form)

@app.route('/home/sendmessage', methods = ['GET','POST'])
@login_required
def send_message():
	form = SendMessageForm()

	if request.method == 'POST':
		message = form.message.data
		target = form.recipients.data
		recipients = User.query.filter_by(occupation = target).all()
		thismessage = Message(message)
		db.session.add(thismessage)
		db.session.commit()
		for person in recipients:
			phonenumber = person.phone_number
			#sendmessage(phonenumber,message)
	return render_template("sendmessage.html",form = form)

@app.route('/home/reportissue', methods = ['POST','GET'])
def issue():
	form = IssueForm()
	if request.method == 'POST':
		myissue = form.issue.data
		postit = Issue(myissue)
		db.session.add(postit)
		db.session.commit()
		flash("suggestion sent")
		return render_template("home.html")

	return render_template("issue.html", form = form)

@app.route('/127.0.0.1:5000/admin')
@login_required
def admininterface():
	return redirect("/127.0.0.1:5000/admin")



if __name__ == '__main__':
	app.run(debug=True)

#string.split("d") ->splits a string with d as delimiter
#pg 130 Alerts/thumbnails
#pg 124 jumbotron