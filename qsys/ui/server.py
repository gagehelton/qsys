from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time,threading
import sys
sys.path.append("../../")
from qsys.classes import Core,ChangeGroup,Control

app = Flask(__name__)
socketio = SocketIO(app,async_mode='threading')

core = Core(Name='myCore',User='',Password='',ip='192.168.61.2')
core.start()    
time.sleep(2)
gainControlObject = Control(parent=core,Name='namedControlInQsysDesigner',ValueType=[int,float])    
myChangeGroup = ChangeGroup(parent=core,Id='myChangeGroup')
myChangeGroup.AddControl(gainControlObject)
myChangeGroup.AutoPoll(Rate=0.1)

thread = None

def bg_task():
    print("BG")
    last_val = False
    while True:
        try:
            if(last_val != gainControlObject.state['Value']):
                print("change")
                try:
                    emit('my response',gainControlObject.state['Value'],namespace='')
                except Exception as e:
                    print(type(e).__name__,e.args,"\n\n")
                last_val = gainControlObject.state['Value']
                print(gainControlObject.state['Value'])
                print(last_val)
        except KeyError:
            pass

@socketio.on('connect')
def start():
    print("connect")
    emit('my response', 'start')
    global thread
    if thread is None:
        print('thread ding')
        thread = socketio.start_background_task(target=bg_task)
    return render_template('ChatApp.html')

def messageRecieved():
    print('rx')

@socketio.on('my event')
def handle_my_custom_event(json):
    print('rx: {}'.format(str(json)))
    socketio.emit('my response',json,callback=messageRecieved)

@app.route("/")
def index():
    return render_template('ChatApp.html')

if __name__ == '__main__':
    socketio.run(app,debug=True)
