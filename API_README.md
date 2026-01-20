# Vnstock CSV Download API

A FastAPI-based REST API for downloading Vietnamese stock data as CSV files with JWT authentication.

## Features

- **JWT Authentication**: Secure token-based authentication
- **CSV Downloads**: Download stock data for single or multiple symbols
- **Date Range Support**: Specify custom date ranges for data retrieval
- **Multiple Data Sources**: Support for VCI, TCBS, and MSN data sources
- **Flexible Output**: Download as file or get as text response
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Installation

Install the required dependencies:

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart email-validator python-dotenv
```

## Configuration

Create a `.env` file in your project root:

```env
JWT_SECRET_KEY=your-super-secret-key-change-in-production
# Optional: Add other environment variables
```

## Running the API

### Development

```bash
cd vnstock/api
python rest_api.py
```

### Production

```bash
uvicorn rest_api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
    "username": "testuser",
    "password": "securepassword123"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

#### Get User Info
```http
GET /auth/me
Authorization: Bearer <your_token>
```

### CSV Downloads

#### Download Single Symbol (File)
```http
POST /api/v1/download/csv
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "symbol": "VCI",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "source": "vci",
    "interval": "D"
}
```

#### Download Single Symbol (Text Response)
```http
POST /api/v1/download/csv-text
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "symbol": "VCI",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "source": "vci",
    "interval": "D"
}
```

#### Download Multiple Symbols
```http
POST /api/v1/download/multiple
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "symbols": ["VCI", "FPT", "HPG"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "source": "vci",
    "interval": "D",
    "combine": false
}
```

### Utility Endpoints

#### Get Available Symbols
```http
GET /api/v1/symbols
Authorization: Bearer <your_token>
```

#### Health Check
```http
GET /api/v1/health
```

## Usage Examples

### Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Register user
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
}
response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print("Registration:", response.json())

# Login
login_data = {
    "username": "testuser",
    "password": "securepassword123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["access_token"]

# Set up authentication headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Download CSV data
download_data = {
    "symbol": "VCI",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "source": "vci",
    "interval": "D"
}

# Option 1: Get as text response
response = requests.post(f"{BASE_URL}/api/v1/download/csv-text", 
                        json=download_data, headers=headers)
csv_data = response.json()["csv_data"]
print("CSV Data:", csv_data[:200] + "...")

# Option 2: Download as file
response = requests.post(f"{BASE_URL}/api/v1/download/csv", 
                        json=download_data, headers=headers)
with open("VCI_stock_data.csv", "wb") as f:
    f.write(response.content)
print("File saved as VCI_stock_data.csv")
```

### JavaScript Client Example

```javascript
// Register and login
const register = async () => {
    const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'testuser',
            email: 'test@example.com',
            password: 'securepassword123'
        })
    });
    return response.json();
};

const login = async () => {
    const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'testuser',
            password: 'securepassword123'
        })
    });
    const data = await response.json();
    return data.access_token;
};

// Download CSV
const downloadCSV = async (token) => {
    const response = await fetch('http://localhost:8000/api/v1/download/csv-text', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: 'VCI',
            start_date: '2024-01-01',
            end_date: '2024-12-31',
            source: 'vci',
            interval: 'D'
        })
    });
    const data = await response.json();
    console.log('CSV Data:', data.csv_data);
    return data;
};

// Usage
(async () => {
    await register();
    const token = await login();
    const csvData = await downloadCSV(token);
})();
```

### cURL Examples

```bash
# Register
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"securepassword123"}'

# Login
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
             -H "Content-Type: application/json" \
             -d '{"username":"testuser","password":"securepassword123"}' \
             | jq -r '.access_token')

# Download CSV as text
curl -X POST "http://localhost:8000/api/v1/download/csv-text" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"symbol":"VCI","start_date":"2024-01-01","end_date":"2024-12-31","source":"vci","interval":"D"}'

# Download CSV as file
curl -X POST "http://localhost:8000/api/v1/download/csv" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"symbol":"VCI","start_date":"2024-01-01","end_date":"2024-12-31","source":"vci","interval":"D"}' \
     --output VCI_stock_data.csv
```

## Security Considerations

1. **JWT Secret Key**: Change the default `JWT_SECRET_KEY` in production
2. **HTTPS**: Use HTTPS in production environments
3. **CORS**: Configure CORS appropriately for your use case
4. **Rate Limiting**: Consider adding rate limiting for API endpoints
5. **Database**: Replace in-memory user storage with a proper database
6. **Input Validation**: All inputs are validated using Pydantic models

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found
- `500`: Internal Server Error

Error responses include detailed error messages:

```json
{
    "detail": "Error downloading CSV: Invalid date format"
}
```

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use proper environment variable management
2. **Database**: Replace in-memory storage with PostgreSQL/MySQL
3. **Caching**: Add Redis for caching frequent requests
4. **Monitoring**: Add logging and monitoring
5. **Load Balancing**: Deploy behind a load balancer
6. **Containerization**: Use Docker for deployment

## License

This API is part of the vnstock project and follows the same license terms.
