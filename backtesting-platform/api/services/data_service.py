from __future__ import annotations

from sqlalchemy.orm import Session

from api.models.orm import Stock
from data.yfinance_client import YFinanceClient


class DataService:
    def __init__(self) -> None:
        self.client = YFinanceClient()

    def get_or_create_stock(self, db: Session, ticker: str) -> Stock:
        ticker = ticker.upper().strip()
        stock = db.query(Stock).filter(Stock.ticker == ticker).first()
        if stock:
            return stock

        info = self.client.get_stock_info(ticker)
        stock = Stock(
            ticker=ticker,
            name=info.get("name"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            exchange=info.get("exchange"),
            market_cap=info.get("market_cap"),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
        return stock

    def get_prices(self, ticker: str, start: str | None = None, end: str | None = None):
        return self.client.get_prices(ticker, start=start, end=end)
