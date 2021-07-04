from enum import Enum
from functools import total_ordering


class Frequency(Enum):
    """
    ``Frequency`` defines the sampling frequency for the data.
    It is helpful if you want your time series to be split into equal intervals and you want to define interval width.

    Values:

    - `MINUTE` - One minute
    - `MINUTE5` - 5 minutes
    - `MINUTE15` - 15 minutes
    - `HOUR` - 1 hour
    - `DAY` - 1 day
    - `WEEK` - 1 week
    - `MONTH` - 1 month
    """

    MINUTE = "min"
    MINUTE5 = "5min"
    MINUTE15 = "15min"
    HOUR = "H"
    DAY = "D"
    WEEK = "W"
    MONTH = "M"


class Fee(Enum):
    """
    ``Fee`` defines available fees for UniV3 pools. Currently 3 values are available: 0.05%, 0.3%, 1%.
    The actual enum values are fee * 100_000, i.e. 0.05% enum value is integer 500

    Values:

    - `LOW` - 500
    - `MIDDLE` - 3000
    - `HIGH` - 10000
    """

    LOW = 500
    MIDDLE = 3000
    HIGH = 10000

    @property
    def percent(self) -> float:
        """
        The actual uniswap percentage fee, i.e. 0.05%, 0.3% or 1%.
        """
        return self.value / 100000


@total_ordering
class Token(Enum):
    """
    ``Token`` represents a specific token and contains some additional data about the token.
    This class is ordered according to token address. E.g. :code:`Token.WBTC < Token.USDC`.

    Values:

    - `WBTC`
    - `WETH`
    - `USDC`
    - `USDT`

    """

    WBTC = "WBTC"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"

    @property
    def address(self) -> str:
        """
        Mainnet address of the token
        """
        return TOKEN_DETAILS[self.value]["address"]

    @property
    def decimals(self) -> int:
        """
        Decimals of the token
        """
        return TOKEN_DETAILS[self.value]["decimals"]

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
    """
    ``Pool`` represents a UniV3 pool.

    :param tokenA: First token of the pool
    :param tokenB: Second token of the pool
    :param fee: Pool fee
    """

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

    @property
    def decimals_diff(self) -> int:
        """
        Difference between ``token0`` and ``token1`` decimals. Used for conversion of price from `wei` to `eth`.
        """
        return self._token0.decimals - self._token1.decimals

    @property
    def l_decimals_diff(self) -> int:
        """
        Average of ``token0`` and ``token1`` decimals. Used for conversion of liquidity from `wei` to `eth`.
        """
        return int((self._token0.decimals + self._token1.decimals) / 2)

    @property
    def name(self) -> str:
        """
        Unique name for the pool
        """
        return f"{self._token0.value}-{self._token1.value}-{self._fee.value}"

    @property
    def address(self) -> str:
        """
        Address of the pool on the mainnet
        """
        return self._address

    @property
    def token0(self) -> Token:
        """
        First token of the pool
        """
        return self._token0

    @property
    def token1(self) -> Token:
        """
        Second token of the pool
        """
        return self._token1

    @property
    def fee(self) -> Fee:
        """
        Fee of the pool
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
    Token.USDT.value: {
        "name": "USDT",
        "description": "Tether USD",
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
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
