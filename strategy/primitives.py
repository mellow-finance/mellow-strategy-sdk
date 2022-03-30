import math
from enum import Enum
from functools import total_ordering

# TODO different fees to lp holders and swap operation


class Fee(Enum):
    """
    ``Fee`` Enum class defines available fees for UniV3 pools.
    Currently 3 values are available: 0.05%, 0.3%, 1%.
    The actual enum values are fee * 1_000_000, i.e. 0.05% enum value is integer 500.
    """

    LOW = 500
    MIDDLE = 3000
    HIGH = 10000

    @property
    def percent(self) -> float:
        """
        Returns:
            UniswapV3 fee in form of 0.0005, 0.003, 0.01.
        """
        return self.value / 1000000

    @property
    def spacing(self) -> int:
        """
        Returns:
            Tick spacing for this fee 10, 60 or 200
        """
        return SPACING[self]


@total_ordering
class Token(Enum):
    """
    ``Token`` represents one of mainnet tokens and contains some
    additional data line address and decimals.
    This class is ordered according to token address. E.g. :code:`Token.WBTC < Token.USDC`.
    """

    WBTC = "WBTC"
    WETH = "WETH"
    stETH = "stETH"
    USDC = "USDC"
    USDT = "USDT"

    @property
    def address(self) -> str:
        """
        Returns:
            Mainnet address of the token.
        """
        return TOKEN_DETAILS[self.value]["address"]

    @property
    def decimals(self) -> int:
        """
        Returns:
            Decimals of the token.
        """
        return TOKEN_DETAILS[self.value]["decimals"]

    def _is_valid_operand(self, other: 'Token') -> bool:
        """
        Checks if Token is valid.

        Args:
            other: Other Token.

        Returns:
            Valid or not.
        """
        return isinstance(other, Token)

    def __eq__(self, other: 'Token') -> bool:
        """
        Checks if Tokens are equal.

        Args:
            other: Other Token.

        Returns:
            Equal or not.
        """
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: 'Token') -> bool:
        """
        Args:
            other: Other Token.
        """
        if not self._is_valid_operand(other):
            return NotImplemented

        return (
            TOKEN_DETAILS[self.value]["address"].lower()
            < TOKEN_DETAILS[other.value]["address"].lower()
        )


class Pool:
    """
    ``Pool`` represents a mainnet UniV3 pool.

    Attributes:
        tokenA:
            First token of the pool.
        tokenB:
            Second token of the pool.
        fee:
            Pool fee.
    """

    def __init__(self, tokenA: "Token", tokenB: "Token", fee: "Fee"):
        self._token0, self._token1 = tokenA, tokenB
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

    @property
    def decimals_diff(self) -> int:
        """
        Difference between ``token0`` and ``token1`` decimals.
        Used for conversion of price from `wei` to `eth`.

        Returns:
            Decimal difference between Tokens.
        """
        return self._token0.decimals - self._token1.decimals

    @property
    def l_decimals_diff(self) -> float:
        """
        Used for conversion of liquidity from `wei` to `eth`.

        Returns:
            Decimal difference between Tokens in Eth.
        """
        return float(self._token0.decimals + self._token1.decimals) / 2

    @property
    def tick_diff(self) -> int:
        """
        Used for conversion of tick from `wei` to `eth`.

        Returns:
            Tick diff. tick(eth/btc) - tick(wei/satoshi)
        """

        return int(math.floor(self.decimals_diff) * math.log(10, 1.0001))

    @property
    def name(self) -> str:
        """
        Unique name for the pool.

        Returns:
            Pool unique name for the pool.
        """
        return f"{self._token0.value}_{self._token1.value}_{self._fee.value}"

    @property
    def _name(self) -> str:
        """
        Unique name for the pool.

        Returns:
            Pool name.
        """
        return f"{self._token0.value}/{self._token1.value} {100 * self._fee.percent}%"

    @property
    def address(self) -> str:
        """
        Returns:
            Pool mainnet address.
        """
        return self._address

    @property
    def token0(self) -> "Token":
        """
        Returns:
            First token name.
        """
        return self._token0

    @property
    def token1(self) -> "Token":
        """
        Returns:
            Second token name.
        """
        return self._token1

    @property
    def fee(self) -> "Fee":
        """
        Returns:
            Fee of the pool.
        """
        return self._fee


TOKEN_DETAILS = {
    Token.WBTC.value: {
        "name": "WBTC",
        "description": "Wrapped BTC",
        "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "decimals": 8,
    },
    Token.USDC.value: {
        "name": "USDC",
        "description": "USD Coin",
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
    },
    Token.WETH.value: {
        "name": "WETH",
        "description": "Wrapped Ether",
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "decimals": 18,
    },
    Token.stETH.value: {
        "name": "stETH",
        "description": "Staked Ether",
        "address": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        "decimals": 18,
    },
    Token.USDT.value: {
        "name": "USDT",
        "description": "Tether USD",
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
    },
}

POOLS = [
    {
        "address": "0x4585FE77225b41b697C938B018E2Ac67Ac5a20c0",
        "token0": Token.WBTC,
        "token1": Token.WETH,
        "fee": Fee.LOW,
    },
    {
        "address": "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD",
        "token0": Token.WBTC,
        "token1": Token.WETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x6Ab3bba2F41e7eAA262fa5A1A9b3932fA161526F",
        "token0": Token.WBTC,
        "token1": Token.WETH,
        "fee": Fee.HIGH,
    },
    {
        "address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
        "token0": Token.USDC,
        "token1": Token.WETH,
        "fee": Fee.LOW,
    },
    {
        "address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
        "token0": Token.USDC,
        "token1": Token.WETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x7BeA39867e4169DBe237d55C8242a8f2fcDcc387",
        "token0": Token.USDC,
        "token1": Token.WETH,
        "fee": Fee.HIGH,
    },
    {
        "address": "0x7858E59e0C01EA06Df3aF3D20aC7B0003275D4Bf",
        "token0": Token.USDC,
        "token1": Token.USDT,
        "fee": Fee.LOW,
    },
    {
        "address": "0xEe4Cf3b78A74aFfa38C6a926282bCd8B5952818d",
        "token0": Token.USDC,
        "token1": Token.USDT,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0xbb256c2F1B677e27118b0345FD2b3894D2E6D487",
        "token0": Token.USDC,
        "token1": Token.USDT,
        "fee": Fee.HIGH,
    },
]
MIN_TICK = -887272
MAX_TICK = 887272
SPACING = {Fee.LOW: 10, Fee.MIDDLE: 60, Fee.HIGH: 200}
