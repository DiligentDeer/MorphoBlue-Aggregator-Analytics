import streamlit as st
import plotly.graph_objects as go


# Define a function to plot multi-line chart
def create_plot(vault_name, df, LPprice, i):
    # Create Plotly figure
    fig = go.Figure()

    # Add line for vault data
    fig.add_trace(go.Scatter(x=df['block'], y=df[vault_name], mode='lines', name=f'Oracle {vault_name}', line=dict(color='#2685ed')))

    # Add line for LPprice data
    lp_column_index = i + 1
    lp_column_name = LPprice.columns[lp_column_index]
    fig.add_trace(go.Scatter(x=LPprice['block'], y=LPprice[lp_column_name], mode='lines', name=f'Curve LP Price - {vault_name}', line=dict(color='#9ecbff')))

    # Update layout
    fig.update_layout(xaxis_title='Block',
                      yaxis_title='Value',
                      legend=dict(x=0, y=1, traceorder='normal'))

    return fig