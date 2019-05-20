<?php

function a($q, $y, $z, $p, $e, $k) {
	var_dump($q, $y, $z, $p, $e, $k);
	return (((($z >> 5) & 134217727) ^ ($y << 2))+((($y >> 3) & 536870911) ^ ($z << 4)))^(($q ^ $y)+($k[($e ^ ($p & 3))] ^ $z));
}

function verify($str) {
	$v = unpack("V\x2a", $str.str_repeat("\0", (4-(strlen($str)%4))&3));
	$v = array_values($v);
	$v[count($v)]=strlen($str);
	$k = [1752186684,1600069744,1953259880,1836016479];
	$b = [1029560848,2323109303,4208702724,3423862500,3597800709,2222997091,4137082249,2050017171,4045896598];
	$n = COUNT($v)-1;
	$z = $v[COUNT($v)-1];
	$q = floor(52/COUNT($v)+6);
	var_dump($v);
	for($sum=0; 0 < $q; $q--) {  

		$sum = ($sum + 2654435769) & 0xffffffff;
		$e = ($sum >> 2) & 3;
		for ($p=0; $p<$n; $p++) {
			$z = $v[$p] = ((a($sum, $v[$p+1], $z, $p, $e, $k)+$v[$p]) & 0xffffffff);
		}
		//if ($q==1) break;
		$z = $v[$n] = ($v[$n] + a($sum, $v[0], $z, $p, $e, $k)) & 0xffffffff;
	}
	for($i=0;$i<count($v);$i++) {
		$v[$i] = $v[$i] ^ $k[$i%4];
	}
	var_dump('final',$v);
	return $v == $b;
}

//verify('FLAG_HERE');
reverse();

function reverse() {
	$v = $b = [1029560848,2323109303,4208702724,3423862500,3597800709,2222997091,4137082249,2050017171,4045896598];
	//$v = [3083636581,361734860,1305231159,4060754200];
	$k = [1752186684,1600069744,1953259880,1836016479];
	
	for($i=0;$i<count($v);$i++) {
		$v[$i] = $v[$i] ^ $k[$i%4];
	}
	$n = COUNT($v)-1;
	
	// calc $sum
	$q = floor(52/COUNT($v)+6);
	for($sum=0; 0 < $q; $q--) {  
		$sum = ($sum + 2654435769) & 0xffffffff;
	}
	
	$end_q = floor(52/COUNT($v)+6);
	for($q = 1; ; $q++) {
		$e = ($sum >> 2) & 3;
		
		$v[$n] = ($v[$n] - a($sum, $v[0], $v[$n-1], $n, $e, $k)) & 0xffffffff;
		
		for ($p = $n-1; $p != 0; $p--) {
			$v[$p] = ($v[$p] - a($sum, $v[$p+1], $v[$p-1], $p, $e, $k)) & 0xffffffff;
		}
		if ($q == $end_q) $z = $v[COUNT($v)-1]; else $z = $v[$n];
		$v[$p] = ($v[$p] - a($sum, $v[$p+1], $z, $p, $e, $k)) & 0xffffffff;
		
		$sum = ($sum - 2654435769) & 0xffffffff;
		$e = ($sum >> 2) & 3;
		if ($q == $end_q) break;
	}
	assert($sum == 0);
	//var_dump($v);
	$ret = '';
	for ($i=0; $i < count($v)-1; $i++) {
		$ret .= pack('V',$v[$i]);
	}
	echo ($ret);
}