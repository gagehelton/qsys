import time
from inspect import currentframe,getframeinfo

def required_args(passed,required):
    for arg in required:
        if(arg not in passed):
            return False,'missing {}'.format(arg)
        elif(isinstance(required[arg],list)): #for multi type arguments pass a list of types - [int,float] or [str,dict]
            if(not type(passed[arg]) in required[arg]):
                return False,'{} type is {} - it should be {}'.format(arg,type(passed[arg]),required[arg])
        elif(required[arg] != '*' and not isinstance(passed[arg],required[arg])):
            return False,'{} type is {} - it should be {}'.format(arg,type(passed[arg]),required[arg])
    return True,''

def lineno(): #get line number for logging
    cf = currentframe()
    return str(cf.f_back.f_lineno)+" "

def epoch():
    return float(time.time())