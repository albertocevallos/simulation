"""
http://www.eecs.harvard.edu/cs286r/courses/fall12/papers/OPRS10.pdf
http://www.cs.cmu.edu/~aothman/
"""

from agents import MarketPlayer
from decimal import Decimal as Dec
from typing import Dict, Any, Optional
import orderbook as ob
import random


class MarketMaker(MarketPlayer):
    """
    Market makers in general have four desiderata:
    (1) bounded loss
    (2) the ability to make a profit
    (3) a vanishing bid/ask spread
    (4) unlimited market depth

    This market maker uses Fixed prices with shrinking profit cut

    Probably the simplest automated market maker is to determine a probability distribution
    over the future states of the world, and to offer to make bets directly at those odds.

    If we allow the profit cut to diminish to zero as trading volume increases, the resulting
    market maker has three of the four desired properties: the ability to make a profit,
    a vanishing marginal bid/ask spread, and unbounded depth in limit.

    However, it still has unbounded worst-case loss because a trader with knowledge of the
    true future could make an arbitrarily large winning bet with the market maker.

    To calculate the probability of the future state, a simple gradient on the moving average
    will be used.

    In the case where the market maker believes the price will rise, it will place a sell at a
    set price in the for the future, and slowly buy at higher and higher prices

    |
    |====================---
    |            -----
    |       -----   =====
    |  -----   =====
    |--   =====
    |=====
    | -> Time
    = Market maker's bid/ask spread
    - Predicted price movement
    the price difference is dependant on the gradient

    TODO: ensure profitability (calculate fees)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_bet_end = random.randint(-20, 10)
        '''How long since the last market maker's "bet"'''

        self.minimal_wait = 10
        '''How long will the market maker wait since it's last "bet" to let the market recover'''
        self.bet_length = 30
        '''How long will the market maker do its "bet" for'''
        self.bet_percentage = Dec('1')
        '''
        How much of it's wealth will the market maker use on a "bet"
        The bot will constantly update the orders on either side to use all it's wealth
        multiplied by the percentage value
        '''
        self.bet_margin = Dec('0.99')
        '''
        How off the expected price gradient will the gradient bet be placed
        This also determines how close the bets get at the end (both would be off by the margin)
        i.e:
        - starting price would be 0.8, expected max price would be 1.1
        - gradient is positive (.01)
        - increase bid by .01 per step
        - start bid at 0.8*margin
        - start ask at 1.1*(2-margin)
        - next bid 0.8*margin + .01 etc...
        '''

        # self.trade_market = random.choice([
        #     self.havven_fiat_market,
        #     self.nomin_fiat_market,
        #     self.havven_nomin_market
        # ])
        self.trade_market = self.havven_fiat_market

        self.current_bet: Optional[Dict[str, Any[str, int, Dec, 'ob.LimitOrder']]] = None

    def step(self):
        # TODO: make it check what it needs more of the two options to sell into
        if self.trade_market == self.havven_nomin_market:
            if self.available_fiat > 0:
                self.sell_fiat_for_havvens_with_fee(self.available_fiat)
        if self.trade_market == self.nomin_fiat_market:
            if self.available_havvens > 0:
                self.sell_havvens_for_fiat_with_fee(self.available_nomins)
        if self.trade_market == self.havven_fiat_market:
            if self.available_nomins > 0:
                self.sell_nomins_for_fiat_with_fee(self.available_nomins)

        # if the duration has ended, close the trades
        if self.last_bet_end >= self.minimal_wait + self.bet_length:
            self.last_bet_end = 0
            self.current_bet['bid'].cancel()
            self.current_bet['ask'].cancel()
            self.current_bet = None
        # if the duration hasn't ended, update the trades
        elif self.current_bet is not None:
            # update both bid and ask every step in case orders were partially filled
            # so that quantities are updated
            self.current_bet['bid'].cancel()
            self.current_bet['ask'].cancel()
            bid = self.place_bid_func(
                self.last_bet_end-self.minimal_wait,
                self.current_bet['gradient'],
                self.current_bet['initial_bid_price']
            )
            if bid is None:
                self.current_bet = None
                self.last_bet_end = 0
                return
            ask = self.place_ask_func(
                self.last_bet_end-self.minimal_wait,
                self.current_bet['gradient'],
                self.current_bet['initial_ask_price']
            )
            if ask is None:
                bid.cancel()
                self.current_bet = None
                self.last_bet_end = 0
                return
            self.current_bet['bid'] = bid
            self.current_bet['ask'] = ask

        # if the minimal wait period has ended, create a bet
        elif self.last_bet_end >= self.minimal_wait:
            gradient = self.calculate_gradient(self.trade_market)
            if gradient is None:
                return
            start_price = self.trade_market.price
            if gradient > Dec(0.0025):
                ask_price = (start_price + gradient*self.bet_length)*(2-self.bet_margin)
                bid_price = start_price*self.bet_margin
            elif gradient < Dec(0.0025):
                ask_price = start_price*(2-self.bet_margin)
                bid_price = (start_price + gradient*self.bet_length)*self.bet_margin
            else:
                return
            bid = self.place_bid_func(
                self.last_bet_end - self.minimal_wait,
                gradient,
                bid_price
            )
            if bid is None:
                self.last_bet_end = 0
                return
            ask = self.place_ask_func(
                self.last_bet_end - self.minimal_wait,
                gradient,
                ask_price
            )
            if ask is None:
                bid.cancel()
                self.last_bet_end = 0
                return

            self.current_bet = {
                'gradient': gradient,
                'initial_bid_price': bid_price,
                'initial_ask_price': ask_price,
                'bid': bid,
                'ask': ask
            }
        self.last_bet_end += 1

    def place_bid_func(self, time_in_effect: int, gradient: Dec, start_price: Dec) -> "ob.Bid":
        if gradient < 0:
            # bids change, asks constant
            price = start_price
        else:
            # asks change, bids constant
            price = start_price + gradient * time_in_effect

        if self.trade_market == self.nomin_fiat_market:
            return self.place_nomin_fiat_bid_with_fee(self.available_fiat*self.bet_percentage/price, price)
        elif self.trade_market == self.havven_fiat_market:
            return self.place_havven_fiat_bid_with_fee(self.available_fiat*self.bet_percentage/price, price)
        elif self.trade_market == self.havven_nomin_market:
            return self.place_havven_nomin_bid_with_fee(self.available_havvens*self.bet_percentage/price, price)

    def place_ask_func(self, time_in_effect: int, gradient: Dec, start_price: Dec) -> "ob.Ask":
        if gradient < 0:
            # bids change, asks constant
            price = start_price + gradient*time_in_effect
        else:
            # asks change, bids constant
            price = start_price

        if self.trade_market == self.nomin_fiat_market:
            return self.place_nomin_fiat_ask_with_fee(self.available_nomins*self.bet_percentage, price)
        elif self.trade_market == self.havven_fiat_market:
            return self.place_havven_fiat_ask_with_fee(self.available_havvens*self.bet_percentage, price)
        elif self.trade_market == self.havven_nomin_market:
            return self.place_havven_nomin_ask_with_fee(self.available_nomins*self.bet_percentage, price)

    def calculate_gradient(self, trade_market: 'ob.OrderBook') -> Optional[Dec]:
        """
        Calculate the gradient of the moving average by taking the difference of the last two points
        """
        if len(trade_market.price_data) < 2:
            return None
        return (trade_market.price_data[-1] - trade_market.price_data[-2])/2
