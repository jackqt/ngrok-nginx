#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 建议Python 3.1 以上运行 以下是依赖
# 项目地址: https://github.com/hauntek/python-ngrok
# Version: v1.38
import socket
import select
import ssl
import json
import struct
import random
import sys
import time
import atexit
import logging
import threading
import ConfigParser
import io


config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('../conf/main.cfg')

host = config.get('ngrok', 'host')
port = int(config.get('ngrok', 'port'))
bufsize = int(config.get('ngrok', 'bufsize'))

Tunnels = list() # 全局渠道赋值
body = dict()
body['protocol'] = config.get('ngrok_nginx', 'protocol')
body['hostname'] = config.get('ngrok_nginx', 'hostname')
body['subdomain'] = config.get('ngrok_nginx', 'subdomain')
body['rport'] = int(config.get('ngrok_nginx', 'rport'))
body['lhost'] = config.get('ngrok_nginx', 'localhost')
body['lport'] = int(config.get('ngrok_nginx', 'localport'))
Tunnels.append(body) # 加入渠道队列

mainsocket = 0

ClientId = ''
pingtime = 0

def getloacladdr(Tunnels, Url):
    protocol = Url[0:Url.find(':')]
    hostname = Url[Url.find('//') + 2:]
    subdomain = hostname[0:hostname.find('.')]
    rport = Url[Url.rfind(':') + 1:]

    for tunnelinfo in Tunnels:
        if tunnelinfo.get('protocol') == protocol:
            if tunnelinfo.get('hostname') == hostname:
                return tunnelinfo
            if tunnelinfo.get('subdomain') == subdomain:
                return tunnelinfo
            if tunnelinfo.get('protocol') == 'tcp':
                if tunnelinfo.get('rport') == int(rport):
                    return tunnelinfo

    return dict()

def dnsopen(host):
    try:
        ip = socket.gethostbyname(host)
    except socket.error:
        return False

    return ip

def connectremote(host, port):
    try:
        host = socket.gethostbyname(host)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_client = ssl.wrap_socket(client, ssl_version=ssl.PROTOCOL_SSLv23)
        ssl_client.connect((host, port))
        ssl_client.setblocking(0)
        logger = logging.getLogger('%s:%d' % ('Conn', ssl_client.fileno()))
        logger.debug('New connection to: %s:%d' % (host, port))
    except socket.error:
        return False

    return ssl_client

def connectlocal(localhost, localport):
    try:
        localhost = socket.gethostbyname(localhost)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((localhost, localport))
        client.setblocking(0)
        logger = logging.getLogger('%s:%d' % ('Conn', client.fileno()))
        logger.debug('New connection to: %s:%d' % (localhost, localport))
    except socket.error:
        return False

    return client

def NgrokAuth():
    Payload = dict()
    Payload['ClientId'] = ''
    Payload['OS'] = 'darwin'
    Payload['Arch'] = 'amd64'
    Payload['Version'] = '2'
    Payload['MmVersion'] = '1.7'
    Payload['User'] = 'user'
    Payload['Password'] = ''
    body = dict()
    body['Type'] = 'Auth'
    body['Payload'] = Payload
    buffer = json.dumps(body)
    return(buffer)

def ReqTunnel(Protocol, Hostname, Subdomain, RemotePort):
    Payload = dict()
    Payload['ReqId'] = getRandChar(8)
    Payload['Protocol'] = Protocol
    Payload['Hostname'] = Hostname
    Payload['Subdomain'] = Subdomain
    Payload['HttpAuth'] = ''
    Payload['RemotePort'] = RemotePort
    body = dict()
    body['Type'] = 'ReqTunnel'
    body['Payload'] = Payload
    buffer = json.dumps(body)
    return(buffer)

def RegProxy(ClientId):
    Payload = dict()
    Payload['ClientId'] = ClientId
    body = dict()
    body['Type'] = 'RegProxy'
    body['Payload'] = Payload
    buffer = json.dumps(body)
    return(buffer)

def Ping():
    Payload = dict()
    body = dict()
    body['Type'] = 'Ping'
    body['Payload'] = Payload
    buffer = json.dumps(body)
    return(buffer)

def lentobyte(len):
    xx = struct.pack('I', len)
    xx1 = struct.pack('I', 0)
    return xx + xx1

def sendbuf(sock, buf, isblock = True):
    if isblock:
        sock.setblocking(1)
    sock.send(buf)
    if isblock:
        sock.setblocking(0)

def sendpack(sock, msg, isblock = True):
    if isblock:
        sock.setblocking(1)
    sock.send(lentobyte(len(msg)) + msg.encode('utf-8'))
    logger = logging.getLogger('%s:%d' % ('Send', sock.fileno()))
    logger.debug('Writing message: %s' % msg)
    if isblock:
        sock.setblocking(0)

def tolen(v):
    try:
        return struct.unpack('I', v)[0]
    except:
        return 0

def getRandChar(length):
    _chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.sample(_chars, length))

def main_shutdown():
    global mainsocket
    global pingtime
    if mainsocket == False: return
    if pingtime == False: return
    sendpack(mainsocket, 'close')

# 客户端程序处理过程
def HKClient(sock, linkstate, type, tosock = None):
    global mainsocket
    global ClientId
    global pingtime
    recvbuf = bytes()
    while True:
        inputs = list()
        outputs = list()
        if isinstance(sock, socket.socket):
            inputs.append(sock)
            if linkstate == 0:
                outputs.append(sock)
        else:
            if type == 1:
                mainsocket = False
            logger = logging.getLogger('%s' % 'client')
            logger.error('z:close')

        try:
            readable , writable , exceptional = select.select(inputs, outputs, [], 1)
        except select.error:
            logger = logging.getLogger('%s' % 'client')
            logger.error('select.error')

        # 可读
        if readable:
            try:
                recvbut = sock.recv(bufsize)
                if not recvbut: break

                if len(recvbut) > 0:
                    if not recvbuf:
                        recvbuf = recvbut
                    else:
                        recvbuf += recvbut

                if type == 1 or (type == 2 and linkstate == 1):
                    lenbyte = tolen(recvbuf[0:4])
                    if len(recvbuf) >= (8 + lenbyte):
                        buf = recvbuf[8:].decode('utf-8')
                        logger = logging.getLogger('%s:%d' % ('Recv', sock.fileno()))
                        logger.debug('Reading message with length: %d' % len(buf))
                        logger.debug('Read message: %s' % buf)
                        js = json.loads(buf)
                        if type == 1:
                            if js['Type'] == 'ReqProxy':
                                newsock = connectremote(host, port)
                                if newsock:
                                    thread = threading.Thread(target = HKClient, args = (newsock, 0, 2))
                                    thread.setDaemon(True)
                                    thread.start()
                            if js['Type'] == 'AuthResp':
                                ClientId = js['Payload']['ClientId']
                                logger = logging.getLogger('%s' % 'client')
                                logger.info('Authenticated with server, client id: %s' % ClientId)
                                sendpack(sock, Ping())
                                pingtime = time.time()
                                for tunnelinfo in Tunnels:
                                    # 注册通道
                                    sendpack(sock, ReqTunnel(tunnelinfo['protocol'], tunnelinfo['hostname'], tunnelinfo['subdomain'], tunnelinfo['rport']))
                            if js['Type'] == 'NewTunnel':
                                if js['Payload']['Error'] != '':
                                    logger = logging.getLogger('%s' % 'client')
                                    logger.error('Server failed to allocate tunnel: %s' % js['Payload']['Error'])
                                    time.sleep(30)
                                else:
                                    logger = logging.getLogger('%s' % 'client')
                                    logger.info('Tunnel established at %s' % js['Payload']['Url'])
                        if type == 2:
                            if linkstate == 1:
                                if js['Type'] == 'StartProxy':
                                    loacladdr = getloacladdr(Tunnels, js['Payload']['Url'])

                                    newsock = connectlocal(loacladdr['lhost'], loacladdr['lport'])
                                    if newsock:
                                        thread = threading.Thread(target = HKClient, args = (newsock, 0, 3, sock))
                                        thread.setDaemon(True)
                                        thread.start()
                                        tosock = newsock
                                        linkstate = 2
                                    else:
                                        body = '<html><body style="background-color: #97a8b9"><div style="margin:auto; width:400px;padding: 20px 60px; background-color: #D3D3D3; border: 5px solid maroon;"><h2>Tunnel %s unavailable</h2><p>Unable to initiate connection to <strong>%s</strong>. This port is not yet available for web server.</p>'
                                        html = body % (js['Payload']['Url'], loacladdr['lhost'] + ':' + str(loacladdr['lport']))
                                        header = "HTTP/1.0 502 Bad Gateway" + "\r\n"
                                        header += "Content-Type: text/html" + "\r\n"
                                        header += "Content-Length: %d" + "\r\n"
                                        header += "\r\n" + "%s"
                                        buf = header % (len(html), html)
                                        sendbuf(sock, buf.encode('utf-8'))

                        if len(recvbuf) == (8 + lenbyte):
                            recvbuf = bytes()
                        else:
                            recvbuf = recvbuf[8 + lenbyte:]

                if type == 3 or (type == 2 and linkstate == 2):
                    sendbuf(tosock, recvbuf)
                    recvbuf = bytes()

            except socket.error:
                # logger = logging.getLogger('%s' % 'client')
                # logger.error('socket.error')
                break

        # 可写
        if writable:
            try:
                if linkstate == 0:
                    if type == 1:
                        sendpack(sock, NgrokAuth(), False)
                        linkstate = 1
                    if type == 2:
                        sendpack(sock, RegProxy(ClientId), False)
                        linkstate = 1
                    if type == 3:
                        linkstate = 1

            except socket.error:
                # logger = logging.getLogger('%s' % 'client')
                # logger.error('socket.error')
                break

    if type == 1:
        mainsocket = False
    if type == 3:
        if tosock.fileno() != -1:
            tosock.shutdown(socket.SHUT_WR)

    logger = logging.getLogger('%s:%d' % ('Close', sock.fileno()))
    logger.debug('Closing')
    sock.close()

# 客户端程序初始化
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(levelname)s:%(lineno)d] [%(name)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    # 注册退出回调函数
    atexit.register(main_shutdown)
    while True:
        try:
            # 检测控制连接是否连接.
            if mainsocket == False:
                ip = dnsopen(host)
                if ip == False:
                    logging.info('update dns')
                    time.sleep(10)
                    continue
                mainsocket = connectremote(ip, port)
                if mainsocket == False:
                    logging.info('connect failed...!')
                    time.sleep(10)
                    continue
                thread = threading.Thread(target = HKClient, args = (mainsocket, 0, 1))
                thread.setDaemon(True)
                thread.start()

            # 发送心跳
            if pingtime + 20 < time.time() and pingtime != 0:
                sendpack(mainsocket, Ping())
                pingtime = time.time()

            time.sleep(1)

        # 捕获心跳异常信号
        except socket.error:
            pingtime = 0
        # 捕获中断异常信号
        except KeyboardInterrupt:
            sys.exit()
