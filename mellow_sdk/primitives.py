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
    ULTRA_LOW = 100
    LOW = 500
    MIDDLE = 3000
    HIGH = 10000

    @property
    def percent(self) -> float:
        """
        Returns:
            UniswapV3 fee in form of 0.01%, 0.05%, 0.3%, 1%
        """
        return self.value / 10000

    @property
    def fraction(self) -> float:
        """
        Returns:
            UniswapV3 fee in form of 0.0001, 0.0005, 0.003, 0.01.
        """
        return self.percent / 100

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

    agEUR = "agEUR"
    FRAX = "FRAX"
    DAI = "DAI"
    RAI = "RAI"
    ETH2x_FLI = "ETH2x-FLI"
    UNI = "UNI"
    MATIC = "MATIC"
    LOOKS = "LOOKS"
    LINK = "LINK"
    APE = "APE"
    sETH2 = "sETH2"
    FEI = "FEI"
    rETH2 = "rETH2"
    BUSD = "BUSD"
    EURT = "EURT"
    UST = "UST"


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
        return f"{self._token0.value}/{self._token1.value} {self._fee.percent}%"

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

    Token.agEUR.value: {
        "name": "agEUR",
        "description": "",
        "address": "0x1a7e4e63778B4f12a199C062f3eFdD288afCBce8",
        "decimals": 18
    },
    Token.FRAX.value: {
        "name": "FRAX",
        "description": "",
        "address": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
        "decimals": 18
    },
    Token.DAI.value: {
        "name": "DAI",
        "description": "",
        "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "decimals": 18
    },
    Token.RAI.value: {
        "name": "RAI",
        "description": "",
        "address": "0x03ab458634910AaD20eF5f1C8ee96F1D6ac54919",
        "decimals": 18
    },
    Token.ETH2x_FLI.value: {
        "name": "ETH2x-FLI",
        "description": "",
        "address": "0xAa6E8127831c9DE45ae56bB1b0d4D4Da6e5665BD",
        "decimals": 18
    },
    Token.UNI.value: {
        "name": "UNI",
        "description": "",
        "address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "decimals": 18
    },
    Token.MATIC.value: {
        "name": "MATIC",
        "description": "",
        "address": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
        "decimals": 18
    },
    Token.LOOKS.value: {
        "name": "LOOKS",
        "description": "",
        "address": "0xf4d2888d29D722226FafA5d9B24F9164c092421E",
        "decimals": 18
    },
    Token.LINK.value: {
        "name": "LINK",
        "description": "",
        "address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "decimals": 18
    },
    Token.APE.value: {
        "name": "APE",
        "description": "",
        "address": "0x4d224452801ACEd8B2F0aebE155379bb5D594381",
        "decimals": 18
    },
    Token.sETH2.value: {
        "name": "sETH2",
        "description": "",
        "address": "0xFe2e637202056d30016725477c5da089Ab0A043A",
        "decimals": 18
    },
    Token.FEI.value: {
        "name": "FEI",
        "description": "",
        "address": "0x956F47F50A910163D8BF957Cf5846D573E7f87CA",
        "decimals": 18
    },
    Token.rETH2.value: {
        "name": "rETH2",
        "description": "",
        "address": "0x20BC832ca081b91433ff6c17f85701B6e92486c5",
        "decimals": 18
    },
    Token.BUSD.value: {
        "name": "BUSD",
        "description": "",
        "address": "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
        "decimals": 18
    },
    Token.EURT.value: {
        "name": "EURT",
        "description": "",
        "address": "0xC581b735A1688071A1746c968e0798D642EDE491",
        "decimals": 6
    },
    Token.UST.value: {
        "name": "UST",
        "description": "",
        "address": "0xa47c8bf37f92aBed4A126BDA807A7b7498661acD",
        "decimals": 18
    }
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

    {
        "address": "0x8ce5796ef6B0c5918025bCf4f9CA908201B030b3",
        "token0": Token.agEUR,
        "token1": Token.FRAX,
        "fee": Fee.LOW,
    },
    {
        "address": "0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168",
        "token0": Token.DAI,
        "token1": Token.USDC,
        "fee": Fee.ULTRA_LOW,
    },
    {
        "address": "0x60594a405d53811d3BC4766596EFD80fd545A270",
        "token0": token.DAI,
        "token1": token.ETH,
        "fee": Fee.LOW,
    },
    {
        "address": "0x6c6Bc977E13Df9b0de53b251522280BB72383700",
        "token0": token.DAI,
        "token1": token.USDC,
        "fee": Fee.LOW,
    },
    {
        "address": "0x97e7d56A0408570bA1a7852De36350f7713906ec",
        "token0": token.DAI,
        "token1": token.FRAX,
        "fee": Fee.LOW,
    },
    {
        "address": "0xC2e9F25Be6257c210d7Adf0D4Cd6E3E881ba25f8",
        "token0": Token.DAI,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0xcB0C5d9D92f4F2F80cce7aa271a1E148c226e19D",
        "token0": Token.RAI,
        "token1": Token.DAI,
        "fee": Fee.LOW,
    },
    {
        "address": "0x151CcB92bc1eD5c6D0F9Adb5ceC4763cEb66AC7f",
        "token0": Token.ETH2x_FLI,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x1d42064Fc4Beb5F8aAF85F4617AE8b3b5B8Bd801",
        "token0": Token.UNI,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x290A6a7460B308ee3F19023D2D00dE604bcf5B42",
        "token0": Token.MATIC,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x4b5Ab61593A2401B1075b90c04cBCDD3F87CE011",
        "token0": Token.ETH,
        "token1": Token.LOOKS,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0xa6Cc3C2531FdaA6Ae1A3CA84c2855806728693e8",
        "token0": Token.LINK,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0xAc4b3DacB91461209Ae9d41EC517c2B9Cb1B7DAF",
        "token0": Token.APE,
        "token1": Token.ETH,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0x7379e81228514a1D2a6Cf7559203998E20598346",
        "token0": Token.ETH,
        "token1": Token.sETH2,
        "fee": Fee.MIDDLE,
    },
    {
        "address": "0xdf50fbde8180c8785842c8e316ebe06f542d3443",
        "token0": Token.FEI,
        "token1": Token.USDC,
        "fee": Fee.ULTRA_LOW,
    },
    {
        "address": "0xa9ffb27d36901F87f1D0F20773f7072e38C5bfbA",
        "token0": Token.rETH2,
        "token1": Token.sETH2,
        "fee": Fee.,
    },
    {
        "address": "0x00cEf0386Ed94d738c8f8A74E8BFd0376926d24C",
        "token0": Token.BUSD,
        "token1": Token.USDC,
        "fee": Fee.LOW,
    },
    {
        "address": "0x7ED3F364668cd2b9449a8660974a26A092C64849",
        "token0": Token.agEUR,
        "token1": Token.USDC,
        "fee": Fee.LOW,
    },
    {
        "address": "0xc63B0708E2F7e69CB8A1df0e1389A98C35A76D52",
        "token0": Token.FRAX,
        "token1": Token.USDC,
        "fee": Fee.LOW,
    },
    {
        "address": "0x07f3D316630719F4Fc69c152F397c150f0831071",
        "token0": Token.EURT,
        "token1": Token.USDT,
        "fee": Fee.LOW,
    },
    {
        "address": "0x18D96B617a3e5C42a2Ada4bC5d1B48e223f17D0D",
        "token0": Token.USDC,
        "token1": Token.UST,
        "fee": Fee.ULTRA_LOW,
    },
    {
        "address": "0x92995D179a5528334356cB4Dc5c6cbb1c068696C",
        "token0": Token.USDC,
        "token1": Token.UST,
        "fee": Fee.LOW,
    }
]
MIN_TICK = -887272
MAX_TICK = 887272
SPACING = {Fee.LOW: 10, Fee.MIDDLE: 60, Fee.HIGH: 200}
