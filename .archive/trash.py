def old_test():
    core = Core(User='',Password='',ip='192.168.61.2')
    core.start()

    #gain = Control(parent=core,Name='gain',ValueType=int)
    
    cg = ChangeGroup(parent=core,Id='mygroup')

    #create some control objects
    for i in range(1,10):
        l = Control(parent=core,Name='Mixer6x9Output{}Label'.format(i),ValueType=str)
        cg.AddControl(l)
        m = Control(parent=core,Name='Mixer6x9Output{}Mute'.format(i),ValueType=[int,float])
        cg.AddControl(m)
        g = Control(parent=core,Name='Mixer6x9Output{}Gain'.format(i),ValueType=[int,float])
        cg.AddControl(g)
        print(l,m,g)

    time.sleep(2)

    cg.AutoPoll(Rate=.1)

    while True:
        x = str(input("Control Name: "))
        if(x):
            try:
                print(core.Objects[x].state)
            except:
                print("fail")
