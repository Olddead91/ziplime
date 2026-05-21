import datetime
from functools import lru_cache
from typing import Literal

import aiocache
import polars as pl
import uuid

from aiocache import Cache
from exchange_calendars import ExchangeCalendar

from ziplime.assets.entities.asset import Asset
from ziplime.assets.entities.equity import Equity
from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.assets.entities.futures_contract import FuturesContract
from ziplime.constants.period import Period
from ziplime.data.services.data_source import DataSource

from ziplime.domain.position import Position
from ziplime.domain.portfolio import Portfolio
from ziplime.domain.account import Account
from ziplime.finance.commission import EquityCommissionModel, FutureCommissionModel, CommissionModel
from ziplime.finance.domain.commission import Commission
from ziplime.finance.domain.order import Order
from ziplime.finance.slippage.slippage_model import SlippageModel
from ziplime.exchanges.exchange import Exchange
from ziplime.gens.domain.trading_clock import TradingClock


class SimulationExchange(Exchange):

    def __init__(self,
                 name: str,
                 country_code: str,
                 trading_calendar: ExchangeCalendar,
                 clock: TradingClock,
                 cash_balance: float,
                 equity_slippage: SlippageModel,
                 future_slippage: SlippageModel,
                 equity_commission: EquityCommissionModel,
                 future_commission: FutureCommissionModel,
                 account_id:str,
                 is_default: bool,
                 data_source: DataSource = None,
                 price_used_in_order_execution: Literal["open", "close", "low", "high"] = "close"
                 ):
        super().__init__(name=name,
                         canonical_name=name,
                         clock=clock,
                         data_source=data_source,
                         country_code=country_code,
                         trading_calendar=trading_calendar,
                         account_id=account_id, is_default=is_default)
        self.slippage_models = {
            Equity: equity_slippage,
            FuturesContract: future_slippage,
        }
        self.commission_models = {
            Equity: equity_commission,
            FuturesContract: future_commission,
        }
        self.cash_balance = cash_balance
        self.price_used_in_order_execution = price_used_in_order_execution

    def get_start_cash_balance(self) -> float:
        return self.cash_balance

    def get_current_cash_balance(self) -> float:
        return self.cash_balance

    def get_commission_model(self, asset: ExchangeAsset) -> CommissionModel:
        return self.commission_models[type(asset.asset)]

    def get_slippage_model(self, asset: ExchangeAsset) -> SlippageModel:
        return self.slippage_models[type(asset.asset)]

    async def submit_order(self, order: Order):
        order.id = uuid.uuid4().hex
        return order

    async def get_positions(self) -> dict[Asset, Position]:
        pass

    async def get_portfolio(self) -> Portfolio:
        positions = {}
        portfolio = Portfolio(start_date=datetime.datetime.now(tz=datetime.timezone.utc),
                              starting_cash=self.cash_balance,
                              portfolio_value=self.cash_balance,
                              cash=self.cash_balance,
                              cash_flow=0.00,
                              pnl=0.00,
                              returns=0.00,
                              positions_value=0.00,
                              positions_exposure=0.00,
                              positions=positions
                              )
        return portfolio

    async def get_account(self) -> Account:
        pass

    def get_time_skew(self):
        pass

    async def order(self, asset, amount, style):
        pass

    def is_alive(self):
        pass

    async def get_orders(self) -> dict[str, Order]:
        return {}

    async def get_transactions(self, orders: dict[Asset, dict[str, Order]],
                               current_dt: datetime.datetime, same_bar_execution: bool):
        """
        Creates a list of transactions based on the current open orders,
        slippage model, and commission model.

        Parameters
        ----------
        bar_data: ziplime._protocol.BarData

        Notes
        -----
        This method book-keeps the blotter's open_orders dictionary, so that
         it is accurate by the time we're done processing open orders.

        Returns
        -------
        transactions_list: List
            transactions_list: list of transactions resulting from the current
            open orders.  If there were no open orders, an empty list is
            returned.

        commissions_list: List
            commissions_list: list of commissions resulting from filling the
            open orders.  A commission is an object with "asset" and "cost"
            parameters.

        closed_orders: List
            closed_orders: list of all the orders that have filled.
        """

        closed_orders = []
        transactions = []
        commissions = []

        for asset, asset_orders in orders.items():
            slippage = self.get_slippage_model(asset=asset)

            async for order, txn in slippage.simulate(exchange=self,
                                                      assets=frozenset({asset}),
                                                      orders_for_asset=asset_orders.values(),
                                                      current_dt=current_dt,
                                                      same_bar_execution=same_bar_execution,
                                                      price_used_in_order_execution=self.price_used_in_order_execution
                                                      ):
                commission = self.get_commission_model(asset=asset)
                additional_commission = commission.calculate(order=order, transaction=txn)

                if additional_commission > 0:
                    commissions.append(
                        Commission(
                            asset=order.asset,
                            order=order,
                            amount=additional_commission,
                        )
                    )

                order.filled += txn.amount
                order.commission += additional_commission
                order.dt = txn.dt
                transactions.append(txn)
                if not order.open:
                    closed_orders.append(order)

        return transactions, commissions, closed_orders

    async def get_orders_by_ids(self, order_ids: list[str]):
        pass

    async def get_transactions_by_order_ids(self, order_ids: list[str]):
        pass

    async def cancel_order(self, order_param):
        pass

    def get_last_traded_dt(self, asset):
        pass

    async def get_spot_value(self, assets: frozenset[Asset], fields: frozenset[str], dt: datetime.datetime,
                             data_frequency: datetime.timedelta = None) -> pl.DataFrame:
        return await self.get_data_by_limit(
            fields=fields,
            limit=1,
            end_date=dt,
            frequency=data_frequency or self.data_source.frequency,
            assets=assets,
            include_end_date=True,
        )

    @aiocache.cached(cache=Cache.MEMORY)
    async def get_data_by_period(self,
                                 fields: frozenset[str],
                                 start_date: datetime.datetime,
                                 end_date: datetime.datetime,
                                 frequency: datetime.timedelta,
                                 assets: frozenset[Asset],
                                 include_end_date: bool,
                                 source: str
                                 ) -> pl.DataFrame:
        return await self.data_source.get_data_by_limit(fields=fields,
                                                        limit=limit,
                                                        end_date=end_date,
                                                        frequency=frequency,
                                                        assets=assets,
                                                        include_end_date=include_end_date,
                                                        )

    @aiocache.cached(cache=Cache.MEMORY)
    async def get_data_by_limit(self, fields: frozenset[str],
                                limit: int,
                                end_date: datetime.datetime,
                                frequency: datetime.timedelta | Period,
                                assets: frozenset[Asset],
                                include_end_date: bool,
                                ) -> pl.DataFrame:
        return await self.data_source.get_data_by_limit(fields=fields,
                                                        limit=limit,
                                                        end_date=end_date,
                                                        frequency=frequency,
                                                        assets=assets,
                                                        include_end_date=include_end_date,
                                                        )
