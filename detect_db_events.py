#https://stackoverflow.com/questions/58354509/modulenotfounderror-no-module-named-python-jwt-raspberry-pi
#https://github.com/thisbejim/Pyrebase
#https://stackoverflow.com/questions/45154853/how-to-detect-changes-in-firebase-child-with-python


#this may be helpful if i cant figure something else out for updating values
#https://pypi.org/project/FirebaseData/


#This may be the thing to do
#https://github.com/thisbejim/Pyrebase/issues/341

#OTHER
#________________
#https://stackoverflow.com/questions/62301320/pyrebase-and-firebase-database-rules-how-to-deal-with-it-with-python
#https://www.reddit.com/r/Firebase/comments/idhdji/how_can_i_store_data_under_a_user_id_with_pyrebase/g2bcvhz/
#https://medium.com/@parasmani300/pyrebase-firebase-in-flask-d249a065e0df
#https://stackoverflow.com/questions/54838847/pyrebase-stream-retrived-data-access

import os.path
import sys
import time

#set proper path for modules
sys.path.append('/home/pi/grow-ctrl')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')


import pyrebase
from multiprocessing import Process, Queue
import json

#declare state variables
device_state = None #describes the current state of the system
grow_params = None #holds growing parameters
access_config = None #contains credentials for connecting to firebase

#loads device state, hardware, and access configurations
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, grow_params, access_config

    with open("/home/pi/device_state.json") as d:
        device_state = json.load(d) #get device state
    d.close()

    with open("/home/pi/grow_params.json") as g:
        grow_params = json.load(g) #get hardware state
    g.close()

    with open("/home/pi/access_config.json") as a:
        access_config = json.load(a) #get access state
    a.close()

#save key values to .json
def write_state(path,field,value): #Depends on:, 'json'; Modifies: path
    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()
    x.close()

def initialize_user(RefreshToken):

#app configuration information
    config = {
    "apiKey": "AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc",
    "authDomain": "oasis-1757f.firebaseapp.com",
    "databaseURL": "https://oasis-1757f.firebaseio.com/",
    "storageBucket": "gs://oasis-1757f.appspot.com"
    }

    firebase = pyrebase.initialize_app(config)

    # Get a reference to the auth service
    auth = firebase.auth()

    # Get a reference to the database service
    db = firebase.database()

    #WILL NEED TO GET THIS FROM USER
    user = auth.refresh(RefreshToken)

    return user, db

#get all user data
def get_user_data(user, db):
    return  db.child(user['userId']).get(user['idToken']).val()

def stream_handler(m):
    #ok some kind of update
    #might be from start up or might be user changed it
    if m['event']=='put':
        act_on_event(m['stream_id'],m['data'])
        print(m)

    #something else
    else:
        pass
        #if this happens... theres a problem...
        #should be handled for
        print('something wierd...')

def detect_field_event(user, db, field):
    my_stream = db.child(user['userId']+'/'+access_config["device_name"]+"/"+field).stream(stream_handler, user['idToken'], stream_id=field)

#https://stackoverflow.com/questions/2046603/is-it-possible-to-run-function-in-a-subprocess-without-threading-or-writing-a-se
#https://stackoverflow.com/questions/200469/what-is-the-difference-between-a-process-and-a-thread#:~:text=A%20process%20is%20an%20execution,sometimes%20called%20a%20lightweight%20process.
#run multiprocesser to handle database listener
#could use threads in future? would it be better?
def detect_multiple_field_events(user, db, fields):
    for field in fields:
        p = Process(target=detect_field_event, args=(user, db, field))
        p.start()

#make change to config file
def act_on_event(field, new_data):
    #get data and field info

    #checks if file exists and makes a blank one if not
    #the path has to be set for box
    device_state_fields = list(device_state.keys())
    grow_params_fields = list(grow_params.keys())

    if str(field) in device_state_fields:
        path = '/home/pi/device_state_buffer.json'
    if str(field) in grow_params_fields:
        path = '/home/pi/grow_params_buffer.json'

    if os.path.exists(path) == False:
        f = open(path, "w")
        f.write("{}")
        f.close()

    #open data config file
    #edit appropriate spot
    #print(path)
    write_state(path,field,new_data)

if __name__ == '__main__':
    print("Starting listener...")
    load_state()
    try:
        user, db = initialize_user(access_config['refresh_token'])
        print("Database monitoring: active")
    except Exception as e:
        print("Listener could not connect")
        print("Database monitoring: inactive")
        sys.exit()
    #print(get_user_data(user, db)) #Avi what do these lines do
    #detect_field_event(user, db, 'set_temp')
    device_state_fields = list(device_state.keys())
    grow_params_fields = list(grow_params.keys())
    fields = device_state_fields + grow_params_fields

    detect_multiple_field_events(user, db, fields)





