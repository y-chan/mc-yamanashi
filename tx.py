import binascii

from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, TypedDict

from util import sha256d


class OutPointDict(TypedDict):
    tx_hash: bytes
    index: int


class TxInDict(TypedDict):
    outpoint: OutPointDict
    script_sig: bytes
    sequence: int


class TxOutDict(TypedDict):
    value: int
    script_pubkey: bytes


class TxDict(TypedDict):
    version: int
    tx_ins: List[TxInDict]
    tx_outs: List[TxOutDict]
    locktime: int


@dataclass
class OutPoint:
    tx_hash: bytes
    index: int

    @classmethod
    def from_dict(cls, op_data: OutPointDict) -> "OutPoint":
        shaped_data = {}

        data_list: List[Tuple[str, type]] = [
            ("tx_hash", str),
            ("index", int)
        ]

        for data in data_list:
            one_of_block_data = op_data.get(data[0])
            shaped_data[data[0]] = one_of_block_data
            if one_of_block_data is not None and data[1] == str:
                shaped_data[data[0]] = binascii.a2b_hex(one_of_block_data)

        return cls(**shaped_data)

    def as_dict(self) -> OutPointDict:
        result = asdict(self)
        result["tx_hash"] = result["tx_hash"].hex()
        return result

    def as_hex(self) -> str:
        return self.as_bin().hex()

    def as_bin(self) -> bytes:
        """
        OutPointはその通貨をたどるために使われる情報。どの取引でその通貨が自分のアドレスに入ってきたかを示す値になる。
        なお、マイニングで生成された場合はtx_hashが32bytes分の0で埋められる。
        """
        outpoint_bin = self.tx_hash[::-1]
        outpoint_bin += self.index.to_bytes(4, "little")
        return outpoint_bin


@dataclass
class TxIn:
    outpoint: OutPoint
    script_sig: bytes
    sequence: int

    @classmethod
    def from_dict(cls, tx_in_data: TxInDict) -> "TxIn":
        shaped_data = {}

        data_list: List[Tuple[str, type]] = [
            ("outpoint", dict),
            ("script_sig", str),
            ("sequence", int)
        ]

        for data in data_list:
            one_of_block_data = tx_in_data.get(data[0])
            shaped_data[data[0]] = one_of_block_data
            if one_of_block_data is not None and data[1] == str:
                shaped_data[data[0]] = binascii.a2b_hex(one_of_block_data)
            elif data[0] == "outpoint":
                shaped_data[data[0]] = OutPoint.from_dict(one_of_block_data)

        return cls(**shaped_data)

    def as_dict(self) -> TxInDict:
        result = asdict(self)
        result["outpoint"] = self.outpoint.as_dict()
        result["script_sig"] = result["script_sig"].hex()
        return result

    def as_hex(self) -> str:
        return self.as_bin().hex()

    def as_bin(self) -> bytes:
        """
        TxInはOutPoint、ScriptSig(Signatureの略)、Sequenceの3つの要素で成り立つ。
        OutPointの詳細はOutPoint Classを参照。
        ScriptSigはOutPointでたどられた通貨を所有していることを証明するための、秘密鍵による署名が入ることが一般的。
        SequenceはCSV(Check Sequence Verify)に使われる。
        """
        tx_in_bin = self.outpoint.as_bin()
        tx_in_bin += len(self.script_sig).to_bytes(1, "little")
        tx_in_bin += self.script_sig
        tx_in_bin += self.sequence.to_bytes(4, "little")
        return tx_in_bin


@dataclass
class TxOut:
    value: int
    script_pubkey: bytes

    @classmethod
    def from_dict(cls, tx_out_data: TxOutDict) -> "TxOut":
        shaped_data = {}

        data_list: List[Tuple[str, type]] = [
            ("value", int),
            ("script_pubkey", str)
        ]

        for data in data_list:
            one_of_block_data = tx_out_data.get(data[0])
            shaped_data[data[0]] = one_of_block_data
            if one_of_block_data is not None and data[1] == str:
                shaped_data[data[0]] = binascii.a2b_hex(one_of_block_data)

        return cls(**shaped_data)

    def as_dict(self) -> TxOutDict:
        result = asdict(self)
        result["script_pubkey"] = result["script_pubkey"].hex()
        return result

    def as_hex(self) -> str:
        return self.as_bin().hex()

    def as_bin(self) -> bytes:
        """
        TxOutはValue、ScriptPubKeyの2つの要素で成り立つ。
        Valueは送金価格を表し、最小単位で示される。
        ScriptPubKeyは送金のためのスクリプトが記述される。(Bitcoin Scriptが用いられるが、複雑なため省略)
        """
        tx_out_bin = self.value.to_bytes(8, "little")
        tx_out_bin += len(self.script_pubkey).to_bytes(1, "little")
        tx_out_bin += self.script_pubkey
        return tx_out_bin


@dataclass
class Tx:
    version: int
    tx_ins: List[TxIn]
    tx_outs: List[TxOut]
    locktime: int

    @classmethod
    def from_dict(cls, tx_data: TxDict) -> "Tx":
        shaped_data = {}

        data_list: List[Tuple[str, type]] = [
            ("version", int),
            ("tx_ins", list),
            ("tx_outs", list),
            ("locktime", int)
        ]

        for data in data_list:
            one_of_block_data = tx_data.get(data[0])
            shaped_data[data[0]] = one_of_block_data
            if one_of_block_data is not None and data[1] == str:
                shaped_data[data[0]] = binascii.a2b_hex(one_of_block_data)
            elif one_of_block_data is not None and data[1] == list:
                shaped_data[data[0]] = []
                if data[0] == "tx_ins":
                    for tx_in in one_of_block_data:
                        shaped_data[data[0]].append(TxIn.from_dict(tx_in))
                if data[0] == "tx_outs":
                    for tx_out in one_of_block_data:
                        shaped_data[data[0]].append(TxOut.from_dict(tx_out))

        return cls(**shaped_data)

    def as_dict(self) -> TxDict:
        result = asdict(self)
        result["tx_ins"] = [tx_in.as_dict() for tx_in in self.tx_ins]
        result["tx_outs"] = [tx_out.as_dict() for tx_out in self.tx_outs]
        return result

    def as_hex(self) -> str:
        return self.as_bin().hex()

    def as_bin(self) -> bytes:
        tx_bin = self.version.to_bytes(4, "little")
        tx_bin += len(self.tx_ins).to_bytes(1, "little")
        for tx_in in self.tx_ins:
            tx_bin += tx_in.as_bin()
        tx_bin += len(self.tx_outs).to_bytes(1, "little")
        for tx_out in self.tx_outs:
            tx_bin += tx_out.as_bin()
        tx_bin += self.locktime.to_bytes(4, "little")

        return tx_bin

    def tx_hash(self) -> bytes:
        tx_bin = self.as_bin()
        return sha256d(tx_bin)

