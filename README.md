# Python QSYS QRC Wrapper
* Control QSC QSYS Core devices with python

# ToDo
* Flaskify... 
* Document, document, document

# Use
* For each QSC Core on the network instantiate a "Core" class
* When adding control objects they will "cast" themselves to the parent core class
    * The parent Core class instance is required as keyword arg "parent" when creating control objects
```python
#!/usr/bin/python3
import time
from qsys.classes import Core,Control,ChangeGroup

#returns epoch time
from qsys.helpers import epoch

def main():
    #See qsys.py for parameters in Core class
    #The initiail EngineStatus response parameters from the device will get added to Core.__dict__
    #You can pass "port" as well, but it defaults to 1710
    myCore = Core(Name='myCore',User='',Password='',ip='192.168.61.2')

    #Open the socket,creates "listen" and "keepalive" threads
    myCore.start()

    #ValueType can be a list of potential value types [int,float] or a single type "str" etc
    #This object is assumed to be a "gain" control object, so we can pass [int,float]
    gainControlObject = Control(parent=myCore,Name='namedControlInQsysDesigner',ValueType=[int,float])

    #To constantly monitor the state of your object use a ChangeGroup
    #You need to a ChangeGroup instance to add control objects and set polling rates
    #Parameters that are capitalize are that way because of the QRC parameter protocol
    #Id in this case is just the name of the ChangeGroup
    myChangeGroup = ChangeGroup(parent=myCore,Id='myChangeGroup')
    myChangeGroup.AddControl(gainControlObject)

    #Allow the socket time to connect and parse the initial responses
    time.sleep(2)

    #Set the change group auto poll rate
    #This rate is fast, your mileage may vary
    myChangeGroup.AutoPoll(Rate=0.1)

    #Value = value to set object to
    #TransId = QRC id parameter for transaction ID
    gainControlObject.set(Value=10,TransId=epoch())

    while True:
        print(gainControlObject.state)
        time.sleep(1)

if __name__ == '__main__':
    main()
```

# Notes
* In development, versions will change rapidly. This version doesn't do much yet.. stand by

# References
* https://q-syshelp.qsc.com/Content/External_Control/Q-Sys_Remote_Control/QRC.htm
* https://github.com/rakibtg/Python-Chat-App - simple chat app example with SocketIO, use for UI
