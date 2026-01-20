"""
vnstock/api/download.py

API for downloading stock data as CSV files with date range support.
"""

import os
import io
from datetime import datetime, timedelta
from typing import Optional, Union, List
import pandas as pd
from pydantic import BaseModel, validator
from tenacity import retry, stop_after_attempt, wait_exponential
from vnstock.config import Config
from vnstock.core.types import DataSource, TimeFrame


class DownloadRequest(BaseModel):
    """Model for download request validation."""
    symbol: str
    start_date: str
    end_date: str
    source: str = DataSource.VCI
    interval: str = TimeFrame.DAILY
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Symbol must be at least 3 characters')
        return v.upper()
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        # Try DD-MM-YYYY format first (preferred format)
        try:
            datetime.strptime(v, '%d-%m-%Y')
            return v
        except ValueError:
            pass
        
        # Fallback to YYYY-MM-DD format for backward compatibility
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in DD-MM-YYYY or YYYY-MM-DD format')
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values:
            # Parse dates - try DD-MM-YYYY first, then YYYY-MM-DD
            start_str = values['start_date']
            end_str = v
            
            try:
                start = datetime.strptime(start_str, '%d-%m-%Y')
            except ValueError:
                start = datetime.strptime(start_str, '%Y-%m-%d')
            
            try:
                end = datetime.strptime(end_str, '%d-%m-%Y')
            except ValueError:
                end = datetime.strptime(end_str, '%Y-%m-%d')
            
            if end < start:
                raise ValueError('End date must be after start date')
            if (end - start).days > 365 * 5:  # 5 years max
                raise ValueError('Date range cannot exceed 5 years')
        return v
    
    @validator('source')
    def validate_source(cls, v):
        valid_sources = DataSource.all_sources()
        if v.lower() not in [s.lower() for s in valid_sources]:
            sources_str = ', '.join(valid_sources)
            raise ValueError(f'Source must be one of: {sources_str}')
        return v


class Download:
    """
    Adapter for downloading stock data as CSV files.
    
    Usage:
        dl = Download(source="vci", symbol="VCI")
        csv_data = dl.to_csv(start_date="2024-01-01", end_date="2024-12-31")
        dl.save_csv(start_date="2024-01-01", end_date="2024-12-31", filename="VCI_2024.csv")
    """
    
    def __init__(
        self,
        source: str = DataSource.VCI,
        symbol: str = "",
        random_agent: bool = False,
        show_log: bool = False
    ):
        """
        Initialize a Download instance.
        
        Args:
            source (str): Data source (VCI, TCBS, MSN)
            symbol (str): Stock symbol
            random_agent (bool): Use random user agent for requests
            show_log (bool): Show log messages
        """
        self.source = source
        self.symbol = symbol if symbol else ""
        self.random_agent = random_agent
        self.show_log = show_log
        
        # Validate source
        all_sources = DataSource.all_sources()
        if source.lower() not in [s.lower() for s in all_sources]:
            sources_str = ', '.join(all_sources)
            raise ValueError(f"Download class only accepts source values: {sources_str}")

    @retry(
        stop=stop_after_attempt(Config.RETRIES),
        wait=wait_exponential(
            multiplier=Config.BACKOFF_MULTIPLIER,
            min=Config.BACKOFF_MIN,
            max=Config.BACKOFF_MAX
        )
    )
    def to_csv(
        self,
        symbol: Optional[str] = None,
        start_date: str = None,
        end_date: str = None,
        interval: str = TimeFrame.DAILY,
        **kwargs
    ) -> str:
        """
        Get stock data as CSV string for the specified date range.
        
        Args:
            symbol (str, optional): Stock symbol
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            interval (str): Data interval (D, 1W, 1M, 1m, 5m, 15m, 30m, 1H)
            **kwargs: Additional parameters
            
        Returns:
            str: CSV formatted data
            
        Raises:
            ValueError: If parameters are invalid
            NetworkError: If data fetch fails
            
        Examples:
            >>> dl = Download(symbol="VCI")
            >>> csv_data = dl.to_csv(start_date="2024-01-01", end_date="2024-12-31")
            >>> csv_data = dl.to_csv(symbol="FPT", start_date="2024-01-01", end_date="2024-04-18", interval="1W")
        """
        # Validate request
        request = DownloadRequest(
            symbol=symbol or self.symbol,
            start_date=start_date,
            end_date=end_date,
            source=self.source,
            interval=interval
        )
        
        # Convert dates to YYYY-MM-DD format for internal processing if needed
        start_date_formatted = self._normalize_date_format(request.start_date)
        end_date_formatted = self._normalize_date_format(request.end_date)
        
        # Fetch historical data
        df = self._fetch_historical_data(
            symbol=request.symbol,
            start_date=start_date_formatted,
            end_date=end_date_formatted,
            interval=request.interval,
            **kwargs
        )
        
        # Format dates to YYYY-MM-DD format
        df = self._format_dates_for_csv(df)
        
        # Add ticket column (stock symbol) after Date column
        df = self._add_ticket_column(df, request.symbol)
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=True, encoding='utf-8')
        return csv_buffer.getvalue()

    @retry(
        stop=stop_after_attempt(Config.RETRIES),
        wait=wait_exponential(
            multiplier=Config.BACKOFF_MULTIPLIER,
            min=Config.BACKOFF_MIN,
            max=Config.BACKOFF_MAX
        )
    )
    def save_csv(
        self,
        symbol: Optional[str] = None,
        start_date: str = None,
        end_date: str = None,
        filename: Optional[str] = None,
        interval: str = TimeFrame.DAILY,
        path: str = ".",
        **kwargs
    ) -> str:
        """
        Save stock data as CSV file for the specified date range.
        
        Args:
            symbol (str, optional): Stock symbol
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            filename (str, optional): Output filename. If None, auto-generated.
            interval (str): Data interval
            path (str): Directory to save the file
            **kwargs: Additional parameters
            
        Returns:
            str: Full path to saved file
            
        Examples:
            >>> dl = Download(symbol="VCI")
            >>> filepath = dl.save_csv(start_date="2024-01-01", end_date="2024-12-31")
            >>> filepath = dl.save_csv(symbol="FPT", start_date="2024-01-01", end_date="2024-04-18", 
            ...                       filename="FPT_Q1_2024.csv")
        """
        # Validate request
        request = DownloadRequest(
            symbol=symbol or self.symbol,
            start_date=start_date,
            end_date=end_date,
            source=self.source,
            interval=interval
        )
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{request.symbol}_{request.start_date}_{request.end_date}_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Convert dates to YYYY-MM-DD format for internal processing if needed
        start_date_formatted = self._normalize_date_format(request.start_date)
        end_date_formatted = self._normalize_date_format(request.end_date)
        
        # Fetch data
        df = self._fetch_historical_data(
            symbol=request.symbol,
            start_date=start_date_formatted,
            end_date=end_date_formatted,
            interval=request.interval,
            **kwargs
        )
        
        # Format dates to YYYY-MM-DD format
        df = self._format_dates_for_csv(df)
        
        # Add ticket column (stock symbol) after Date column
        df = self._add_ticket_column(df, request.symbol)
        
        # Save to file
        filepath = os.path.join(path, filename)
        df.to_csv(filepath, index=True, encoding='utf-8')
        
        if self.show_log:
            print(f"CSV file saved to: {filepath}")
        
        return filepath

    @retry(
        stop=stop_after_attempt(Config.RETRIES),
        wait=wait_exponential(
            multiplier=Config.BACKOFF_MULTIPLIER,
            min=Config.BACKOFF_MIN,
            max=Config.BACKOFF_MAX
        )
    )
    def download_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = TimeFrame.DAILY,
        combine: bool = False,
        **kwargs
    ) -> Union[str, dict]:
        """
        Download data for multiple symbols.
        
        Args:
            symbols (List[str]): List of stock symbols
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            interval (str): Data interval
            combine (bool): If True, combine all data into single CSV
            **kwargs: Additional parameters
            
        Returns:
            Union[str, dict]: CSV string if combine=True, dict of CSV strings otherwise
            
        Examples:
            >>> dl = Download()
            >>> csv_data = dl.download_multiple(["VCI", "FPT"], "2024-01-01", "2024-12-31", combine=True)
            >>> csv_dict = dl.download_multiple(["VCI", "FPT"], "2024-01-01", "2024-12-31")
        """
        if combine:
            all_data = []
            
            # Normalize date formats
            start_date_formatted = self._normalize_date_format(start_date)
            end_date_formatted = self._normalize_date_format(end_date)
            
            for symbol in symbols:
                try:
                    df = self._fetch_historical_data(
                        symbol=symbol,
                        start_date=start_date_formatted,
                        end_date=end_date_formatted,
                        interval=interval,
                        **kwargs
                    )
                    if not df.empty:
                        # Format dates and add ticket column
                        df = self._format_dates_for_csv(df)
                        df = self._add_ticket_column(df, symbol)
                        all_data.append(df)
                except Exception as e:
                    if self.show_log:
                        print(f"Failed to fetch data for {symbol}: {e}")
                    continue
            
            if not all_data:
                raise ValueError("No data could be fetched for any symbols")
            
            combined_df = pd.concat(all_data, ignore_index=False)
            # Dates and ticket columns are already formatted and added per symbol
            # Just ensure proper column order if needed
            csv_buffer = io.StringIO()
            combined_df.to_csv(csv_buffer, index=True, encoding='utf-8')
            return csv_buffer.getvalue()
        else:
            result = {}
            # Normalize date formats
            start_date_formatted = self._normalize_date_format(start_date)
            end_date_formatted = self._normalize_date_format(end_date)
            
            for symbol in symbols:
                try:
                    csv_data = self.to_csv(
                        symbol=symbol,
                        start_date=start_date_formatted,
                        end_date=end_date_formatted,
                        interval=interval,
                        **kwargs
                    )
                    result[symbol] = csv_data
                except Exception as e:
                    if self.show_log:
                        print(f"Failed to fetch data for {symbol}: {e}")
                    result[symbol] = None
            
            return result

    def _add_ticket_column(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Add ticket column (stock symbol) after Date column in the DataFrame.
        When exported to CSV with index=True, the date index will be first column,
        then ticket, then other columns.
        
        Args:
            df (pd.DataFrame): DataFrame with date columns/index
            symbol (str): Stock symbol to add in ticket column
            
        Returns:
            pd.DataFrame: DataFrame with ticket column added after Date
        """
        if df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        df_with_ticket = df.copy()
        
        # Check if date is in index (most common case for VCI data)
        date_is_index = False
        if isinstance(df_with_ticket.index, pd.Index) and len(df_with_ticket.index) > 0:
            # Check if index contains date-like values (strings in YYYY-MM-DD format or datetime)
            sample_idx = df_with_ticket.index[0] if len(df_with_ticket.index) > 0 else None
            if sample_idx is not None:
                # Check if it looks like a date (string in YYYY-MM-DD format or datetime)
                if isinstance(sample_idx, str) and len(sample_idx) == 10 and sample_idx[4] == '-' and sample_idx[7] == '-':
                    date_is_index = True
                elif pd.api.types.is_datetime64_any_dtype(df_with_ticket.index):
                    date_is_index = True
        
        # Determine the date column name
        date_col_name = None
        
        # Check for 'Date' column
        if 'Date' in df_with_ticket.columns:
            date_col_name = 'Date'
        # Check for 'time' column
        elif 'time' in df_with_ticket.columns:
            date_col_name = 'time'
        
        # Add ticket column with stock symbol
        df_with_ticket['ticket'] = symbol
        
        # Reorder columns to put ticket after Date column (if Date is a column)
        if date_col_name and date_col_name in df_with_ticket.columns:
            # Get column order
            cols = df_with_ticket.columns.tolist()
            # Remove ticket from current position
            cols.remove('ticket')
            # Find Date column index
            date_idx = cols.index(date_col_name)
            # Insert ticket after Date
            cols.insert(date_idx + 1, 'ticket')
            df_with_ticket = df_with_ticket[cols]
        elif date_is_index:
            # If date is in index, when exported with index=True, the CSV will have:
            # Date (index), ticket, open, high, low, close, volume
            # So ticket should be first column in the DataFrame
            cols = df_with_ticket.columns.tolist()
            cols.remove('ticket')
            cols.insert(0, 'ticket')
            df_with_ticket = df_with_ticket[cols]
        # If no date column found, ticket will be added at the end (shouldn't happen normally)
        
        return df_with_ticket
    
    def _format_dates_for_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format date columns and index to YYYY-MM-DD format for CSV export.
        
        Args:
            df (pd.DataFrame): DataFrame with date columns/index
            
        Returns:
            pd.DataFrame: DataFrame with dates formatted as YYYY-MM-DD
        """
        if df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        df_formatted = df.copy()
        
        # Format datetime index to YYYY-MM-DD
        if isinstance(df_formatted.index, pd.DatetimeIndex):
            df_formatted.index = df_formatted.index.strftime('%Y-%m-%d')
        elif hasattr(df_formatted.index, 'dtype') and pd.api.types.is_datetime64_any_dtype(df_formatted.index):
            # Convert to DatetimeIndex first, then format
            df_formatted.index = pd.DatetimeIndex(df_formatted.index).strftime('%Y-%m-%d')
        
        # Format 'time' column if it exists
        if 'time' in df_formatted.columns:
            if pd.api.types.is_datetime64_any_dtype(df_formatted['time']):
                df_formatted['time'] = pd.to_datetime(df_formatted['time']).dt.strftime('%Y-%m-%d')
            elif df_formatted['time'].dtype == 'object':
                # Try to parse and reformat if it's a string
                try:
                    df_formatted['time'] = pd.to_datetime(df_formatted['time']).dt.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    pass  # If parsing fails, leave as is
        
        # Format 'Date' column if it exists (some sources use 'Date' instead of 'time')
        if 'Date' in df_formatted.columns:
            if pd.api.types.is_datetime64_any_dtype(df_formatted['Date']):
                df_formatted['Date'] = pd.to_datetime(df_formatted['Date']).dt.strftime('%Y-%m-%d')
            elif df_formatted['Date'].dtype == 'object':
                # Try to parse and reformat if it's a string
                try:
                    df_formatted['Date'] = pd.to_datetime(df_formatted['Date']).dt.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    pass  # If parsing fails, leave as is
        
        return df_formatted

    def _normalize_date_format(self, date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format.
        Accepts both DD-MM-YYYY and YYYY-MM-DD formats.
        """
        try:
            # Try DD-MM-YYYY format first
            dt = datetime.strptime(date_str, '%d-%m-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                raise ValueError(f'Invalid date format: {date_str}. Use DD-MM-YYYY or YYYY-MM-DD')
    
    def _fetch_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = TimeFrame.DAILY,
        **kwargs
    ) -> pd.DataFrame:
        """
        Internal method to fetch historical data using Quote adapter.
        
        Args:
            symbol (str): Stock symbol
            start_date (str): Start date
            end_date (str): End date
            interval (str): Data interval
            **kwargs: Additional parameters
            
        Returns:
            pd.DataFrame: Historical price data
        """
        from vnstock.api.quote import Quote
        
        # Create Quote instance with same configuration
        quote = Quote(
            source=self.source,
            symbol=symbol,
            random_agent=self.random_agent,
            show_log=self.show_log
        )
        
        # Fetch historical data
        df = quote.history(
            symbol=symbol,
            start=start_date,
            end=end_date,
            interval=interval,
            **kwargs
        )
        
        return df
