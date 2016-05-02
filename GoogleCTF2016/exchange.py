import exchange_pb2
import time
import connection
import hashlib
import pymd5, sys

reload(sys)
sys.setdefaultencoding("windows-1252")

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



def calcPass(user, realm, password, method, uri, nonce, nonceCount, cnonce):
    ha1 = hashlib.md5(user+':'+realm+':'+password).hexdigest()
    ha2 = hashlib.md5(method+':'+uri).hexdigest()
    return hashlib.md5(ha1+':'+nonce+':'+nonceCount+':'+cnonce+':auth:'+ha2).hexdigest()

def md5_padding(st, block_num):
    st = st.encode('windows-1252')
    ori_len = 512*block_num + len(st)*8
    st += "\x80"
    assert len(st) < 56
    while len(st) != 56:
        st += '\x00'
    st += l32(ori_len)
    st += l32(0)
    return st
    
def md5(st):
    return hashlib.md5(st).hexdigest()
    
def md5_append_last_block(md5str, ori, oriblocknum):
    ori = md5_padding(ori, oriblocknum)

    a = unl32(md5str[:8].decode('hex'))
    b = unl32(md5str[8:16].decode('hex'))
    c = unl32(md5str[16:24].decode('hex'))
    d = unl32(md5str[24:32].decode('hex'))
    
    md5obj = pymd5.md5()
    md5obj.state =(a, b, c, d)
    md5obj.update(ori)
    return md5obj.final(False).encode('hex')

def pure_md5(s):
    md5obj = pymd5.md5()
    md5obj.update(s)
    return md5obj.final(False).encode('hex')
    
'''
md5obj = pymd5.md5()
md5obj.update('a'*64)
md5obj.update(md5_padding('aaaaa'))
print md5obj.final(False).encode('hex')
print md5('a'*64+'aaaaa')
exit()
'''
assert md5_append_last_block(md5('a'*64+'abc'), 'c', 2) == md5('a'*64+md5_padding('abc', 1)+'c')

proxy = None
conn = connection.Connection(('ssl-added-and-removed-here.ctfcompetition.com', 12001), proxy, True)
    
req_ex = recv_protobuf(conn)
req_ex.request.uri = '/protected/secret'
send_protobuf(conn, req_ex)
print req_ex
    
reply_ex = recv_protobuf(conn)
nonce = reply_ex.reply.headers[1].value[reply_ex.reply.headers[1].value.find('nonce="')+7:]
nonce = nonce[:nonce.find('"')]
send_protobuf(conn, reply_ex)
print reply_ex

req_ex = recv_protobuf(conn)
response = req_ex.request.headers[0].value[req_ex.request.headers[0].value.find('response="')+10:]
response = response[:response.find('"')]
cnonce = req_ex.request.headers[0].value[req_ex.request.headers[0].value.find('cnonce="')+8:]
cnonce = cnonce[:cnonce.find('"')]
nc = req_ex.request.headers[0].value[req_ex.request.headers[0].value.find('nc=')+3:]
nc = nc[:nc.find(',')]

ha1 = md5("Mufasa:testrealm@host.com:Circle Of Life")

inner = ha1+':%s:%s:%s:auth:%s' % (nonce, nc, cnonce, md5('GET:/protected/joke'))
assert md5(inner) == calcPass("Mufasa", "testrealm@host.com", "Circle Of Life", "GET", "/protected/joke", nonce, nc, cnonce)

cn2 = inner[64:]
cn1 = cnonce[:cnonce.find(cn2[:cn2.find(':')])]

print cn1, cn2

new_tail = ':auth:'+md5('GET:/protected/token')
assert md5_append_last_block(md5(inner), new_tail, 2) == md5(inner[:64]+md5_padding(cn2, 1)+new_tail)
assert md5(inner) == pure_md5(inner[:64]+md5_padding(cn2, 1))
new_response = md5_append_last_block(response, new_tail, 2)
new_cnonce = cn1+md5_padding(cn2, 1)

new_inner = ha1+(':%s:%s:%s' % (nonce, nc, new_cnonce))+new_tail
assert md5_append_last_block(md5(inner), new_tail, 2) == calcPass("Mufasa", "testrealm@host.com", "Circle Of Life", "GET", "/protected/token", nonce, nc, new_cnonce) == md5(new_inner)

req_ex.request.headers[0].value = req_ex.request.headers[0].value.decode('utf-8')
req_ex.request.headers[0].value = req_ex.request.headers[0].value.encode('windows-1252').replace(cnonce, new_cnonce).replace(response, new_response).replace('/joke', '/token')

req_ex.request.uri = '/protected/token'

send_protobuf(conn, req_ex)
print req_ex, req_ex.request.headers[0].value.encode('hex')
thru_protobuf(conn, True)

