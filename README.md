# Market Data Downloader

A Python-based tool for downloading historical stock market data from Yahoo Finance and exporting it into CSV files for further analysis.

## Features

- Download historical daily stock prices.
- Support multiple stock tickers.
- Extract Open, High, Low, Close, Adjusted Close and Volume (OHLCV) data.
- Calculate daily percentage returns.
- Export historical data to CSV files.
- Validate date ranges and market data quality.
- Handle invalid tickers, HTTP errors and network failures.
- Maintain application logs.
- Automated unit tests using Python's `unittest` framework.

## Technologies Used

- Python
- Requests
- CSV
- Logging
- Unittest
- Yahoo Finance Chart API

## Project Structure

```text
market-data-downloader/
│
├── data/
│   └── CSV market data files
│
├── tests/
│   └── test_main.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

2. Navigate into the project directory:

```bash
cd market-data-downloader
```

3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate the virtual environment.

Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

Enter the requested information:

- Stock ticker (e.g. AAPL, MSFT, GOOG)
- Start date (YYYY-MM-DD)
- End date (YYYY-MM-DD)

The downloaded data is saved as a CSV file in the `data/` directory.

## Running Tests

Run the automated test suite:

```bash
python -m unittest discover -s tests -v
```

The tests cover market data retrieval, daily return calculations, date validation, data quality, error handling and CSV export.

## Data Source

This project uses the Yahoo Finance Chart API. The endpoint is unofficial and its availability, response format and access policies may change.

## Future Improvements

- SQLite database integration.
- Multiple ticker downloads.
- Historical volatility calculations.
- Moving averages and other technical indicators.
- Data visualisation.
- Backtesting integration.

## Disclaimer

This project is intended for educational and research purposes. It does not provide investment advice.
