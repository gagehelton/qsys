from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from threading import Thread,Event
import time,json,sys,argparse

sys.path.append("../../")
from qsys.classes import Core,ChangeGroup,Control
from qsys.helpers import scale_number

#cli arg parser
parser = argparse.ArgumentParser()
parser.add_argument("-a","--address",help="IP Address of QSYS Core",required=True)
args = parser.parse_args()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

#super crappy init of Core objects
core = Core(Name='myCore',User='',Password='',ip=args.address)
core.start()    

time.sleep(2)

controlObjects = [Control(parent=core,Name='namedControlInQsysDesigner',ValueType=[int,float]),
                   Control(parent=core,Name='namedControlInQsysDesigner2',ValueType=[int,float])]

myChangeGroup = ChangeGroup(parent=core,Id='eventlet')

myChangeGroup.AddControl(controlObjects[0])
myChangeGroup.AddControl(controlObjects[1])

myChangeGroup.AutoPoll(Rate=0.1)

##---------------------------------------------------------------------

def monitorCore():
    last_val = None
    while not thread_stop_event.isSet():
        try:
            for i in range(len(controlObjects)):
                if(controlObjects[i].change):
                    try:
                        socketio.emit(controlObjects[i].Name, {'value': scale_number(controlObjects[i].state['Value'])}, namespace='/test')
                    except Exception as e:
                        print(type(e).__name__,e.args,"\n\n")
                controlObjects[i].change = False
        except KeyError:
            pass
        socketio.sleep(.1)

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread

    #THERE IS A BETTER WAY TO DO THIS
    o = []
    for i in range(len(controlObjects)):
        o.append(controlObjects[i].Name)

    #send object names to js to create front end objects
    socketio.emit('payload',o,namespace='/test')
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = socketio.start_background_task(monitorCore)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

##---------------------------------------------------------------------

if __name__ == '__main__':
    socketio.run(app)
