from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from threading import Thread,Event
import time,json,sys

sys.path.append("../../")
from qsys.classes import Core,ChangeGroup,Control

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

core = Core(Name='myCore',User='',Password='',ip='192.168.61.2')
core.start()    
time.sleep(2)
gainControlObject = Control(parent=core,Name='namedControlInQsysDesigner',ValueType=[int,float])    
myChangeGroup = ChangeGroup(parent=core,Id='eventlet')
myChangeGroup.AddControl(gainControlObject)
myChangeGroup.AutoPoll(Rate=0.1)


##---------------------------------------------------------------------
def randomNumberGenerator():
    last_val = None
    while not thread_stop_event.isSet():
        try:
            if(last_val != gainControlObject.state['Value']):
                print("change")
                try:
                    #socketio.emit('newnumber',json.dumps({"number":gainControlObject.state['Value']}),namespace='/test')
                    socketio.emit('newnumber', {'number': round(gainControlObject.state['Value'])}, namespace='/test')
                    
                except Exception as e:
                    print(type(e).__name__,e.args,"\n\n")
                last_val = gainControlObject.state['Value']
                print(gainControlObject.state['Value'])
                print(last_val)
        except KeyError:
            pass
        socketio.sleep(.1)


@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = socketio.start_background_task(randomNumberGenerator)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


##---------------------------------------------------------------------



if __name__ == '__main__':
    socketio.run(app)
