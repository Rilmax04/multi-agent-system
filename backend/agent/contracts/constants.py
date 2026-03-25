VALID_COINS = [
    "bitcoin", "ethereum", "tether", "bnb", "solana", "ripple",
    "dogecoin", "cardano", "tron", "avalanche", "shiba-inu",
    "polkadot", "litecoin", "chainlink", "uniswap", "stellar",
    "monero", "near", "cosmos", "filecoin", "aptos", "hedera",
    "arbitrum", "optimism", "aave", "algorand", "fantom",
    "tezos", "eos", "bitcoin-cash",
]

COIN_ALIASES = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "xrp": "ripple", "doge": "dogecoin", "ada": "cardano",
    "dot": "polkadot", "ltc": "litecoin", "link": "chainlink",
    "avax": "avalanche", "bnb": "bnb", "trx": "tron",
    "shib": "shiba-inu",
    "биткоин": "bitcoin", "биткойн": "bitcoin",
    "эфириум": "ethereum", "эфир": "ethereum",
    "солана": "solana", "рипл": "ripple",
    "кардано": "cardano", "лайткоин": "litecoin",
}

PERIOD_KEYWORDS = {
    "час": 1, "сутки": 1, "день": 1,
    "неделю": 7, "недели": 14,
    "месяц": 30, "квартал": 90,
    "полгода": 180, "год": 365,
}