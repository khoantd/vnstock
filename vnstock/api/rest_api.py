"""
vnstock/api/rest_api.py

FastAPI application for CSV download with JWT authentication.
"""

from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from vnstock.api.download import Download
from vnstock.api.company import Company
from vnstock.api.financial import Finance
from vnstock.api.trading import Trading

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI(
    title="Vnstock Comprehensive API",
    description="API for Vietnamese stock data including company info, financial reports, trading data, and CSV downloads with JWT authentication",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory user database (replace with proper database in production)
users_db = {}

# Pydantic models
class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class CSVDownloadRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    source: str = "vci"
    interval: str = "D"

class MultipleCSVRequest(BaseModel):
    symbols: List[str]
    start_date: str
    end_date: str
    source: str = "vci"
    interval: str = "D"
    combine: bool = False

# Company API models
class CompanyRequest(BaseModel):
    symbol: str
    source: str = "vci"
    random_agent: bool = False
    show_log: bool = False

class CompanyOfficersRequest(BaseModel):
    symbol: str
    source: str = "vci"
    filter_by: str = "all"  # "working", "resigned", "all"
    random_agent: bool = False
    show_log: bool = False

class CompanySubsidiariesRequest(BaseModel):
    symbol: str
    source: str = "vci"
    filter_by: str = "all"  # "all", "subsidiary"
    random_agent: bool = False
    show_log: bool = False

# Financial API models
class FinancialRequest(BaseModel):
    symbol: str
    source: str = "vci"
    period: str = "quarter"  # "quarter", "annual"
    get_all: bool = True
    show_log: bool = False

class FinancialReportRequest(BaseModel):
    symbol: str
    source: str = "vci"
    period: str = "quarter"
    lang: str = "vi"  # "vi", "en"
    dropna: bool = True
    get_all: bool = True
    show_log: bool = False

class FinancialRatioRequest(BaseModel):
    symbol: str
    source: str = "vci"
    period: str = "quarter"
    flatten_columns: bool = True
    separator: str = "_"
    get_all: bool = True
    show_log: bool = False

# Trading API models
class TradingRequest(BaseModel):
    symbol: str
    source: str = "vci"
    random_agent: bool = False
    show_log: bool = False

class TradingStatsRequest(BaseModel):
    symbol: str
    source: str = "vci"
    start: str = None
    end: str = None
    limit: int = 1000
    random_agent: bool = False
    show_log: bool = False

class PriceBoardRequest(BaseModel):
    symbols_list: List[str]
    source: str = "vci"
    random_agent: bool = False
    show_log: bool = False

class PriceHistoryRequest(BaseModel):
    symbol: str
    source: str = "vci"
    start: str = None
    end: str = None
    interval: str = "D"
    random_agent: bool = False
    show_log: bool = False

# Helper functions
def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    """Hash a password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and extract user information."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    if token_data.username not in users_db:
        raise credentials_exception
    
    return token_data.username

# Authentication endpoints
@app.post("/auth/register", response_model=dict)
async def register(user: User):
    """Register a new user."""
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password and store user
    hashed_password = get_password_hash(user.password)
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    return {"message": "User registered successfully", "username": user.username}

@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token."""
    user = users_db.get(user_credentials.username)
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_users_me(current_user: str = Depends(verify_token)):
    """Get current user information."""
    user = users_db[current_user]
    return {
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"]
    }

# CSV Download endpoints
@app.post("/api/v1/download/csv")
async def download_csv(
    request: CSVDownloadRequest,
    current_user: str = Depends(verify_token)
):
    """Download stock data as CSV file."""
    try:
        dl = Download(source=request.source, show_log=False)
        csv_data = dl.to_csv(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        # Create streaming response
        csv_stream = io.StringIO(csv_data)
        filename = f"{request.symbol}_{request.start_date}_{request.end_date}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_data.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error downloading CSV: {str(e)}"
        )

@app.post("/api/v1/download/csv-text")
async def download_csv_text(
    request: CSVDownloadRequest,
    current_user: str = Depends(verify_token)
):
    """Get stock data as CSV text (for API responses)."""
    try:
        dl = Download(source=request.source, show_log=False)
        csv_data = dl.to_csv(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        return {
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "csv_data": csv_data,
            "data_size": len(csv_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error downloading CSV: {str(e)}"
        )

@app.post("/api/v1/download/multiple")
async def download_multiple_csv(
    request: MultipleCSVRequest,
    current_user: str = Depends(verify_token)
):
    """Download multiple stock symbols as CSV."""
    try:
        dl = Download(source=request.source, show_log=False)
        
        if request.combine:
            # Combined CSV download
            csv_data = dl.download_multiple(
                symbols=request.symbols,
                start_date=request.start_date,
                end_date=request.end_date,
                interval=request.interval,
                combine=True
            )
            
            filename = f"combined_{request.start_date}_{request.end_date}.csv"
            
            return StreamingResponse(
                io.BytesIO(csv_data.encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Separate CSV data as JSON response
            csv_dict = dl.download_multiple(
                symbols=request.symbols,
                start_date=request.start_date,
                end_date=request.end_date,
                interval=request.interval,
                combine=False
            )
            
            return {
                "symbols": request.symbols,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "csv_data": csv_dict,
                "total_symbols": len(request.symbols)
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error downloading multiple CSV: {str(e)}"
        )

@app.get("/api/v1/symbols")
async def get_available_symbols(current_user: str = Depends(verify_token)):
    """Get list of available stock symbols (basic implementation)."""
    # This is a basic implementation - in production, you'd fetch from your data source
    common_symbols = [
        "VCB", "FPT", "HPG", "MWG", "VNM", "VIC", "BID", "CTG", "TCB", "ACB",
        "HDB", "MBB", "STB", "TPB", "VGI", "SAB", "PLX", "GAS", "POW", "REE"
    ]
    
    return {
        "symbols": common_symbols,
        "total": len(common_symbols),
        "note": "This is a basic list. In production, fetch from your data source."
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

# Company Information endpoints
@app.post("/api/v1/company/overview")
async def get_company_overview(
    request: CompanyRequest,
    current_user: str = Depends(verify_token)
):
    """Get company overview information."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.overview()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching company overview: {str(e)}"
        )

@app.post("/api/v1/company/shareholders")
async def get_company_shareholders(
    request: CompanyRequest,
    current_user: str = Depends(verify_token)
):
    """Get company shareholders information."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.shareholders()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching shareholders: {str(e)}"
        )

@app.post("/api/v1/company/officers")
async def get_company_officers(
    request: CompanyOfficersRequest,
    current_user: str = Depends(verify_token)
):
    """Get company officers information."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.officers(filter_by=request.filter_by)
        return {
            "symbol": request.symbol,
            "filter_by": request.filter_by,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching officers: {str(e)}"
        )

@app.post("/api/v1/company/subsidiaries")
async def get_company_subsidiaries(
    request: CompanySubsidiariesRequest,
    current_user: str = Depends(verify_token)
):
    """Get company subsidiaries information."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.subsidiaries(filter_by=request.filter_by)
        return {
            "symbol": request.symbol,
            "filter_by": request.filter_by,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching subsidiaries: {str(e)}"
        )

@app.post("/api/v1/company/affiliate")
async def get_company_affiliate(
    request: CompanyRequest,
    current_user: str = Depends(verify_token)
):
    """Get company affiliate information."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.affiliate()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching affiliate: {str(e)}"
        )

@app.post("/api/v1/company/news")
async def get_company_news(
    request: CompanyRequest,
    current_user: str = Depends(verify_token)
):
    """Get company news."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.news()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching news: {str(e)}"
        )

@app.post("/api/v1/company/events")
async def get_company_events(
    request: CompanyRequest,
    current_user: str = Depends(verify_token)
):
    """Get company events."""
    try:
        company = Company(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = company.events()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching events: {str(e)}"
        )

# Financial Information endpoints
@app.post("/api/v1/financial/balance-sheet")
async def get_balance_sheet(
    request: FinancialReportRequest,
    current_user: str = Depends(verify_token)
):
    """Get balance sheet data."""
    try:
        finance = Finance(
            source=request.source,
            symbol=request.symbol,
            period=request.period,
            get_all=request.get_all,
            show_log=request.show_log
        )
        data = finance.balance_sheet(lang=request.lang, dropna=request.dropna)
        return {
            "symbol": request.symbol,
            "period": request.period,
            "lang": request.lang,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching balance sheet: {str(e)}"
        )

@app.post("/api/v1/financial/income-statement")
async def get_income_statement(
    request: FinancialReportRequest,
    current_user: str = Depends(verify_token)
):
    """Get income statement data."""
    try:
        finance = Finance(
            source=request.source,
            symbol=request.symbol,
            period=request.period,
            get_all=request.get_all,
            show_log=request.show_log
        )
        data = finance.income_statement(lang=request.lang, dropna=request.dropna)
        return {
            "symbol": request.symbol,
            "period": request.period,
            "lang": request.lang,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching income statement: {str(e)}"
        )

@app.post("/api/v1/financial/cash-flow")
async def get_cash_flow(
    request: FinancialReportRequest,
    current_user: str = Depends(verify_token)
):
    """Get cash flow data."""
    try:
        finance = Finance(
            source=request.source,
            symbol=request.symbol,
            period=request.period,
            get_all=request.get_all,
            show_log=request.show_log
        )
        data = finance.cash_flow(lang=request.lang, dropna=request.dropna)
        return {
            "symbol": request.symbol,
            "period": request.period,
            "lang": request.lang,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching cash flow: {str(e)}"
        )

@app.post("/api/v1/financial/ratios")
async def get_financial_ratios(
    request: FinancialRatioRequest,
    current_user: str = Depends(verify_token)
):
    """Get financial ratio data."""
    try:
        finance = Finance(
            source=request.source,
            symbol=request.symbol,
            period=request.period,
            get_all=request.get_all,
            show_log=request.show_log
        )
        data = finance.ratio(
            flatten_columns=request.flatten_columns,
            separator=request.separator
        )
        return {
            "symbol": request.symbol,
            "period": request.period,
            "flatten_columns": request.flatten_columns,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching financial ratios: {str(e)}"
        )

# Trading Data endpoints
@app.post("/api/v1/trading/stats")
async def get_trading_stats(
    request: TradingStatsRequest,
    current_user: str = Depends(verify_token)
):
    """Get trading statistics."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.trading_stats(start=request.start, end=request.end, limit=request.limit)
        return {
            "symbol": request.symbol,
            "start": request.start,
            "end": request.end,
            "limit": request.limit,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching trading stats: {str(e)}"
        )

@app.post("/api/v1/trading/side-stats")
async def get_side_stats(
    request: TradingRequest,
    current_user: str = Depends(verify_token)
):
    """Get bid/ask side statistics."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.side_stats(dropna=True)
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching side stats: {str(e)}"
        )

@app.post("/api/v1/trading/price-board")
async def get_price_board(
    request: PriceBoardRequest,
    current_user: str = Depends(verify_token)
):
    """Get price board for multiple symbols."""
    try:
        trading = Trading(
            source=request.source,
            symbol="",
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.price_board(symbols_list=request.symbols_list)
        return {
            "symbols": request.symbols_list,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching price board: {str(e)}"
        )

@app.post("/api/v1/trading/price-history")
async def get_price_history(
    request: PriceHistoryRequest,
    current_user: str = Depends(verify_token)
):
    """Get price history for a symbol."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.price_history(start=request.start, end=request.end, interval=request.interval)
        return {
            "symbol": request.symbol,
            "start": request.start,
            "end": request.end,
            "interval": request.interval,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching price history: {str(e)}"
        )

@app.post("/api/v1/trading/foreign-trade")
async def get_foreign_trade(
    request: TradingRequest,
    current_user: str = Depends(verify_token)
):
    """Get foreign trade data."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.foreign_trade()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching foreign trade: {str(e)}"
        )

@app.post("/api/v1/trading/prop-trade")
async def get_prop_trade(
    request: TradingRequest,
    current_user: str = Depends(verify_token)
):
    """Get property trade data."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.prop_trade()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching prop trade: {str(e)}"
        )

@app.post("/api/v1/trading/insider-deal")
async def get_insider_deal(
    request: TradingRequest,
    current_user: str = Depends(verify_token)
):
    """Get insider deal data."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.insider_deal()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching insider deal: {str(e)}"
        )

@app.post("/api/v1/trading/order-stats")
async def get_order_stats(
    request: TradingRequest,
    current_user: str = Depends(verify_token)
):
    """Get order statistics."""
    try:
        trading = Trading(
            source=request.source,
            symbol=request.symbol,
            random_agent=request.random_agent,
            show_log=request.show_log
        )
        data = trading.order_stats()
        return {
            "symbol": request.symbol,
            "data": data.to_dict() if hasattr(data, 'to_dict') else data,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching order stats: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Vnstock Comprehensive API",
        "version": "2.0.0",
        "docs": "/docs",
        "auth": {
            "register": "/auth/register",
            "login": "/auth/login",
            "me": "/auth/me"
        },
        "endpoints": {
            "download_csv": "/api/v1/download/csv",
            "download_csv_text": "/api/v1/download/csv-text",
            "download_multiple": "/api/v1/download/multiple",
            "symbols": "/api/v1/symbols",
            "health": "/api/v1/health",
            "company": {
                "overview": "/api/v1/company/overview",
                "shareholders": "/api/v1/company/shareholders",
                "officers": "/api/v1/company/officers",
                "subsidiaries": "/api/v1/company/subsidiaries",
                "affiliate": "/api/v1/company/affiliate",
                "news": "/api/v1/company/news",
                "events": "/api/v1/company/events"
            },
            "financial": {
                "balance_sheet": "/api/v1/financial/balance-sheet",
                "income_statement": "/api/v1/financial/income-statement",
                "cash_flow": "/api/v1/financial/cash-flow",
                "ratios": "/api/v1/financial/ratios"
            },
            "trading": {
                "stats": "/api/v1/trading/stats",
                "side_stats": "/api/v1/trading/side-stats",
                "price_board": "/api/v1/trading/price-board",
                "price_history": "/api/v1/trading/price-history",
                "foreign_trade": "/api/v1/trading/foreign-trade",
                "prop_trade": "/api/v1/trading/prop-trade",
                "insider_deal": "/api/v1/trading/insider-deal",
                "order_stats": "/api/v1/trading/order-stats"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
