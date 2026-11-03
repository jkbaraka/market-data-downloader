
import requests
import csv
import os
import logging
from datetime import datetime, timedelta, timezone


# Configure logging
logging.basicConfig(
    filename="downloader.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def validate_market_data(rows):
    """Check market data for chronological order and duplicate dates."""

    dates = [row["Date"] for row in rows]

    if dates != sorted(dates):
        raise ValueError(
            "Market data dates are not in chronological order."
        )

    if len(dates) != len(set(dates)):
        raise ValueError(
            "Duplicate trading dates found in market data."
        )
    
def get_market_data(ticker, start_date, end_date):
    """Download historical daily prices for a ticker."""

    logging.info("Starting download for %s", ticker)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    if start >= end:
        raise ValueError("Start date must be earlier than end date.")

    period1 = int(start.replace(tzinfo=timezone.utc).timestamp())

    end_exclusive = end + timedelta(days=1)
    period2 = int(
        end_exclusive.replace(tzinfo=timezone.utc).timestamp()
    )

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    response = requests.get(
        url,
        params={
            "period1": period1,
            "period2": period2,
            "interval": "1d",
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )

    response.raise_for_status()
    data = response.json()

    chart = data.get("chart", {})
    results = chart.get("result")
    error = chart.get("error")

    if error or not results:
        raise ValueError(f"No market data found for {ticker}.")

    result = results[0]
    timestamps = result.get("timestamp", [])
    quotes = result.get("indicators", {}).get("quote", [])
    adjusted_quotes = result.get("indicators", {}).get("adjclose", [])

    if not timestamps or not quotes:
        raise ValueError(f"No price data available for {ticker}.")

    quote = quotes[0]

    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    volumes = quote.get("volume", [])

    if not adjusted_quotes:
        raise ValueError(f"Adjusted closing prices unavailable for {ticker}.")

    adjusted_closes = adjusted_quotes[0].get("adjclose", [])

    rows = []
    previous_adjusted_close = None

    for timestamp, open_price, high, low, close, adj_close, volume in zip(
        timestamps, opens, highs, lows, closes, adjusted_closes, volumes
    ):
        if any(value is None for value in (
            open_price, high, low, close, adj_close, volume
        )):
            continue
        if previous_adjusted_close is None:
            daily_return = None
        else:
            daily_return = (
                (adj_close / previous_adjusted_close) - 1
            ) * 100

        date = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).strftime("%Y-%m-%d")

        rows.append({
            "Date": date,
            "Ticker": ticker,
            "Open": round(open_price, 2),
            "High": round(high, 2),
            "Low": round(low, 2),
            "Close": round(close, 2),
            "Adj Close": round(adj_close, 2),
            "Volume": volume,
            "Daily Return (%)": (
                round(daily_return, 4)
                if daily_return is not None
                else None
            ),
        })
        previous_adjusted_close = adj_close
    validate_market_data(rows)
    logging.info(
        "Successfully downloaded %s records for %s",
        len(rows),
        ticker
    )

    return rows


def save_to_csv(rows, ticker, start_date, end_date):
    """Save market data using a filename containing the date range."""

    os.makedirs("data", exist_ok=True)

    filename = os.path.join(
        "data",
        f"{ticker}_{start_date}_{end_date}.csv"
    )

    with open(filename, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "Date",
            "Ticker",
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume",
            "Daily Return (%)"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    logging.info("Saved %s records to %s", len(rows), filename)

    return filename


def main():
    """Run the market-data downloader."""

    ticker = input("Enter a stock ticker (e.g. AAPL, MSFT, GOOG): ")
    ticker = ticker.strip().upper()

    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    if not ticker:
        print("Error: ticker cannot be empty.")
        logging.warning("User entered an empty ticker.")
        return

    try:
        rows = get_market_data(ticker, start_date, end_date)

        if not rows:
            print("No closing prices were available for that period.")
            logging.warning("No closing prices found for %s", ticker)
            return

        filename = save_to_csv(rows, ticker, start_date, end_date)

        print(f"Downloaded {len(rows)} daily prices.")
        print(f"Saved market data to {filename}.")

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            print(f"Error: ticker '{ticker}' was not found.")
        else:
            print(f"HTTP error: {error}")

        logging.error("HTTP error while downloading %s: %s", ticker, error)

    except requests.RequestException as error:
        print(f"Network error: {error}")
        logging.error("Network error while downloading %s: %s", ticker, error)

    except (ValueError, KeyError, IndexError, TypeError) as error:
        print(f"Error: {error}")
        logging.error("Error while processing %s: %s", ticker, error)


if __name__ == "__main__":
    main()
