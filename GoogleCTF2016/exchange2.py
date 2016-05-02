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
    

proxy = None
conn = connection.Connection(('ssl-added-and-removed-here.ctfcompetition.com', 20691), proxy, True)

ex = recv_protobuf(conn)
send_protobuf(conn, ex)

ex = recv_protobuf(conn)
ex.reply.headers[1].value = 'Basic realm="In the realm of hackers"'
send_protobuf(conn, ex)

ex = recv_protobuf(conn)
cred = ex.request.headers[0].value.replace('Basic ', '').decode('base64').split(':')
ex.request.uri = '/protected/secret'
send_protobuf(conn, ex)

def calcPass(user, realm, password, method, uri, nonce, nonceCount, cnonce):
    ha1 = hashlib.md5(user+':'+realm+':'+password).hexdigest()
    ha2 = hashlib.md5(method+':'+uri).hexdigest()
    return hashlib.md5(ha1+':'+nonce+':'+nonceCount+':'+cnonce+':auth:'+ha2).hexdigest()
    
assert calcPass("Mufasa", "testrealm@host.com", "Circle Of Life", "GET", "/dir/index.html", "dcd98b7102dd2f0e8b11d0f600bfb0c093", "00000001", "0a4f113b") == "6629fae49393a05397450978507c4ef1"

reply_ex = recv_protobuf(conn)
print reply_ex
auth = reply_ex.reply.headers[1].value

opaque = auth[auth.find('opaque="')+8:]
opaque = opaque[:opaque.find('"')]
nonce = auth[auth.find('nonce="')+7:]
nonce = nonce[:nonce.find('"')]
nc = "00000002"*9
cnonce = "0a4f113b"*9
response = calcPass(cred[0], 'In the realm of hackers', cred[1], 'GET', ex.request.uri, nonce, nc, cnonce)

ex.request.headers[0].value = 'Digest username="%s",realm="%s",nonce="%s",uri="%s",qop=auth,nc=%s,cnonce="%s",response="%s",opaque="%s"' % (cred[0], 'In the realm of hackers', nonce, ex.request.uri, nc, cnonce, response, opaque)
send_protobuf(conn, ex)

print recv_protobuf(conn)