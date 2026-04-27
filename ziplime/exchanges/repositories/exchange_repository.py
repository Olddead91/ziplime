from abc import abstractmethod, ABC

from ziplime.exchanges.exchange import Exchange


class ExchangeRepository(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def get_exchange_by_name(self, name: str) -> Exchange:
        pass

    @abstractmethod
    async def add_exchange(self, exchange: Exchange) -> Exchange:
        pass

    @abstractmethod
    async def get_default_exchange(self) -> Exchange:
        pass

    @abstractmethod
    async def get_all_exchanges(self) -> list[Exchange]:
        pass

    @abstractmethod
    def get_all_exchanges_sync(self) -> list[Exchange]:
        pass
