from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug import security
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user, login_required
from sqlalchemy import text
from markupsafe import escape
from datetime import datetime
import base64
import string
import random

# create the Flask app
from flask import Flask, render_template, redirect, session, request, jsonify, flash
app = Flask(__name__)
app.secret_key = 'any Su93r$3cret string you want'

# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///todo.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# set up a 'model' for the data you want to store
from db_schema import db, User, Bills, Household, Debt, Notification, dbinit


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# init the database so it can connect with our app
db.init_app(app)

# change this to False to avoid resetting the database every time this app is restarted
resetdb = True
if resetdb:
    with app.app_context():
        # create all the tables when first initializing the app.
        db.create_all()
        #dbinit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


#route to the index
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = escape(request.form["uname"])
        password = escape(request.form["pswrd"])
        user = User.query.filter_by(username=username).first()
        if user == None:
            flash("No account with that username found. Please register!")
            return redirect('/')
        else:
            if user.verify_password(password):
                # password is good so it is possible to login
                login_user(user)
                return redirect('/not')
            else:
                flash("Incorrect login details. Please enter the correct password!")
                return redirect('/')

@app.route('/reg',  methods = ['GET','POST'])
def reg():
    if request.method == 'POST':
        hashed_password = security.generate_password_hash(escape(request.form["pswrd"]))
        username = escape(request.form["uname"])
        hhold = request.form['hhold']
        if hhold == 'no':
            house = Household(request.form['hhold_name'])
            db.session.add(house)
            db.session.commit()
            house.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        else:
            code = request.form['hhold_code']
            house = Household.query.filter_by(code=code).first()
            if house == None:
                flash("There is no household with that code. Please enter a valid code.")
                return render_template('reg.html')
        user = User(escape(request.form["first-name"]), escape(request.form["last-name"]), username, hashed_password, escape(request.form["email"]),house.id)
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(username=username).first()
        login_user(user)
        return redirect('/not')
    else:
        return render_template('reg.html')

@app.route('/overdue', methods=['GET','POST'])
@login_required
def overdue():
    if request.method == 'POST':
        debt_id = request.form['debt_id']
        debt = Debt.query.filter_by(id=debt_id).first()
        debt.status = 3
        db.session.commit()
        return jsonify({'status':debt.status, 'id':debt.id})


@app.route('/add', methods=['GET','POST'])
@login_required
def add():
    if request.method == 'POST':      
        name = escape(request.form['name'])
        value = int(escape(request.form['value']))
        deadline = escape(request.form['deadline'])
        deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        bill_img = request.files['bill']
        userid = current_user.id
        newbill = Bills(name,value,userid,deadline)
        newbill.image = bill_img.read()
        db.session.add(newbill)
        userid=current_user.id
        user = User.query.filter_by(id=userid).first()
        tenants = User.query.filter_by(hhold_id=user.hhold_id).all()
        i = 1
        people = request.form.getlist('hmates')
        for entry in tenants:
            for member in people:
                if (member == str(entry.id)):
                    i += 1
        db.session.commit()
        bill_id= Bills.query.filter_by(name = name).first().id
        debt_value = round(value/i,2)
        first_name= User.query.filter_by(id=userid).first().first_name
        for entry in tenants:
            for member in people:
                if (member == str(entry.id)):
                    id1 = entry.id
                    entry.total_debt += debt_value
                    debt = Debt(debt_value,bill_id,userid,id1)
                    notf_list = [Notification("Debt Status ("+name+")",first_name+'''
                    introduced a new bill, and you owe him/her £
                    '''+str(debt_value)+". Navigate to the To Pay tab for more details.",id1),
                    Notification("Bill -"+entry.first_name+" ("+name+")",'''
                    You introduced a new bill, and ''' + entry.first_name+''' owes you £
                    '''+str(debt_value)+'''. Navigate to the To Receive 
                    tab for more details. This notification will disappear when
                    him/her pays your bill.
                    ''',userid)]
                    db.session.add(debt)
                    db.session.add_all(notf_list)
                    db.session.commit()
                    notf_list[0].debt_id = Debt.query.filter_by(debtor_id=id1, bill_id=bill_id).first().id
                    notf_list[1].bill_id = bill_id 
                    db.session.commit()
        db.session.commit()
        return redirect('/not')
    else:
        userid = current_user.id
        user = User.query.filter_by(id=userid).first()
        housemates = User.query.filter_by(hhold_id=user.hhold_id).all()
        return render_template('add.html', housemates=housemates, user=user)

@app.route('/bill')
@login_required
def bill():
    array = {}
    settle = {}
    bill_id = escape(request.args.get("id"))
    bills = Bills.query.get(bill_id)
    userid = current_user.id
    if bills.creator_id == userid:
        bill_img = bills.image
        newimage = base64.b64encode(bill_img).decode('utf-8')
        
        debts = Debt.query.filter_by(bill_id=bill_id,status=0).all()
        need_action = Debt.query.filter_by(bill_id=bill_id,status=2).all()
        settled = Debt.query.filter_by(bill_id=bill_id,status=1).all()
        overdue = Debt.query.filter_by(bill_id=bill_id,status=3).all()
        for entry in debts:    
            debtor_id = entry.debtor_id
            debtors = User.query.filter_by(id=debtor_id).first()
            array[debtors]=entry
        for entry in need_action:    
            debtor_id = entry.debtor_id
            debtors = User.query.filter_by(id=debtor_id).first()
            array[debtors]=entry
        for entry in overdue:    
            debtor_id = entry.debtor_id
            debtors = User.query.filter_by(id=debtor_id).first()
            array[debtors]=entry
        for entry in settled:
            debtor_id = entry.debtor_id
            settlers = User.query.filter_by(id=debtor_id).first()
            settle[settlers]=entry
        return render_template('bill.html',bills=bills, array=array,settle=settle,newimage=newimage)
    else:
        return redirect ('/logout')

@app.route('/hhold')
@login_required
def hhold():
    if current_user.is_authenticated:
        userid = current_user.id
        bills = Bills.query.filter_by(creator_id=userid, status=0).all()
        user = User.query.filter_by(id=userid).first()
        hhold = Household.query.filter_by(id=user.hhold_id).first()
        return render_template('hhold.html', user=user, hhold=hhold)

@app.route('/debt')
@login_required
def debt():
    userid = current_user.id
    user = User.query.filter_by(id=userid).first()
    debts_pending = Debt.query.filter_by(debtor_id=userid,status=0).all()
    debts_action = Debt.query.filter_by(debtor_id=userid,status=2).all()
    debts_overdue = Debt.query.filter_by(debtor_id=userid,status=3).all()
    array = {}
    for entry in debts_pending:    
        bill_id = entry.bill_id
        bills = Bills.query.filter_by(id=bill_id).first()
        array[bills]=entry
    for entry in debts_action:    
        bill_id = entry.bill_id
        bills = Bills.query.filter_by(id=bill_id).first()
        array[bills]=entry
    for entry in debts_overdue:    
        bill_id = entry.bill_id
        bills = Bills.query.filter_by(id=bill_id).first()
        array[bills]=entry
    return render_template('debt.html',array=array, user=user)


@app.route('/rembill', methods=['POST','GET'])
@login_required
def rem():
    if request.method == 'POST':
        bill_id = request.form['bill_id']
        bill = Bills.query.filter_by(id=bill_id).first()
        bill.status = 1
        db.session.commit()
        return 'ble'


@app.route('/home')
@login_required
def home():
    if current_user.is_authenticated:
        userid = current_user.id
        bills = Bills.query.filter_by(creator_id=userid, status=0).all()
        user = User.query.filter_by(id=userid).first()
        return render_template('hm.html',bills=bills,user = user)
    else: 
        return redirect('/')

@app.route('/not', methods=['GET','POST'])
@login_required
def notf():
    if request.method == 'POST':
        not_id = request.form['not_id']
        notf = Notification.query.filter_by(id=not_id).first()
        content = notf.content
        return jsonify({'content': content})
    else:
        userid = current_user.id
        i = 0
        notf = Notification.query.filter_by(user_id=userid).all()
        for entry in notf:
            i += 1
        return render_template('not.html', notf=notf, i=i)


@app.route('/remove',methods=['GET','POST'])
@login_required
def remove():
    bill_id = escape(request.args.get("id"))
    Bills.query.filter_by(id=bill_id).delete()
    nots = Notification.query.filter_by(bill_id=bill_id).all()
    for entry in nots:
        db.session.delete(entry)
    debts = Debt.query.filter_by(bill_id=bill_id).all()
    for entry in debts:
        notf = Notification.query.filter_by(debt_id=entry.id).delete()
        db.session.delete(entry)
    db.session.commit()
    return redirect('/home')




@app.route('/spec',methods=['GET','POST'])
@login_required
def spec():
    if request.method == 'POST':
        debt_id = request.form['debt_id']
        proof = request.files['proof']
        debt = Debt.query.filter_by(id=debt_id).first()
        debt.status = 2
        debt.proof = proof.read()
        bill = Bills.query.filter_by(id=debt.bill_id).first()
        collector = User.query.filter_by(id=debt.collector_id).first()
        userid = current_user.id
        debtor = User.query.filter_by(id=userid).first()
        notf = Notification.query.filter_by(debt_id=debt_id).first()
        notf.content = collector.first_name+'''
        have been notified on your Sp.ILL clear request. We will notify you when he/she responds
        to your request. Click on your debt for('''+bill.name+") under the To Pay tab on the navigation menu for more details"
        notf_col = Notification.query.filter_by(title = "Bill -"+debtor.first_name+" ("+bill.name+")").first()
        notf_col.content =debtor.first_name+'''
        claims to have cleared this Sp.ILL. Click on your bill('''+bill.name+") under the To Receive tab on the navigation menu to approve or decline."
        if request.form['settle'] == 'no':
            value = int(request.form['value'])
            debt.claim_value = value
            db.session.commit()
            return redirect('/debt')
        debt.claim_value = debt.value
        db.session.commit()
        return redirect('/not')
    else:
        bill_id = escape(request.args.get("id"))
        debt_id = escape(request.args.get("id2"))
        userid = current_user.id
        bill = Bills.query.filter_by(id=bill_id).first()

        debt = Debt.query.filter_by(id=debt_id).first()
        if debt.debtor_id == userid and debt.bill_id == bill.id:
            collector_id = Debt.query.filter_by(id=debt_id).first().collector_id
            collector = User.query.filter_by(id = collector_id).first()
            return render_template('spec.html',bill=bill,debt=debt, user=collector)
        else:
            flash('Your are trying to access content that is restricted to you!')
            return redirect('/logout')

@app.route('/revert', methods=['POST'])
@login_required
def rev():
    if request.method == 'POST':
        debt_id = request.form['debt_id']
        debt = Debt.query.filter_by(id=debt_id).first()
        debt.status = 0
        collector = User.query.filter_by(id=debt.collector_id).first()
        debtor = User.query.filter_by(id=debt.debtor_id).first()
        notf = Notification.query.filter_by(debt_id = debt_id).first()
        notf.content = 'Uh-oh, it appears that '+collector.first_name+'''
        has declined your previous clear request. Please provide more
        proof and re-send another request. Navigate to the To Pay tab
        for more details on your debt.
        '''
        bill = Bills.query.filter_by(id=debt.bill_id).first()
        notf2 = Notification.query.filter_by(title= "Bill -"+debtor.first_name+" ("+bill.name+")",bill_id = bill.id).first()
        notf2.content = 'The bill has been reverted to '+debtor.first_name+'.'
        db.session.commit()
        return jsonify({'status': debt.status})


@app.route('/spec2',methods=['GET','POST'])
@login_required
def spec2():
    if request.method== 'POST':
        debt_id = request.form['debt_id']
        debt = Debt.query.filter_by(id=debt_id).first()
        debt.value = debt.value - debt.claim_value
        debtor = User.query.filter_by(id = debt.debtor_id).first()
        debtor.total_debt -= debt.claim_value
        bill = Bills.query.filter_by(id=debt.bill_id).first()
        notf = Notification.query.filter_by(debt_id = debt.id).first()
        notf2 = Notification.query.filter_by(title = "Bill -"+debtor.first_name+" ("+bill.name+")",bill_id = bill.id).first()
        if debt.value == 0:
            debt.status = 1
            Notification.query.filter_by(debt_id = debt.id).delete()
            Notification.query.filter_by(title = "Bill -"+debtor.first_name+" ("+bill.name+")",bill_id = bill.id).delete()
        else:
            debt.status = 0
            notf.content = '''
            Your clear request was successful and the debt value has reduced. Navigate to the To Pay tab
            and click on the debt for more info.
            '''
            notf2.content = '''
            This debt has been updated.
            '''
       
        Notification.query.filter_by(title = "Clear Request ("+bill.name+')').delete()
        db.session.commit()
        return jsonify({'status': debt.status,'value':debt.value})
    
    else:
        userid = current_user.id
        debtor_id = escape(request.args.get("id"))
        debt_id = escape(request.args.get("id2"))
        debtor = User.query.filter_by(id=debtor_id).first()
        debt = Debt.query.filter_by(id=debt_id).first()
        bill = Bills.query.filter_by(id=debt.bill_id).first()
        if debt.collector_id == userid and debt.debtor_id == debtor.id:
            if debt.status == 2:
                debt_img = debt.proof
                newimage = base64.b64encode(debt_img).decode('utf-8')
            else:
                newimage = 0
            return render_template('spec2.html',debtor=debtor,debt=debt,bill=bill,proof=newimage)
        else:
            flash('Your are trying to access content that is restricted to you!')
            return redirect('/logout')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


