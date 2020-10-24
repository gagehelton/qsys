#!/usr/bin/python3

import json,socket,time,threading
from helpers import required_args,lineno,epoch
from logg3r import Log


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
                    'ip':str}
        self.success,error = required_args(kwargs,required)
        if(self.success):
            try: 
                self.port = kwargs['port']
            except KeyError: 
                self.port = 1710 #standard port

            self.__dict__.update(**kwargs)
            print(self.__dict__)
            self.logger = Log(log_path="./test_logs/",name='Core_{ip}'.format(**self.__dict__),level=1)
            self.logger.log("object initialized",1)

            #store objects and change groups
            self.objects = {}
            self.change_groups = {}

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ConnectionMethods = ConnectionMethods(parent=self,User=self.User,Password=self.Password)
            self.StatusMethods = StatusMethods(parent=self)
        else:
            init_logger.log(lineno()+"<Core class> __init__ () | {}".format(error),5)
    
    def start(self):
        if(self.connect()):
            threading.Thread(target=self.listen).start()
            threading.Thread(target=self.keepalive).start()

    def connect(self):
        print(self.ip,self.port)
        try:
            self.sock.connect((self.ip,self.port))
            return True
        except Exception as e:
            self.logger.log(lineno()+"<Core class> connect() | {} | {}".format(type(e).__name__,e.args),5)
            return False

    def listen(self):
        while True:
            try:
                rx = self.sock.recv(4096).decode('utf-8')
                self.parse(rx)
            except Exception as e:
                self.logger.log(lineno()+"<Core class> listen() | {} | {}".format(type(e).__name__,e.args),5)
            time.sleep(.001)

    def keepalive(self):
        while True:
            self.ConnectionMethods.NoOp()
            time.sleep(60)
            #clean up worker threads
            for t in threading.enumerate():
                if(not t.is_alive()):
                    t.join()

    def parse(self,payload): #need to think about this some more
        parsed = {}
        payload = json.loads(payload.replace("\0",""))
        try:
            result = payload['result']
        except KeyError:
            try:
                result = payload['params']['Changes']
            except KeyError:
                print("FIX THIS SHIT")
                return False
        
        try:
            if(isinstance(result,list)):
                for item in result:
                    try:
                        self.objects[item['Name']].state.update(**item)
                    except Exception as e:
                        self.logger.log(lineno()+"<ObjectStore class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            elif(isinstance(result,dict)):
                try:
                    self.objects[result['Name']].state.update(**result)
                except Exception as e:
                    self.logger.log(lineno()+"<ObjectStore class> parse() - {} | {}".format(type(e).__name__,e.args),5)
            else:
                self.logger.log(lineno()+"<ObjectStore class> parse() - result isn't a list or dictionary!",5)
        except Exception as e:
            self.logger.log(lineno()+"<ObjectStore class> parse() - {} | {}".format(type(e).__name__,e.args),5)

    def __adopt__(self,obj):
        try:
            self.objects.update({obj.Name:obj})
        except AttributeError:
            self.objects.update({obj.Id:obj})

    def __repr__(self):
        return self.ip

class Base():    
    def struct(self):
        return {'jsonrpc':'2.0','method':'{method}','params':'{params}'}

    def encode(self,s,logger):
        try:
            return (json.dumps(s)+"\0").encode('utf-8')
        except Exception as e:
            logger.log(lineno()+"<Base class> encode() | {} | {}".format(type(e).__name__,e.args),5)
            return False

    def send(self,sock,logger,**kwargs):
        tmp = self.struct()
        tmp.update(**kwargs)
        try:
            sock.send(self.encode(tmp,logger))
        except Exception as e:
            logger.log(lineno()+"<Base class> send() | {} | {}".format(type(e).__name__,e.args),5)
            return False
        return True

    def __cast__(self): #allocate to parent Core class
        self.parent.__adopt__(self)

class ConnectionMethods(Base):
    def __init__(self,**kwargs):
        required = {'parent':'*','User':str,'Password':str}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
        else:
            init_logger.log(lineno()+"<ConnectionMethods class> __init__() | {}".format(error),5)

    def Logon(self):
        return self.send(self.parent.sock,self.parent.logger,method='logon',params={'User':self.User,'Password':self.Password})

    def NoOp(self):
        return self.send(self.parent.sock,self.parent.logger,method='NoOp',params={})

class StatusMethods(Base):
    def __init__(self,**kwargs):
        required = {'parent':'*'}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
        else:
            init_logger.log(lineno()+"<ConnectionMethods class> __init__() | {}".format(error),5)
    
    def StatusGet(self,**kwargs):
        required = {'TransId':[int,float]}
        success,error = required_args(kwargs,required)
        if(success):
            return self.send(self.parent.sock,self.parent.logger,method='StatusGet',id=kwargs['TransId'],params=0)
        else:
            self.parent.logger.log(lineno()+"<StatusMethods class> StatusGet() | {}".format(error),5)
            return False

class ChangeGroup(Base):
    def __init__(self,**kwargs):
        required = {'parent':'*','Id':str}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
            self.auto_poll = False
            self.auto_poll_rate = False
            self.__cast__()
        else:
            init_logger.log(lineno()+"<ChangeGroup class> __init__() | {}".format(error),5)
    
    def poll(self,**kwargs):
        try:
            self.auto_poll = kwargs['auto']
            try:
                self.auto_poll_rate = kwargs['rate']
            except:
                pass
        except:
            pass
        if(self.auto_poll):
            return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.AutoPoll',id=epoch(),params={'Id':self.Id,'Rate':self.auto_poll_rate})
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.Poll',id=epoch(),params={'Id':self.Id})

    def add_control(self,obj):
        return self.send(self.parent.sock,self.parent.logger,method='ChangeGroup.AddControl',params={'Id':self.Id,'Controls':[obj.Name]})

    def __repr__(self):
        pass
    


class Control(Base):
    #self.init = initialized state of control
    def __init__(self,**kwargs):
        required = {'parent':'*','Name':str,'ValueType':'*'}
        success,error = required_args(kwargs,required)
        if(success):
            self.__dict__.update(**kwargs)
            self.init = True
            self.state = {}
            self.__cast__()
            self.get(TransId=epoch())
        else:
            init_logger.log(lineno()+"<Control class> __init__() | {}".format(error),5)
            self.init = False

    def get(self,**kwargs):
        required = {'TransId':[int,float]}
        success,error = required_args(kwargs,required)
        if(success):
            return self.send(self.parent.sock,self.parent.logger,method='Control.Get',id=kwargs['TransId'],params=[self.Name])
        else:
            self.parent.logger.log(lineno()+"<Control class> set() - {} | {}".format(self.Name,error),5)
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
            self.parent.logger.log(lineno()+"<Control class> set() - {} | {}".format(self.Name,error),5)
            return False

    def __repr__(self):
        return '<QSYS Control Object | Parent - {} | Name = {}>'.format(self.parent,self.Name)

class Component(Base):
    def __init__(self,**kwargs):
        pass

if __name__ == '__main__':
    core = Core(User='',Password='',ip='192.168.61.2')
    core.start()

    gain = Control(parent=core,Name='gain',ValueType=int)
    changegroup = ChangeGroup(parent=core,Id='mygroup')
    
    time.sleep(2)
    print(gain.state)

    changegroup.add_control(gain)
    changegroup.poll(auto=True,rate=.1)

    while True:
        #val = int(input('Enter Value: '))
        #gain.set(TransId=epoch(),Value=val)
        time.sleep(1)
        #print(gain.state)
