#!/usr/bin/python3
import json,socket,time,threading
from qsys.helpers import required_args,lineno,epoch
from logg3r import Log
import copy

init_logger = Log(log_path="./test_logs/",name='init_logger',level=1)

ErrorCodes = {
    -32700:'Parse error. Invalid JSON was received by the server.',
    -32600:'Invalid request. The JSON sent is not a valid Request object.',
    -32601:'Method not found.',
    -32602:'Invalid params.',
    -32603:'Server error.',
    2:'Invalid Page Request ID',
    3:'Bad Page Request - could not create the requested Page Request',
    4:'Missing file',
    5:'Change Groups exhausted',
    6:'Unknown change croup',
    7:'Unknown component name',
    8:'Unknown control',
    9:'Illegal mixer channel index',
    0:'Logon required'
}

Methods = {
    'Logon':None,
    'NoOp':None,
    'EngineStatus':{'params':{'State':str,'DesignName':str,'DesignCode':str,'IsRedundant':bool,'IsEmulator':bool}},
    'StatusGet':{'id':[int,float],'result':{'Platform':str,'State':str,'DesignName':str,'DesignCode':str,'IsRedundant':bool,'IsEmulator':bool,'Status':{'Code':int,'String':str}}}
}

IgnoreKeys = ['sock','logger','parent','ip','port']

#contains all method, control, etc objects
#handles parsing, etc - instantiate one per controlled QSC core
class Core():
    def __init__(self,**kwargs):
        required = {'User':str,
                    'Password':str,
                    'Name':str,
                    'ip':str}
        self.success,error = required_args(kwargs,required)
        if(self.success):
            try: 
                self.port = kwargs['port']
            except KeyError: 
                self.port = 1710 #standard port

            self.__dict__.update(**kwargs)
            self.logger = Log(log_path="./test_logs/",name='Core_{ip}'.format(**self.__dict__),level=1)
            self.logger.log("object initialized",1)

            #store objects and change groups
            self.Objects = {}
            self.ChangeGroups = {}

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ConnectionMethods = ConnectionMethods(parent=self,User=self.User,Password=self.Password)
            self.StatusMethods = StatusMethods(parent=self)
        else:
            init_logger.log(lineno()+"<qsys.Core class> __init__ () | {}".format(error),5)
    
    def start(self):
        if(self.connect()):
            threading.Thread(target=self.listen).start()
            threading.Thread(target=self.keepalive).start()

    def connect(self):
        try:
            self.sock.connect((self.ip,self.port))
            return True
        except Exception as e:
            self.logger.log(lineno()+"<qsys.Core class> connect() | {} | {}".format(type(e).__name__,e.args),5)
            return False

    def listen(self):
        while True:
            try:
                rx = self.sock.recv(65534).decode('utf-8')
                self.parse(rx)
            except Exception as e:
                print(rx)
                self.logger.log(lineno()+"<qsys.Core class> listen() | {} | {}".format(type(e).__name__,e.args),5)
            time.sleep(.001)

    def keepalive(self):
        while True:
            self.ConnectionMethods.NoOp()
            time.sleep(60)
            #clean up worker threads
            for t in threading.enumerate():
                if(not t.is_alive()):
                    t.join()

    #THIS CODE SUCKS
    def parse(self,payload): #need to think about this some more
        try:
            payload = json.loads(payload.replace("\0",""))
        except json.JSONDecodeError:
            return False
        except Exception as e:
            print(payload)
            self.logger.log(lineno()+"<qsys.Core class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            return False

        ## THERE IS A MORE EFFICIENT WAY TO DO THIS
        try:
            result = payload['result']
        except KeyError:
            try:
                result = payload['params']['Changes']
            except KeyError:
                try:
                    error = payload['error']
                    self.logger.log(lineno()+"<qsys.Core class> error | code: {} | message: {}".format(error['code'],error['message']),5)
                except KeyError:
                    try:
                        if('EngineStatus' in payload['method']):
                            self.__dict__.update(**payload['params']) #update __dict__ with EngineStatus tokens
                        else:
                            print("no idea...") #this is where group stuff could go
                            print(payload)
                            return False
                    except KeyError:
                        print("no idea...")
                        print(payload)
                        return False
        except Exception as e:
            #self.logger.log(lineno()+"<qsys.Core class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            #COME BACK TO THIS
            return False

        #parse messages
        try:
            if(isinstance(result,list)):
                for item in result:
                    try:
                        self.Objects[item['Name']].state.update(**item)
                        if(self.Objects[item['Name']].state != self.Objects[item['Name']].last_state):
                            #print(self.Objects[item['Name']].state)
                            self.Objects[item['Name']].last_state = copy.copy(self.Objects[item['Name']].state)
                    except Exception as e:
                        self.logger.log(lineno()+"<qsys.Core class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            elif(isinstance(result,dict)):
                try:
                    self.Objects[result['Name']].state.update(**result)
                    if(self.Objects[result['Name']].state != self.Objects[result['Name']].last_state):
                        #print(self.Objects[result['Name']].state)
                        self.Objects[result['Name']].last_state = copy.copy(self.Objects[result['Name']].state)
                except Exception as e:
                    self.logger.log(lineno()+"<qsys.Core class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            else:
                self.logger.log(lineno()+"<qsys.Core class> parse() - result isn't a list or dictionary!",5)
        except Exception as e:
            self.logger.log(lineno()+"<qsys.Core class> parse() - {} | {}".format(type(e).__name__,e.args),5)

    def __adopt__(self,obj):
        try:
            self.Objects.update({obj.Name:obj})
        except AttributeError:
            self.ChangeGroups.update({obj.Id:obj})

    def __repr__(self):
        return '<qsys.Core class | Name: {Name} | Ip: {ip}>'.format(**self.__dict__)

#Control methods
class Base():    
    def struct(self):
        return {'jsonrpc':'2.0','method':'{method}','params':'{params}'}

    def encode(self,s,logger):
        try:
            return (json.dumps(s)+"\0").encode('utf-8')
        except Exception as e:
            logger.log(lineno()+"<qsys.Base class> encode() | {} | {}".format(type(e).__name__,e.args),5)
            return False

    def send(self,sock,logger,**kwargs):
        tmp = self.struct()
        tmp.update(**kwargs)
        try:
            sock.send(self.encode(tmp,logger))
        except Exception as e:
            logger.log(lineno()+"<qsys.Base class> send() | {} | {}".format(type(e).__name__,e.args),5)
            return False
        return True

    def __cast__(self): #allocate to parent Core class
        self.parent.__adopt__(self)

class ConnectionMethods(Base):
    def __init__(self,**kwargs):
        required = {'parent':Core,'User':str,'Password':str}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
        else:
            init_logger.log(lineno()+"<qsys.ConnectionMethods class> __init__() | {}".format(error),5)

    def Logon(self):
        return self.send(self.parent.sock,self.parent.logger,method='logon',params={'User':self.User,'Password':self.Password})

    def NoOp(self):
        return self.send(self.parent.sock,self.parent.logger,method='NoOp',params={})
    
    def __repr__(self):
        return '<qsys.ConnectionMethods class | Parent: {}>'.format(self.parent.name)

class StatusMethods(Base):
    def __init__(self,**kwargs):
        required = {'parent':Core}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
        else:
            init_logger.log(lineno()+"<qsys.ConnectionMethods class> __init__() | {}".format(error),5)
    
    def StatusGet(self,**kwargs):
        required = {'TransId':[int,float]}
        success,error = required_args(kwargs,required)
        if(success):
            return self.send(self.parent.sock,self.parent.logger,method='StatusGet',id=kwargs['TransId'],params=0)
        else:
            self.parent.logger.log(lineno()+"<qsys.StatusMethods class> StatusGet() | {}".format(error),5)
            return False
    
    def __repr__(self):
        return '<qsys.StatusMethods class | Parent: {}>'.format(self.parent.name)

class ChangeGroup(Base):
    def __init__(self,**kwargs):
        required = {'parent':Core,'Id':str}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
            self.__cast__()
            self.AutoPollState = False
            self.AutoPollRate = False
        else:
            init_logger.log(lineno()+"<qsys.ChangeGroup class> __init__() | {}".format(error),5)

    def AddControl(self,obj):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.AddControl',params={'Id':self.Id,'Controls':[obj.Name]})

    def AddComponentControl(self,obj):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.AddComponentControl',params={'Id':self.Id,'Component':{'Name':obj.Name,'Controls':[obj.Controls]}})

    def Remove(self,obj):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Remove',params={'Id':self.Id,'Controls':[obj.Name]})

    def Destroy(self):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Destroy',params={'Id':self.Id})

    def Invalidate(self):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Invalidate',params={'Id':self.Id})

    def Clear(self):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Clear',params={'Id':self.Id})

    def Poll(self,**kwargs):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Poll',id=epoch(),params={'Id':self.Id})

    def AutoPoll(self,**kwargs):
        required = {'Rate':[int,float]}
        success,error = required_args(kwargs,required)
        if(success):
            self.AutoPollState = True
            self.AutoPollRate = kwargs['Rate']
            return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.AutoPoll',id=epoch(),params={'Id':self.Id,'Rate':self.AutoPollRate})
        else:
            self.parent.logger.log(lineno()+"<qsys.qsys.ChangeGroup class> AutoPoll() | Id: {} | {}".format(self.Id,error),5)

    def __repr__(self):
        return '<qsys.ChangeGroup class | Parent: {} | Id: {}>'.format(self.parent.Name,self.Id)

class Control(Base):
    #self.init = initialized state of control
    def __init__(self,**kwargs):
        required = {'parent':Core,'Name':str,'ValueType':'*'}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
            self.init = True
            self.state = {}
            self.last_state = {}
            self.__cast__()
            self.get(TransId=epoch())
        else:
            init_logger.log(lineno()+"<qsys.Control class> __init__() | {}".format(error),5)
            self.init = False

    def get(self,**kwargs):
        required = {'TransId':[int,float]}
        success,error = required_args(kwargs,required)
        if(success):
            return self.send(self.parent.sock,self.parent.logger,method='Control.Get',id=kwargs['TransId'],params=[self.Name])
        else:
            self.parent.logger.log(lineno()+"<qsys.Control class> set() - {} | {}".format(self.Name,error),5)
            return False

    def set(self,**kwargs):
        required = {'TransId':[int,float],'Value':self.ValueType} #option 'Ramp' parameter - sets ramp time used to set the control
        success,error = required_args(kwargs,required)
        if(success):
            kwargs['Name'] = self.Name
            #comprehension to remove TransID
            params = {k:v for k,v in kwargs.items() if k != 'TransId'}
            return self.send(self.parent.sock,self.parent.logger,method='Control.Set',id=kwargs['TransId'],params={k:v for k,v in kwargs.items() if k not in IgnoreKeys})
        else:
            self.parent.logger.log(lineno()+"<qsys.Control class> set() - {} | {}".format(self.Name,error),5)
            return False

    def __repr__(self):
        return '<qsys.Control class | Parent: {} | Name: {}>'.format(self.parent.name,self.Name)

class ComponentControl(Base): #coming soon
    def __init__(self,**kwargs):
        pass

class MixerControl(Base): #coming soon
    def __init__(self,**kwargs):
        pass

class LoopPlayerControl(Base): #coming soon
    def __init__(self,**kwargs):
        pass
