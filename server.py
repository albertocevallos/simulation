"""server.py: Functions for setting up the simulation/visualisation server."""

from typing import List

from visualization.modules import ChartModule, OrderBookModule, WealthModule, PortfolioModule, \
    CurrentOrderModule, CandleStickModule, PastOrdersModule

from visualization.UserParam import UserSettableParameter
from visualization.ModularVisualization import ModularServer

import model


def make_server(n_agents: int = 50, ur: float = 0.2,
                cont_orders: bool = True, threaded=True) -> ModularServer:
    """
    Set up the simulation/visualisation server and return it.

    "Label": "0"/"1" is a workaround to show the graph label where there is only one label
      (the graphs with only one label wont show the label value, and also show multiple
      values at the same time)
    """
    ref_colour = "lightgrey"

    charts: List[VisualizationElement] = [
        CandleStickModule([
            {"Label": "NominFiatPriceData", "orderbook": "NominFiatOrderBook",
             "AvgColor": "rgba(0,191,255,0.6)", "VolumeColor": "rgba(0,191,255,0.3)"}  # deepskyblue
        ]),

        CandleStickModule([
            {"Label": "CuritFiatPriceData", "orderbook": "CuritFiatOrderBook",
             "AvgColor": "rgba(255,0,0,0.6)", "VolumeColor": "rgba(255,0,0,0.3)"}  # red
        ]),

        CandleStickModule([
            {"Label": "CuritNominPriceData", "orderbook": "CuritNominOrderBook",
             "AvgColor": "rgba(153,50,204,0.6)", "VolumeColor": "rgba(153,50,204,0.3)"}  # darkorchid
        ]),

        ChartModule([
            {"Label": "Havven Nomins", "Color": "deepskyblue"},
            {"Label": "Havven Curits", "Color": "red"},
            {"Label": "Havven Fiat", "Color": "darkgreen"},
        ]),

        ChartModule([
            {"Label": "Gini", "Color": "navy"},
            {"Label": "0", "Color": ref_colour}
        ]),

        ChartModule([
            {"Label": "Max Wealth", "Color": "purple"},
            {"Label": "Min Wealth", "Color": "orange"},
        ]),

        ChartModule([
            {"Label": "Avg Profit %", "Color": "grey"},
            {"Label": "Bank Profit %", "Color": "blue"},
            {"Label": "Arb Profit %", "Color": "red"},
            {"Label": "Rand Profit %", "Color": "green"},
            {"Label": "NomShort Profit %", "Color": "orchid"},
            {"Label": "EscrowNomShort Profit %", "Color": "darkorchid"},
            {"Label": "0", "Color": ref_colour}
        ]),

        ChartModule([
            {"Label": "Nomins", "Color": "deepskyblue"},
            {"Label": "Escrowed Curits", "Color": "darkred"},
        ]),

        ChartModule([
            {"Label": "Curit Demand", "Color": "red"},
            {"Label": "Curit Supply", "Color": "orange"},
        ]),

        ChartModule([
            {"Label": "Nomin Demand", "Color": "deepskyblue"},
            {"Label": "Nomin Supply", "Color": "purple"},
        ]),

        ChartModule([
            {"Label": "Fiat Demand", "Color": "darkgreen"},
            {"Label": "Fiat Supply", "Color": "lightgreen"},
        ]),

        ChartModule([
            {"Label": "Fee Pool", "Color": "blue"},
            {"Label": "0", "Color": ref_colour}
        ]),

        ChartModule([
            {"Label": "Fees Distributed", "Color": "blue"},
            {"Label": "0", "Color": ref_colour}
        ]),

        PortfolioModule([{"Label": "WealthBreakdown"}], fiat_values=False),

        WealthModule([{"Label": "Wealth"}]),

        CurrentOrderModule([{"Label": "PlayerBidAskVolume"}]),

        PastOrdersModule([{"Label": "TotalMarketVolume"}]),

        OrderBookModule([{"Label": "NominFiatOrderBook"}]),

        OrderBookModule([{"Label": "CuritFiatOrderBook"}]),

        OrderBookModule([{"Label": "CuritNominOrderBook"}])
    ]

    n_slider = UserSettableParameter(
        'slider', "Number of agents", n_agents, 20, 2000, 1
    )

    ur_slider = UserSettableParameter(
        'slider', "Utilisation Ratio", ur, 0.0, 1.0, 0.01
    )

    match_checkbox = UserSettableParameter(
        'checkbox', "Continuous order matching", cont_orders
    )

    # the none value will randomize the data on every model reset
    agent_fraction_selector = UserSettableParameter(
        'agent_fractions', "Agent fraction selector", None
    )

    server = ModularServer(threaded, model.Havven, charts, "Havven Model",
                           {"num_agents": n_slider, "utilisation_ratio_max": ur_slider,
                            "match_on_order": match_checkbox, 'agent_fractions': agent_fraction_selector})
    return server
