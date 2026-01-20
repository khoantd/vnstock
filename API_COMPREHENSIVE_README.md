# Vnstock Comprehensive API Documentation

## Overview

The Vnstock Comprehensive API provides REST endpoints for accessing Vietnamese stock market data including:
- Company information
- Financial reports
- Trading data
- CSV downloads

## Authentication

All API endpoints (except health check) require JWT authentication.

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "your_username",
  "email": "your_email@example.com", 
  "password": "your_password"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

## API Endpoints

### Company Information

#### Get Company Overview
```http
POST /api/v1/company/overview
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "random_agent": false,
  "show_log": false
}
```

#### Get Shareholders
```http
POST /api/v1/company/shareholders
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Officers
```http
POST /api/v1/company/officers
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "filter_by": "all"
}
```

#### Get Subsidiaries
```http
POST /api/v1/company/subsidiaries
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "filter_by": "all"
}
```

#### Get Affiliate Information
```http
POST /api/v1/company/affiliate
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Company News
```http
POST /api/v1/company/news
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Company Events
```http
POST /api/v1/company/events
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

### Financial Information

#### Get Balance Sheet
```http
POST /api/v1/financial/balance-sheet
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "period": "quarter",
  "lang": "vi",
  "dropna": true,
  "get_all": true,
  "show_log": false
}
```

#### Get Income Statement
```http
POST /api/v1/financial/income-statement
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "period": "quarter",
  "lang": "vi",
  "dropna": true,
  "get_all": true,
  "show_log": false
}
```

#### Get Cash Flow
```http
POST /api/v1/financial/cash-flow
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "period": "quarter",
  "lang": "vi",
  "dropna": true,
  "get_all": true,
  "show_log": false
}
```

#### Get Financial Ratios
```http
POST /api/v1/financial/ratios
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "period": "quarter",
  "flatten_columns": true,
  "separator": "_",
  "get_all": true,
  "show_log": false
}
```

### Trading Data

#### Get Trading Statistics
```http
POST /api/v1/trading/stats
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "start": "2024-01-01",
  "end": "2024-12-31",
  "limit": 1000,
  "random_agent": false,
  "show_log": false
}
```

#### Get Side Statistics (Bid/Ask)
```http
POST /api/v1/trading/side-stats
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Price Board
```http
POST /api/v1/trading/price-board
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbols_list": ["VCB", "FPT", "HPG"],
  "source": "vci"
}
```

#### Get Price History
```http
POST /api/v1/trading/price-history
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci",
  "start": "2024-01-01",
  "end": "2024-12-31",
  "interval": "D"
}
```

#### Get Foreign Trade Data
```http
POST /api/v1/trading/foreign-trade
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Property Trade Data
```http
POST /api/v1/trading/prop-trade
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Insider Deal Data
```http
POST /api/v1/trading/insider-deal
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

#### Get Order Statistics
```http
POST /api/v1/trading/order-stats
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "source": "vci"
}
```

### CSV Downloads (Existing)

#### Download Single Symbol CSV
```http
POST /api/v1/download/csv
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "VCB",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "source": "vci",
  "interval": "D"
}
```

#### Download Multiple Symbols CSV
```http
POST /api/v1/download/multiple
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbols": ["VCB", "FPT", "HPG"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "source": "vci",
  "interval": "D",
  "combine": false
}
```

## Response Format

All endpoints return JSON in the following format:

```json
{
  "symbol": "VCB",
  "data": {...}, // Actual data or pandas DataFrame converted to dict
  "source": "vci",
  // Additional fields depending on endpoint
}
```

## Error Handling

Errors return HTTP status codes with detailed messages:

```json
{
  "detail": "Error description here"
}
```

Common error codes:
- 401: Unauthorized (invalid/missing token)
- 400: Bad Request (invalid parameters, data fetch errors)
- 500: Internal Server Error

## Running the API Server

Start the API server:

```bash
# Using the module
python -m vnstock.api.rest_api

# Or directly
python vnstock/api/rest_api.py
```

The server will start on `http://localhost:8001`

## Interactive Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Testing

Use the provided test script:

```bash
python test_api.py
```

This will test authentication and sample endpoints for each category.

## Data Sources

The API supports multiple data sources:
- `vci`: Vietnam Capital Investments (default)
- `tcbs`: Techcom Securities

## Rate Limiting

The API includes retry logic and exponential backoff for network requests to handle rate limiting from data sources.

## Security Notes

- Use HTTPS in production
- Change the default JWT secret key
- Implement proper user authentication/database
- Configure CORS appropriately for your use case
