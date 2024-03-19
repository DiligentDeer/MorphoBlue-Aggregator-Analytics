import const
import utils
import chart
import streamlit as st

# LOAD past saved files
LPprice, USDprice = utils.load_data()

# Get the latest Block Number to check if enough time has passed to accumulate data for new Blocks
latest_block_with_data = LPprice['block'].max()

historic_block_list = utils.accumulate_block_with_no_data(latest_block_with_data)

if utils.w3.eth.block_number - const.BLOCK_INTERVAL > latest_block_with_data:
    LPprice, USDprice = utils.populate_data(historic_block_list, LPprice, USDprice)

feed_dict = { f'{const.VAULT_NAME[0]}': utils.construct_feed(0, USDprice['price_USDT'], USDprice['price_crvUSD'], LPprice=LPprice)
              ,f'{const.VAULT_NAME[1]}': utils.construct_feed(1, USDprice['price_USDC'], USDprice['price_crvUSD'], LPprice=LPprice)
              ,f'{const.VAULT_NAME[2]}': utils.construct_feed(2, 1, 1, LPprice=LPprice)
              ,f'{const.VAULT_NAME[3]}': utils.construct_feed(3, USDprice['price_wstETH'], USDprice['price_crvUSD'], LPprice=LPprice)
              ,f'{const.VAULT_NAME[4]}': utils.construct_feed(4, 1, 1, LPprice=LPprice)
              }

# ------------------------------------------------------------------------------------------------------------------- #
# Testing

# for i in range(len(feed_dict)):
#     feed_dict[f'{const.VAULT_NAME[i]}'].info()
# LPprice.info()
# USDprice.info()

# ------------------------------------------------------------------------------------------------------------------- #
# Streamlit app

# Set the layout width to a wider size
st.set_page_config(layout="wide")


st.title('MorphoBlue crvUSD Oracle Analytics')
st.write(f'The starting block for the data is {const.BLOCK_START}')
st.markdown('<p class="center">Information sourced from the <a href="https://forum.morpho.org/t/llama-risk-crvusd-metamorpho-vault-whitelisting/484">proposal</a> by LlamaRisk.', unsafe_allow_html=True)

# Get the number of plots to determine the number of rows
num_plots = len(feed_dict)
num_rows = (num_plots + 1) // 2  # Adding 1 to ensure we have at least one row

# Iterate over each key-value pair in feed_dict
for i, (vault_name, df) in enumerate(feed_dict.items()):
    # If the current plot is in the first column, create a new row
    if i % 2 == 0:
        col1, col2 = st.columns(2)

    # Plot multi-line chart
    with col1 if i % 2 == 0 else col2:
        st.write(f"### {vault_name} Aggregator Oracle Price vs. LP Price")
        fig = chart.create_plot(vault_name, df, LPprice, i)
        # Show plot in Streamlit app
        st.plotly_chart(fig)

st.markdown('<p class="center">A Dashboard by <a href="https://twitter.com/LlamaRisk">LlamaRisk</a>! Builder: <a href="https://twitter.com/diligentdeer">DiligentDeer</a>.', unsafe_allow_html=True)
