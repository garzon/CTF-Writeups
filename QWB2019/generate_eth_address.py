from web3 import Web3, HTTPProvider
import rlp
from rlp.utils import decode_hex, encode_hex, ascii_chr, str_to_bytes
w3 = Web3(HTTPProvider('https://ropsten.infura.io/SdO4U3ydQdgK3D3eNE2Y'))
w3.eth.enable_unaudited_features()

def normalize_address(x, allow_blank=False):
    if allow_blank and x == '':
        return ''
    if len(x) in (42, 50) and x[:2] == '0x':
        x = x[2:]
    if len(x) in (40, 48):
        x = decode_hex(x)
    if len(x) == 24:
        assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
        x = x[:20]
    if len(x) != 20:
        raise Exception("Invalid address format: %r" % x)
    return x

def get_deployed_contract_addr(acc_address, nonce):
	return Web3.toHex(Web3.sha3(rlp.encode([normalize_address(acc_address), nonce]))[12:])[2:]

acc=w3.eth.account.create()
while not get_deployed_contract_addr(acc.address, 0).endswith('b1b1'): 
	acc = w3.eth.account.create()
print(acc.privateKey.__repr__())