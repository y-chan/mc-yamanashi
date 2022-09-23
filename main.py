from config import genesis_bits, genesis_message, address_base_bytes
from mining import create_genesis_block, create_block, mining_block
from address import hash160_to_b58_address
from block import load_blockchain, dump_blockchain
from util import hash160, now_unixtime

# 本来は公開鍵を用いて算出するが、送金等は行わない前提なので、適当な文字列のハッシュをアドレスとして使う
address = hash160_to_b58_address(hash160(address_base_bytes))
print("Your Address:", address)

try:
    blockchain = load_blockchain()
except FileNotFoundError:
    # ブロックチェーンファイル(blockchain.json)が存在しない場合、新しく生成する
    genesis_block = create_genesis_block(now_unixtime(), address)
    genesis_block = mining_block(0, genesis_block)
    blockchain = [genesis_block]

height = len(blockchain)
try:
    while True:
        new_block = create_block(blockchain, address)
        new_block = mining_block(height, new_block)
        print(f"New Block Found! Height: {height} Hash: {new_block.block_hash()[::-1].hex()}")
        blockchain.append(new_block)
        height += 1
except KeyboardInterrupt:
    dump_blockchain(blockchain)
