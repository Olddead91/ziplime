import datetime
import logging

import numpy as np
import structlog
from pydantic import BaseModel

from ziplime.config.base_algorithm_config import BaseAlgorithmConfig
from ziplime.domain.bar_data import BarData
from ziplime.finance.execution import MarketOrder
from ziplime.trading.trading_algorithm import TradingAlgorithm

logger = structlog.get_logger(__name__)


class EquityToTrade(BaseModel):
    symbol: str
    target_percentage: float


class AlgorithmConfig(BaseAlgorithmConfig):
    currency: str
    equities_to_trade: list[EquityToTrade]


async def initialize(context):
    context.asset = await context.symbol("AAPL")
    context.short_window = 50
    context.long_window = 200


async def handle_data(context, data):
    asset = context.asset
    df = data.history(assets=[asset], fields=["close"], bar_count=context.long_window)
    prices = df["close"].to_numpy()

    current_amount = getattr(context.portfolio.positions.get(asset, 0), 'amount', 0)

    order_buy = await context.order_target_percent(asset=asset, target=1.0, style=MarketOrder())

    order_sell = await context.order_target_percent(asset=asset, target=0.0, style=MarketOrder())
    # if order_buy:
    #     print(f"[{context.simulation_dt}]Buy order, quantity={order_buy.amount},  status={order_buy.status}, cash={context.portfolio.cash}")
    # if order_sell:
    #     print(f"[{context.simulation_dt}]Sell order, quantity={order_sell.amount}, status={order_sell.status}, cash={context.portfolio.cash}")
    #
