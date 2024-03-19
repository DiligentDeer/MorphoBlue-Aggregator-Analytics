from web3 import Web3, HTTPProvider
import const
import pandas as pd
from requests import get, post
import time
import streamlit as st

# from dotenv import load_dotenv
import os

INFURA_KEY = os.environ.get("INFURA_KEY")
if INFURA_KEY is None:
    raise ValueError("INFURA_KEY is not set")

# load_dotenv()
#INFURA_KEY = os.getenv("INFURA_KEY")

w3 = Web3(HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_KEY}"))


# ------------------------------------------------------------------------------------------------------------------- #

# Function used to fetch Chainlink Prices in USD
def get_price_chainlink(oracle_address, block=w3.eth.block_number):
    abi = [{"inputs": [], "name": "latestAnswer",
            "outputs": [{"internalType": "int256", "name": "arg_0", "type": "int256"}],
            "stateMutability": "view",
            "type": "function"}]
    address = Web3.to_checksum_address(oracle_address)

    contract = w3.eth.contract(address=address, abi=abi)

    price = contract.functions.latestAnswer().call(block_identifier=int(block))

    data = {
        'block': int(block),
        'price_': float(price / 1e8)
    }

    return data


# Function used to fetch Chainlink Prices for a list of block numbers
def get_price_data_for_blocks(block_numbers, oracle_address):
    price_data_list = []

    for block_number in block_numbers:
        try:
            price_data = get_price_chainlink(oracle_address, int(block_number))
            price_data_list.append(price_data)
        except Exception as e:
            # print(f"Error fetching data for block {block_number}: {e}")
            continue

    return pd.DataFrame(price_data_list)


# Function used to fetch wstETH Price in ETH
def get_price_wsteth(oracle_address=const.WSTETH_PRICE, block=w3.eth.block_number):
    abi = [{"inputs": [], "name": "latestRoundData",
            "outputs": [{"internalType": "uint80", "name": "roundId", "type": "uint80"},
                        {"internalType": "int256", "name": "answer", "type": "int256"},
                        {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
                        {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                        {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}],
            "stateMutability": "view",
            "type": "function"}]
    address = Web3.to_checksum_address(oracle_address)

    contract = w3.eth.contract(address=address, abi=abi)

    price = contract.functions.latestRoundData().call(block_identifier=int(block))

    data = {
        'block': int(block),
        'price_wstETH': float(price[1] / 1e8)
    }

    return data


# Function used to fetch wstETH Price in ETH for a list of block numbers
def get_wsteth_data_for_blocks(block_numbers, oracle_address=const.WSTETH_PRICE):
    price_data_list = []

    for block_number in block_numbers:
        try:
            price_data = get_price_wsteth(oracle_address, int(block_number))
            price_data_list.append(price_data)
        except Exception as e:
            # print(f"Error fetching data for block {block_number}: {e}")
            continue

    return pd.DataFrame(price_data_list)


# Function used to compile all the price data in USD format
def merge_chainlink_data(historic_block_list, oracle_list=const.CHAINLINK_USD):
    data_list = []
    names = list(const.CHAINLINK_USD.keys())

    for i in range(len(oracle_list)):
        price_data = get_price_data_for_blocks(historic_block_list, oracle_list[f'{names[i]}'])
        price_data = price_data.add_suffix(names[i])
        price_data = price_data.rename(columns={f'block{names[i]}': 'block'})
        data_list.append(price_data)

    data_list_for_merging = data_list.copy()

    merged_df = data_list_for_merging[0]
    for df in data_list_for_merging[1:]:
        merged_df = pd.merge(merged_df, df, on='block', how='inner')
        merged_df = merged_df.rename(columns={f'block_x': 'block'})

    wsteth = get_wsteth_data_for_blocks(block_numbers=historic_block_list)

    wsteth["price_wstETH"] = wsteth["price_wstETH"] * merged_df["price_ETH"]

    merged_df = pd.merge(merged_df, wsteth, on='block', how='inner')

    return merged_df


# ------------------------------------------------------------------------------------------------------------------- #

# Function used to fetch Pool token Price from Curve
def get_lp_price(pool_address, block=w3.eth.block_number):
    abi = [{"stateMutability": "view",
            "type": "function",
            "name": "lp_price",
            "inputs": [],
            "outputs": [{"name": "arg_0", "type": "uint256"}]}]
    address = Web3.to_checksum_address(pool_address)

    contract = w3.eth.contract(address=address, abi=abi)

    price = contract.functions.lp_price().call(block_identifier=int(block))

    data = {
        'block': int(block),
        'price_': float(price / 1e18)
    }

    return data


# Function used to fetch Pool token Price for a list of block numbers
def get_lp_price_for_blocks(block_numbers, pool_address):
    price_data_list = []

    for block_number in block_numbers:
        try:
            price_data = get_lp_price(pool_address, int(block_number))
            price_data_list.append(price_data)
        except Exception as e:
            # print(f"Error fetching data for block {block_number}: {e}")
            continue

    return pd.DataFrame(price_data_list)


# Function used to compile all the lp token price data
def merge_lp_price(historic_block_list, pool_address_list=const.POOL_ADDRESS_LIST, pool_names=const.VAULT_NAME):
    data_list = []

    for i in range(len(pool_address_list)):
        price_data = get_lp_price_for_blocks(historic_block_list, pool_address_list[i])
        price_data = price_data.add_suffix(pool_names[i])
        price_data = price_data.rename(columns={f'block{pool_names[i]}': 'block'})
        data_list.append(price_data)

    data_list_for_merging = data_list.copy()

    merged_df = data_list_for_merging[0]
    for df in data_list_for_merging[1:]:
        merged_df = pd.merge(merged_df, df, on='block', how='inner')
        merged_df = merged_df.rename(columns={f'block_x': 'block'})

    return merged_df


# ------------------------------------------------------------------------------------------------------------------- #
def load_data():
    lp = pd.read_csv('LPprice.csv')
    usd = pd.read_csv('USDprice.csv')
    return lp, usd


def save_data(lp, usd):
    lp.to_csv('LPprice.csv', index=False)
    usd.to_csv('USDprice.csv', index=False)


# ------------------------------------------------------------------------------------------------------------------- #
def accumulate_block_with_no_data(latest_block_with_data):
    latest_block_number = w3.eth.block_number
    historic_block_list = []

    start_block_number = closest_lower_value(latest_block_with_data) + const.BLOCK_INTERVAL
    # print(f'start_block_number = {start_block_number}')

    while start_block_number < latest_block_number:
        # Add the current block number to the list
        historic_block_list.append(start_block_number)
        # Compute the next block number
        start_block_number += const.BLOCK_INTERVAL

    historic_block_list.append(latest_block_number)

    return historic_block_list


def closest_lower_value(latest_block_with_data, starting_number=const.BLOCK_START):
    # print(f'starting_number = {starting_number}')
    target_number = latest_block_with_data
    # Calculate the number of steps needed to reach the target number
    steps = (target_number - starting_number) // const.BLOCK_INTERVAL

    # Calculate the closest lower value
    closest_lower = starting_number + steps * const.BLOCK_INTERVAL

    return closest_lower


# ------------------------------------------------------------------------------------------------------------------- #
def populate_data(blocks_with_no_data, LPprice, USDprice):
    new_LPprice = merge_lp_price(blocks_with_no_data)
    concat_LPprice = pd.concat([LPprice, new_LPprice], ignore_index=True)

    new_USDprice = merge_chainlink_data(blocks_with_no_data)
    concat_USDprice = pd.concat([USDprice, new_USDprice], ignore_index=True)

    save_data(concat_LPprice,concat_USDprice)

    return concat_LPprice, concat_USDprice


def construct_feed(index, multiply, divide, LPprice):
    df = pd.DataFrame()
    df['block'] = LPprice['block']
    df[const.VAULT_NAME[index]] = LPprice[f'price_{const.VAULT_NAME[index]}'] * multiply / divide

    return df
