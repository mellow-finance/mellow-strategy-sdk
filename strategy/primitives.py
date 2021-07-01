from enum import Enum
from functools import total_ordering
from typing import KeysView


class Frequency(Enum):
    BLOCK = "15S"
    MINUTE = "min"
    MINUTE5 = "5min"
    MINUTE15 = "15min"
    HOUR = "H"
    DAY = "D"
    WEEK = "W"
    MONTH = "M"


class Fee(Enum):
    LOW = 500
    MIDDLE = 3000
    HIGH = 10000


@total_ordering
class Token(Enum):
    WBTC = "WBTC"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"

    def address(self):
        return TOKEN_DETAILS[self.value]["address"]

    def _is_valid_operand(self, other):
        return isinstance(other, Token)

    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented

        return (
            TOKEN_DETAILS[self.value]["address"].lower()
            < TOKEN_DETAILS[other.value]["address"].lower()
        )


class Pool:
    def __init__(self, tokenA: Token, tokenB: Token, fee: Fee):
        [self._token0, self._token1] = sorted([tokenA, tokenB])
        self._fee = fee
        self._address = None
        for pool in POOLS:
            if (
                (pool["token0"] == self._token0)
                and (pool["token1"] == self._token1)
                and (pool["fee"] == fee)
            ):
                self._address = pool["address"]
                break
        if not self._address:
            raise KeyError("Pool not found")

    def name(self) -> str:
        return f"{self._token0.value}-{self._token1.value}-{self._fee.value}"

    def address(self) -> str:
        return self._address

    def token0(self) -> Token:
        return self._token0

    def token1(self) -> Token:
        return self._token1

    def fee(self) -> Fee:
        return self._fee


TOKEN_DETAILS = {
    Token.WBTC.value: {
        "name": "WBTC",
        "description": "Wrapped BTC",
        "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    Token.USDC.value: {
        "name": "USDC",
        "description": "USD Coin",
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    },
    Token.WETH.value: {
        "name": "WETH",
        "description": "Wrapped Ether",
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    Token.USDT.value: {
        "name": "USDT",
        "description": "Tether USD",
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    },
}

POOLS = [
    {
        "address": "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD",
        "token0": Token.WBTC,
        "token1": Token.WETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
        "token0": Token.USDC,
        "token1": Token.WETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x7858E59e0C01EA06Df3aF3D20aC7B0003275D4Bf",
        "token0": Token.USDC,
        "token1": Token.USDT,
        "fee": Fee.MIDDLE,
    },
]
