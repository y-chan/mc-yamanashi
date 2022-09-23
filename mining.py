import binascii

from typing import List


from block import Block
from tx import Tx, TxIn, OutPoint, TxOut
from config import retarget_block_count, retarget_time_span, min_bits, miner_name, genesis_message, genesis_bits
from script import script_int_to_bytes, script_int_to_bytes_contain_opcode
from address import address_to_script


def bits_to_target(bits: int) -> int:
    bitsN = (bits >> 24) & 0xff
    if not (0x03 <= bitsN <= 0x1f):
        raise Exception("First part of bits should be in [0x03, 0x1f]")
    bitsBase = bits & 0xffffff
    if not (0x8000 <= bitsBase <= 0x7fffff):
        raise Exception("Second part of bits should be in [0x8000, 0x7fffff]")
    return bitsBase << (8 * (bitsN-3))


def target_to_bits(target: int) -> int:
    c = ("%064x" % target)[2:]
    while c[:2] == '00' and len(c) > 6:
        c = c[2:]
    bitsN, bitsBase = len(c) // 2, int.from_bytes(bytes.fromhex(c[:6]), byteorder='big')
    if bitsBase >= 0x800000:
        bitsN += 1
        bitsBase >>= 8
    return bitsN << 24 | bitsBase


def get_bits(blocks: List[Block]) -> int:
    """
    Bitcoinの場合、マイニング難易度の調整は2016ブロックに一回行われている。

    難易度変更条件は、2016ブロック生成されるまでにどのくらい時間がかかっているかを見て、指定された時間より長ければ難易度を落とし、
    指定された時間よりも短ければ難易度を上げる
    """
    if len(blocks) % retarget_block_count == 0:
        first = blocks[-(retarget_block_count-1)]
        last = blocks[-1]
        target = bits_to_target(last.bits)
        n_actual_timespan = last.time - first.time
        n_actual_timespan = max(n_actual_timespan, retarget_time_span // 4)
        n_actual_timespan = min(n_actual_timespan, retarget_time_span * 4)
        new_target = min(bits_to_target(min_bits), (target * n_actual_timespan) // retarget_time_span)
    else:
        return blocks[-1].bits

    new_target = target_to_bits(new_target)
    print("Retarget:", bits_to_target(new_target).to_bytes(32, "big").hex(), "bits:", new_target.to_bytes(4, "big").hex())
    return new_target


def create_genesis_block(time: int, receive_address: str) -> Block:
    """
    ジェネシスブロック(= ブロックチェーンの始まりのブロック)を生成する。
    Bitcoinの場合、ジェネシスブロックにはメッセージ(ジェネシスメッセージと呼ばれる)が混入され、誰でも閲覧可能になっている。
    ここではジェネシスメッセージを msg 変数で定義する。(なお、ASCIIでエンコードされて混入されるので、英数字のみで構成される必要がある)
    versionは適当な値でよいのだが、Bitcoinでは"1"が用いられるため、そのまま利用する。
    ジェネシスブロックのTxInのScriptSigにマイニングの難易度を表すBitsの初期値(0x1d00ffff)とジェネシスメッセージを仕込むが、
    Bitsの初期値を0x1d00ffffに設定するとハッシュの探索に時間がかかりすぎるので、0x1f00ffffを渡してあげるのがオススメ
    """

    # とりあえずジェネシスメッセージを含んだジェネシストランザクションを生成
    msg = genesis_message
    first_bits = genesis_bits.to_bytes(4, "little")  # リトルエンディアンで格納されるため
    # script_sigの生成
    script_sig = (
        len(first_bits).to_bytes(1, "little") +  # 文字列(何かしらの数値も含む)を入れるときはまず長さを入れる
        first_bits +  # bitsを挿入
        b"\x01\x04" +  # Bitcoinではなぜか"4"という数字が文字列として挿入されているため、それに従い長さと文字列本体を挿入
        script_int_to_bytes(
            len(msg)  # ジェネシスメッセージの長さを挿入。Bitcoin Scriptに従い、0x4d以上の長さであれば大きさに応じてPUSHDATAが付与される
        ) +
        msg.encode("ascii")  # メッセージそのものを挿入
    )

    # script pubkeyの生成
    script_pubkey = address_to_script(receive_address)

    genesis_tx = create_coinbase_tx(script_sig, script_pubkey, 0)

    # 一旦ブロックを作る(nonceは0を設定)
    """ジェネシスブロックの中身を埋めてください！"""
    block = Block()

    # マイニングに移行
    return mining_block(0, block)


def create_coinbase_tx(script_sig: bytes, script_pubkey: bytes, reward: int = 50 * 10 ** 9) -> Tx:
    """tx_inと、tx_inに使うoutpointの引数を埋めましょう！"""
    outpoint = OutPoint()
    tx_in = TxIn()
    tx_out = TxOut(
        value=reward,  # マイニング報酬は設定値をそのまま代入
        script_pubkey=script_pubkey
    )
    coinbase_tx = Tx(
        version=1,  # 現在BitcoinにTxのVersionは1と2があるが、特別な機能(=SegWit等)を使わない限り1でよい
        tx_ins=[tx_in],  # tx_inをリストにして代入
        tx_outs=[tx_out],  # tx_inと一緒
        locktime=0  # locktimeは特に必要がないので0を代入
    )

    return coinbase_tx


def create_block(blockchain: List[Block], receive_address: str) -> Block:
    coinbase_tx = create_coinbase_tx(
        script_sig=script_int_to_bytes(
            len(miner_name)  # マイナーの名前の長さ。Bitcoin Scriptに従い、0x4d以上の長さであれば大きさに応じてPUSHDATAが付与される
        ) +
        miner_name.encode("utf-8"),  # マイナーの名前を挿入"
        script_pubkey=address_to_script(receive_address)
    )
    assert len(blockchain) > 0

    # 一旦ブロックを作る(nonceは0を設定)
    """マイニングするブロックの中身を埋めてください！"""
    block = Block()

    return block


def mining_block(height: int, block: Block, extra_nonce: int = 0) -> Block:
    # bitsは32bytesのバイト列に変換され、さらにintのtargetに変換されて使用される。使用方法は後程
    target = bits_to_target(block.bits)

    nonce_found = False

    # extra nonceが設定されている時、coinbase txとmerkle rootを更新する
    if extra_nonce != 0:
        script_sig = script_int_to_bytes(
            len(miner_name)
        ) + miner_name.encode("utf-8") + script_int_to_bytes_contain_opcode(extra_nonce)
        """
        ここにコードを挿入
        """

    for i in range(0, 0xffffffff):
        # マイニングとは、生成するブロックのハッシュがあらかじめ設定されたtargetよりも小さくなるようなnonceを探すことである。
        # というわけで、全探索的にnonceを探す。
        block.nonce = i  # nonceを設定
        block_hash = int.from_bytes(block.block_hash(), "little")  # ブロックのハッシュをintに直す
        # targetとblock_hashを比較し、targetがblock_hash以下であれば、マイニング成功(=ブロック生成成功)
        if target > block_hash:
            print(f"nonce found! nonce = {block.nonce}, extra nonce = {extra_nonce}", "block hash = 0x%064x" % block_hash)
            nonce_found = True
            break

    # 万が一探索しきっても見つからなければ、extra nonceを加算して再探索する
    if not nonce_found:
        return mining_block(height, block, extra_nonce + 1)
    return block
