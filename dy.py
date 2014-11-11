import socket
import time
import random
import threading


g_rid= b'5275'
g_username= b'visitor42'
g_ip= b'danmu.douyutv.com'
g_port= 8601
g_gid= b'0'
g_exit= False

def cast_wetght(g):
    g= int(g)
    if g>1e6:
        return str(round(g/1e6,2))+'t'
    elif g>1e3:
        return str(round(g/1e3,2))+'kg'
    else:
        return str(g)+'g'

def sendmsg(s,msg,code=689):
    data_length= len(msg)+8
    s.send(int.to_bytes(data_length,4,'little'))
    s.send(int.to_bytes(data_length,4,'little'))
    s.send(int.to_bytes(code,4,'little'))
    sent=0
    while sent<len(msg):
        tn= s.send(msg[sent:])
        sent= sent + tn

def recvmsg(s):
    bdata_length= s.recv(12)
    data_length= int.from_bytes(bdata_length[:4],'little')-8
    if data_length<=0:
        print('badlength',bdata_length)
        return None
    total_data=[]
    while True:
        msg= s.recv(data_length)
        if not msg: break
        data_length= data_length - len(msg)
        total_data.append(msg)
    ret= b''.join(total_data)
    return ret

def unpackage(data):
    ret={}
    lines= data.split(b'/')
    lines.pop() # pop b''
    for line in lines:
        kv= line.split(b'@=')
        if len(kv)==2:
            ret[kv[0]]= kv[1].replace(b'@S',b'/').replace(b'@A',b'@')
        else:
            ret[len(ret)]= kv[0].replace(b'@S',b'/').replace(b'@A',b'@')

    return ret

def unpackage_list(l):
    ret=[]
    lines= l.split(b'@S')
    for line in lines:
        line= line.replace(b'@AA',b'')
        mp= line.split(b'@AS')
        tb={}
        for kv in mp:
            try:
                k,v= kv.split(b'=')
                tb[k]=v
            except:
                pass
        ret.append(tb)
    return ret

def get_longinres():
    global g_rid
    global g_username
    global g_ip
    global g_port
    global g_gid

    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('117.79.132.20',8001))

    sendmsg(s,b'type@=loginreq/username@=/password@=/roomid@='+g_rid+b'/\x00')

    print('==========longinres')
    longinres= unpackage(recvmsg(s))
    g_username= longinres[b'username']
    print('username= ',longinres[b'username'])

    print('==========msgrepeaterlist')
    msgrepeaterlist= unpackage(recvmsg(s))
    lst= unpackage(msgrepeaterlist[b'list'])
    tb= unpackage(random.choice(tuple(lst.values())))
    g_ip= tb[b'ip']
    g_port= tb[b'port']
    print(tb[b'ip'],tb[b'port'],tb[b'id'])

    print('==========setmsggroup')
    setmsggroup= unpackage(recvmsg(s))
    g_gid= setmsggroup[b'gid']
    print('gid=', setmsggroup[b'gid'])

    def keepalive_send():
        global g_exit
        while not g_exit:
            sendmsg(s,b'type@=keeplive/tick@='+str(random.randint(1,99)).encode('ascii')+b'/\x00')
            time.sleep(45)
        s.close()
    threading.Thread(target=keepalive_send).start()
    def keepalive_recv():
        global g_exit
        while not g_exit:
            bmsg= recvmsg(s)
            print('*** usr alive:',unpackage(bmsg),'***')
        s.close()
    threading.Thread(target=keepalive_recv).start()

def get_danmu():
    print('==========danmu')
    global g_rid
    global g_username
    global g_ip
    global g_port
    global g_gid

    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((g_ip,int(g_port)))
    sendmsg(s,b'type@=loginreq/username@='+g_username+b'/password@=1234567890123456/roomid@='+g_rid+b'/\x00')
    loginres= unpackage(recvmsg(s))
    sendmsg(s,b'type@=joingroup/rid@='+g_rid+b'/gid@='+g_gid+b'/\x00')

    def keepalive():
        global g_exit
        print('==========keepalive')
        while not g_exit:
            sendmsg(s,b'type@=keeplive/tick@='+str(random.randint(1,99)).encode('ascii')+b'/\x00')
            time.sleep(45)
        s.close()
    threading.Thread(target=keepalive).start()

    global g_exit
    while True:
        bmsg= recvmsg(s)
        if not bmsg:
            print('*** connection break ***')
            g_exit= True
            break
        msg= unpackage(bmsg)
        msgtype= msg.get(b'type',b'undefined')

        if msgtype==b'chatmessage':
                nick= msg[b'snick'].decode('utf8')
                content= msg.get(b'content',b'undefined').decode('utf8')
                print(nick, ': ', content)
        elif msgtype==b'donateres':
            sui= unpackage(msg.get(b'sui',b'nick@=undifined//00'))
            nick= sui[b'nick'].decode('utf8')
            print('***', nick, '送给主播', int(msg[b'ms']),\
                  '个鱼丸 (', cast_wetght(msg[b'dst_weight']), ') ***')
        elif msgtype==b'keeplive':
            print('*** dm alive:',msg,'***')
        elif msgtype in (b'userenter'):
            pass
        else:
            print(msg)
            

get_longinres()
get_danmu()
