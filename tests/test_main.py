
import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone
import requests    

from main import get_market_data, save_to_csv, main


class TestMarketDataDownloader(unittest.TestCase):

    def test_invalid_date_range(self):
        """Start date must be earlier than end date."""

        with self.assertRaises(ValueError):
            get_market_data(
                "AAPL",
                "2025-03-31",
                "2025-01-01"
            )

    @patch("main.requests.get")
    def test_get_market_data(self, mock_get):
        """Check OHLCV data and daily return calculations."""

        timestamps = [
            int(datetime(2025, 1, 2, tzinfo=timezone.utc).timestamp()),
            int(datetime(2025, 1, 3, tzinfo=timezone.utc).timestamp())
        ]

        mock_response = Mock()
        mock_response.json.return_value = {
            "chart": {
                "result": [
                    {
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [
                                {
                                    "open": [240.00, 243.00],
                                    "high": [245.00, 246.00],
                                    "low": [238.00, 240.00],
                                    "close": [243.85, 244.00],
                                    "volume": [1000000, 1200000]
                                }
                            ],
                            "adjclose": [
                                {
                                    "adjclose": [243.50, 244.50]
                                }
                            ]
                        }
                    }
                ],
                "error": None
            }
        }

        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rows = get_market_data(
            "AAPL",
            "2025-01-01",
            "2025-01-05"
        )

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]["Ticker"], "AAPL")
        self.assertEqual(rows[0]["Date"], "2025-01-02")
        self.assertEqual(rows[0]["Open"], 240.00)
        self.assertEqual(rows[0]["High"], 245.00)
        self.assertEqual(rows[0]["Low"], 238.00)
        self.assertEqual(rows[0]["Close"], 243.85)
        self.assertEqual(rows[0]["Adj Close"], 243.50)
        self.assertEqual(rows[0]["Volume"], 1000000)

        # First trading day has no previous-day return.
        self.assertIsNone(rows[0]["Daily Return (%)"])

        # Second trading day's return.
        expected_return = round(
            ((244.50 / 243.50) - 1) * 100,
            4
        )

        self.assertEqual(
            rows[1]["Daily Return (%)"],
            expected_return
        )

    def test_duplicate_dates(self):
        """Reject market data containing duplicate dates."""

        from main import validate_market_data

        rows = [
            {"Date": "2025-01-02"},
            {"Date": "2025-01-02"}
        ]

        with self.assertRaises(ValueError):
            validate_market_data(rows)

    def test_dates_not_chronological(self):
        """Reject market data that is not chronologically ordered."""

        from main import validate_market_data

        rows = [
            {"Date": "2025-01-03"},
            {"Date": "2025-01-02"}
        ]

        with self.assertRaises(ValueError):
            validate_market_data(rows)

    @patch("builtins.input")
    @patch("main.requests.get")
    def test_invalid_ticker(self, mock_get, mock_input):
        """Check that an invalid ticker produces a friendly error."""

        mock_input.side_effect = [
            "INVALIDTICKER",
            "2025-01-01",
            "2025-01-31"
        ]

        mock_response = Mock()
        mock_response.status_code = 404

        http_error = requests.HTTPError(
            "404 Client Error"
        )
        http_error.response = mock_response

        mock_get.return_value.raise_for_status.side_effect = http_error

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call(
            "Error: ticker 'INVALIDTICKER' was not found."
        )        

    @patch("builtins.input")
    @patch("main.requests.get")
    def test_network_error(self, mock_get, mock_input):
        """Check that network failures are handled gracefully."""

        mock_input.side_effect = [
            "AAPL",
            "2025-01-01",
            "2025-01-31"
        ]

        mock_get.side_effect = requests.ConnectionError(
            "Connection failed"
        )

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call(
            "Network error: Connection failed"
        )
    @patch("builtins.input")
    @patch("main.requests.get")
    def test_empty_ticker(self, mock_get, mock_input):
        """Check that an empty ticker is rejected."""

        mock_input.side_effect = [
            "",
            "2025-01-01",
            "2025-01-31"
        ]

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call(
            "Error: ticker cannot be empty."
        )

        mock_get.assert_not_called()
    def test_save_to_csv(self):
        """Check that OHLCV market data can be saved to CSV."""

        rows = [
            {
                "Date": "2025-01-02",
                "Ticker": "AAPL",
                "Open": 240.00,
                "High": 245.00,
                "Low": 238.00,
                "Close": 243.85,
                "Adj Close": 243.50,
                "Volume": 1000000,
                "Daily Return (%)": None
            }
        ]

        import tempfile
        import os
        import csv

        with tempfile.TemporaryDirectory() as temp_dir:
            original_directory = os.getcwd()

            try:
                os.chdir(temp_dir)

                filename = save_to_csv(
                    rows,
                    "AAPL",
                    "2025-01-01",
                    "2025-01-02"
                )

                self.assertTrue(os.path.exists(filename))

                with open(filename, newline="", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    saved_rows = list(reader)

                self.assertEqual(len(saved_rows), 1)
                self.assertEqual(saved_rows[0]["Ticker"], "AAPL")
                self.assertEqual(saved_rows[0]["Open"], "240.0")
                self.assertEqual(saved_rows[0]["High"], "245.0")
                self.assertEqual(saved_rows[0]["Low"], "238.0")
                self.assertEqual(saved_rows[0]["Close"], "243.85")
                self.assertEqual(saved_rows[0]["Volume"], "1000000")
                self.assertEqual(saved_rows[0]["Adj Close"], "243.5")
                self.assertEqual(saved_rows[0]["Daily Return (%)"], "")
            finally:
                os.chdir(original_directory)


if __name__ == "__main__":
    unittest.main()
