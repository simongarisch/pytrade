import pytest
from datetime import datetime
from pxtrade.assets import Stock, Portfolio, FxRate
from pxtrade.trade import Trade
from pxtrade.events import (
    AssetPriceEvent,
    FxRateEvent,
    TradeEvent,
    IndicatorEvent,
)


def test_asset_price_event():
    stock = Stock("XYZ AU", 2.50, currency_code="AUD")
    dt = datetime(2020, 9, 1, 12, 30)
    event = AssetPriceEvent(stock, dt, 2.60)
    str_expected = "AssetPriceEvent(Stock('XYZ AU'), 2020-09-01 12:30:00, 2.6)"
    assert str(event) == str_expected
    assert event.asset is stock
    assert event.datetime is dt
    assert event.event_value == 2.60

    # args must be of specific types / values
    with pytest.raises(TypeError):
        AssetPriceEvent(stock, "2020-09-01", 2.60)
    with pytest.raises(TypeError):
        AssetPriceEvent(stock, dt, "2.60")
    with pytest.raises(ValueError):
        AssetPriceEvent(stock, dt, -2.0)  # must be positive

    # is immutable
    with pytest.raises(AttributeError):
        event.asset = stock
    with pytest.raises(AttributeError):
        event.datetime = dt
    with pytest.raises(AttributeError):
        event.event_value = 2.65
    with pytest.raises(AttributeError):
        event.processed = True

    # can be processed
    assert stock.price == 2.50
    assert event.processed is False
    event.process()
    assert event.processed is True
    assert stock.price == 2.60
    with pytest.raises(ValueError):
        event.process()  # cannot process twice


def test_fx_rate_event():
    fx_rate = FxRate("AUDNZD")
    assert fx_rate.rate is None
    dt = datetime(2020, 9, 1, 12, 30)
    event = FxRateEvent(fx_rate, dt, 1.10)
    assert str(event) == "FxRateEvent('AUDNZD', 2020-09-01 12:30:00, 1.1)"
    assert event.fx_rate is fx_rate
    assert event.fx_rate.pair == "AUDNZD"
    assert event.datetime is dt
    assert event.event_value == 1.10

    # args must be of specific types / values
    with pytest.raises(TypeError):
        FxRateEvent("AUDNZD", dt, 1.10)
    with pytest.raises(TypeError):
        FxRateEvent(fx_rate, "2020-09-01", 1.10)
    with pytest.raises(TypeError):
        FxRateEvent(fx_rate, dt, "1.10")

    # is immutable
    with pytest.raises(AttributeError):
        event.fx_rate = fx_rate
    with pytest.raises(AttributeError):
        event.datetime = dt
    with pytest.raises(AttributeError):
        event.event_value = 1.09

    # can be processed
    assert event.processed is False
    event.process()
    assert event.processed is True
    assert fx_rate.rate == 1.10
    with pytest.raises(ValueError):
        event.process()  # cannot process twice


def test_proposed_trade_event():
    Portfolio.reset()
    portfolio = Portfolio("USD")
    goog = Stock("GOOG US", 1500, currency_code="USD")
    dt = datetime(2020, 9, 1, 12, 30)
    trade = Trade(portfolio, goog, +100)
    event = TradeEvent(dt, trade)
    str_expected = "TradeEvent(2020-09-01 12:30:00, Trade(Portfolio('USD'), 'GOOG US', 100))"  # noqa: E501
    assert str(event) == str_expected
    assert event.datetime is dt
    assert event.event_value is trade

    # args must be of specific types / values
    with pytest.raises(TypeError):
        TradeEvent("2020-09-01", trade)
    with pytest.raises(TypeError):
        TradeEvent(dt, 100)

    # is immutable
    with pytest.raises(AttributeError):
        event.event_value.portfolio = portfolio
    with pytest.raises(AttributeError):
        event.datetime = datetime
    with pytest.raises(AttributeError):
        event.event_value = trade

    # process the trade
    assert portfolio.get_holding_units("GOOG US") == 0
    assert portfolio.get_holding_units("USD") == 0
    event.process()
    assert portfolio.get_holding_units("GOOG US") == 100
    assert portfolio.get_holding_units("USD") == -1500 * 100


def test_indicator_event():
    dt = datetime(2020, 9, 1, 12, 30)
    event = IndicatorEvent("some_name", dt, "some_value")
    str_expected = (
        "IndicatorEvent('some_name', 2020-09-01 12:30:00, some_value)"  # noqa: E501
    )
    assert str(event) == str_expected
    assert event.datetime is dt
    assert event.indicator_name == "some_name"
    assert event.event_value == "some_value"

    # is immutable
    with pytest.raises(AttributeError):
        event.datetime = dt
    with pytest.raises(AttributeError):
        event.event_value = "some_value"


def test_indicator_event_validation():
    dt = datetime(2020, 9, 1, 12, 30)

    def validation_func(x):
        if not isinstance(x, str):
            raise TypeError("Expecting string.")

    event = IndicatorEvent(
        "IndicatorName", dt, "IndicatorValue", validation_func=validation_func
    )
    assert event.datetime is dt
    assert event.event_value == "IndicatorValue"
    assert event._process() is None  # no associated backtest

    # event value must pass valiadation_func validation
    with pytest.raises(TypeError):
        IndicatorEvent(
            "IndicatorName", dt, 123, validation_func=validation_func
        )  # noqa: E501

    # validation func must be callable
    with pytest.raises(TypeError):
        IndicatorEvent("IndicatorName", dt, "xxx", validation_func=123)

    # indicator name must be a string
    with pytest.raises(TypeError):
        IndicatorEvent(123, dt, "xxx")
