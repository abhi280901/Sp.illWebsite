from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)

# create the database interface
db = SQLAlchemy()

class Household(db.Model):
    __tablename__ = 'hhold'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    code = db.Column(db.Text())
    def __init__(self, name):
        self.name=name


class Bills(db.Model):
    __tablename__='bills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    total = db.Column(db.Integer())
    creator_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    deadline = db.Column(db.Date())
    image = db.Column(db.LargeBinary) 
    status = db.Column(db.Integer())#0 - pending/1 - settled
    def __init__(self, name, total, creator_id, deadline):
        self.name=name
        self.total = total
        self.creator_id=creator_id
        self.deadline=deadline
        self.status = 0

class Debt(db.Model):
    __tablename__='debts'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer())
    bill_id = db.Column(db.Integer(), db.ForeignKey('bills.id'))
    collector_id =  db.Column(db.Integer(), db.ForeignKey('bills.creator_id'))
    debtor_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    status = db.Column(db.Integer())#0 - pending/1 - settled/2 - needs action/3 - overdue
    proof = db.Column(db.LargeBinary())
    claim_value = db.Column(db.Integer())#If the debtor settles part of the debt, the value that they claim to settle will be put here.

    def __init__(self,value,bill_id,collector_id,debtor_id):
        self.value=value
        self.bill_id=bill_id
        self.collector_id=collector_id
        self.debtor_id=debtor_id
        self.status = 0


class Notification(db.Model):
    __tablename__="notification"
    id = db.Column(db.Integer, primary_key=True)
    title =  db.Column(db.Text())
    content =  db.Column(db.Text())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    debt_id = db.Column(db.Integer(), db.ForeignKey('debts.id'))
    bill_id = db.Column(db.Integer(), db.ForeignKey('bills.id'))

    def __init__(self,title,content,user_id):
        self.title = title
        self.content = content
        self.user_id = user_id

# a model of a user for the database
class User(db.Model, UserMixin):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text())
    last_name = db.Column(db.Text())
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(1024))
    email = db.Column(db.Text())
    hhold_id = db.Column(db.Integer(), db.ForeignKey('hhold.id'))
    total_debt = db.Column(db.Integer())

    def __init__(self,first_name,last_name, username, password_hash, email, hhold_id):  
        self.first_name=first_name
        self.last_name=last_name
        self.username=username
        self.password_hash=password_hash
        self.email = email
        self.hhold_id=hhold_id
        self.total_debt=0

    def get(x):
        return x

    @property
    def password(self):
        raise AttributeError("Can't view password!")

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash,password)


from datetime import datetime
import time

# put some data into the tables
def dbinit():
    shared_list = [
        Household("Jules and Friends")
    ]
    db.session.add_all(shared_list)
    
    
    hhold_id = Household.query.filter_by(name="Jules and Friends").first().id
    user_list = [
        User("Abhiraaj","Sithambaram","abhi280901",generate_password_hash("strongpswrd"),"clans280901@gmail.com",hhold_id), 
        User("Narmatha","Murugesu","narmuru",generate_password_hash("strongpswrd"),"narmuru@yahoo.com",hhold_id),
        User("Angeline","Yi Feng","angie",generate_password_hash("strongpswrd"),"angie@yahoo.com",hhold_id)
        ]
    db.session.add_all(user_list)

    abhi_id = User.query.filter_by(username="abhi280901").first().id
    narm_id = User.query.filter_by(username="narmuru").first().id
    ang_id = User.query.filter_by(username="angie").first().id
    
    notf_list = Notification('New Debt','Ali Malar Kudi Yammathame',abhi_id)
    db.session.add(notf_list)

    bills_list = [
        Bills("Monthly Rent",200,abhi_id,datetime.now().date()),
        Bills("Lunch - 19/8",50,abhi_id,datetime.now().date()),
        Bills("Dinner - 24/8",50,abhi_id,datetime.now().date())
    ]

    db.session.add_all(bills_list)

    rent_id = Bills.query.filter_by(name="Monthly Rent").first().id
    lunch_id = Bills.query.filter_by(name="Lunch - 19/8").first().id

    debt_list = [
        Debt(20,rent_id,abhi_id,narm_id,0),
        Debt(20,rent_id,abhi_id,ang_id,1),
        Debt(15,lunch_id,abhi_id,narm_id,0),
    ]

    db.session.add_all(debt_list)

    # commit all the changes to the database file
    db.session.commit()
