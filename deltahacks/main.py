from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from datetime import date
from datetime import timedelta

from flask import Flask, render_template, url_for,request, jsonify, session, redirect
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
from PIL import Image
import pytesseract as tess



app = Flask(__name__)

# Use a service account
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)

def list_users():
    users = db.collection('Users').get()
    list_users = [user.id for user in users]
    return list_users

@app.route('/')
def index():
    return "HOME"

@app.route('/home')
def home():
    user_dict = db.collection('Users').document('user@email.com').get().to_dict()
    return render_template('homepage.html', user_dict=user_dict)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        fullname = request.form.get('fullname')
        dateofbirth = request.form.get('dob')
        doctor = request.form.get('doctor')
        email = request.form.get('email')
        password = request.form.get('password')
        hash_pass = get_hashed_password(password.encode('utf-8'))
        db.collection('Users').document(email).set({"password": hash_pass,
                                                    "name": fullname,
                                                    "doctor": doctor,
                                                    "date of birth": dateofbirth,
                                                    "prescriptions": []})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        if email in list_users():
            user_ref = db.collection('Users').document(email).get().to_dict()
            hash_pass = user_ref['password']
            if check_password(password.encode('utf-8'), hash_pass):
                return redirect(url_for('home'))
            else:
                return "Incorrect Email or Password"
        else:
            "User does not Exist"
        return "SUCCESS!"
    return render_template('login.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    img = Image.open(request.files['file'])
    text = tess.image_to_string(img)
    result = extract_data(text)
    return redirect(url_for('home'))


def extract_data(prescription_text):
    f = open('drugs2.txt', 'r')
    commonDrugs = f.read().splitlines()
    f.close()
    instruction = ""
    instructionSet = False
    drug = "not found"
    drugSet = False
    start = ['take']
    end  = ['daily', 'day']
    amountKeys = ['cap', 'tabs']
    amountSet = False
    imgarr = prescription_text.split()
    for i in range(len(imgarr)):
        word = imgarr[i]
        if (word.lower() in commonDrugs and not drugSet):
            drug = word.lower().capitalize()
            drugSet = True
        if (word.lower() in amountKeys and not amountSet):
            amountSet = True
            amount = int(imgarr[i-1])
        if (word.lower() in start and not instructionSet):
            instructionSet = True
            while (word.lower() not in end):
                instruction += word.lower() +' '
                i+=1
                word = imgarr[i]
            instruction+=word.lower() +' '
        if (drugSet and instructionSet and amountSet): break


    dict1 = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    dict2 = {"once": 1, "twice": 2, "thrice": 3}
    daily_amt = 1
    for word in instruction.split():
        if word.isdigit():
            daily_amt *= int(word)
        if word in dict1.keys():
            daily_amt *= dict1[word]
        if word in dict2.keys():
            daily_amt *= dict2[word]


    data = db.collection('Users').document('user@email.com').get().to_dict()

    list_prescriptions = data['prescriptions']

    list_prescriptions.append({'Medication': drug,
                              'Quantity': int(amount),
                              'Dosage': instruction,
                              'Timing': ['9 AM', '2 PM', '6 PM'],
                             'Daily Amount': daily_amt
                             })
    data['prescriptions'] = list_prescriptions

    db.collection('Users').document('user@email.com').set(data)

    try:
        import argparse

        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
            if flags else tools.run(flow, store)
    CAL = build('calendar', 'v3', http=creds.authorize(Http()))

    def multipleevents(quantity, perday):
        totalleft = quantity
        timearr = [['11', '12'], [['09', '10'], ['15', '16']], [['9', '10'], ['14', '15'], ['18', '19']]]
        for i in range(len(timearr)):
            if i +1 == perday:
                for j in range(quantity // perday):
                    today = date.today()
                    GMT_OFF = '-05:00'
                    for k in range(perday):
                        EVENT = {
                            'summary': "Time To Take Medicine",
                            'start': {'dateTime': str((today + timedelta(days=j))) + 'T' + str(
                                timearr[i][k][0]) + ':00:00%s' % GMT_OFF},
                            'end': {'dateTime': str((today + timedelta(days=j))) + 'T' + str(
                                timearr[i][k][1]) + ':00:00%s' % GMT_OFF},

                        }
                        e = CAL.events().insert(calendarId='primary', \
                                                sendNotifications=True, body=EVENT).execute()

                        totalleft -= 1
                        if totalleft == 10:
                            EVENTREFILL = {
                                'summary': "Book Appointment With Doctor For Refill",
                                'start': {'dateTime': str((today + timedelta(days=j))) + 'T09:00:00%s' % GMT_OFF},
                                'end': {'dateTime': str((today + timedelta(days=j))) + 'T20:00:00%s' % GMT_OFF},

                            }
                            e = CAL.events().insert(calendarId='primary', \
                                                    sendNotifications=True, body=EVENTREFILL).execute()

                        print('''*** %r event added: \
                        Start: %s \
                        End: %s''' % (e['summary'].encode('utf-8'), e['start']['dateTime'], e['end']['dateTime']))

    multipleevents(amount, daily_amt)

    return [daily_amt, amount, drug, instruction]


if __name__ == '__main__':
    app.run(debug=True)