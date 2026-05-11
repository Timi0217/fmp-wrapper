import os
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
import httpx


FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
BASE_URL = "https://financialmodelingprep.com/api/v3"

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await http_client.aclose()


app = FastAPI(title="Financial Modeling Prep Wrapper", lifespan=lifespan)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_key() -> str:
    key = FMP_API_KEY or os.environ.get("FMP_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="FMP_API_KEY not configured")
    return key


async def _fmp_request(path: str, params: dict | None = None) -> dict | list:
    """Make a request to FMP API."""
    if params is None:
        params = {}
    params["apikey"] = _get_key()
    url = f"{BASE_URL}{path}"

    try:
        response = await http_client.get(url, params=params)
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="FMP rate limit exceeded")
        if response.status_code == 403:
            raise HTTPException(status_code=503, detail="FMP API key invalid or plan limit reached")
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("Error Message"):
            raise HTTPException(status_code=404, detail=data["Error Message"])

        return data
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unexpected error: {str(e)}")


# ── Endpoints ────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return {
        "name": "Financial Modeling Prep Wrapper",
        "description": "Financial statements, ratios, DCF valuations, company profiles, and stock screening from FMP",
        "endpoints": [
            {"path": "/profile?symbol=AAPL", "description": "Company profile"},
            {"path": "/income?symbol=AAPL", "description": "Income statement"},
            {"path": "/balance?symbol=AAPL", "description": "Balance sheet"},
            {"path": "/cashflow?symbol=AAPL", "description": "Cash flow statement"},
            {"path": "/ratios?symbol=AAPL", "description": "Financial ratios"},
            {"path": "/dcf?symbol=AAPL", "description": "DCF valuation"},
            {"path": "/metrics?symbol=AAPL", "description": "Key financial metrics"},
            {"path": "/search?query=apple", "description": "Search companies"},
            {"path": "/health", "description": "Health check"},
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": _ts()}


@app.get("/profile")
async def get_profile(symbol: str = Query(..., description="Stock symbol (e.g., AAPL)")):
    """Get company profile."""
    data = await _fmp_request(f"/profile/{symbol.upper()}")
    if not data:
        raise HTTPException(status_code=404, detail=f"No profile for {symbol}")

    p = data[0] if isinstance(data, list) else data
    return {
        "symbol": p.get("symbol"),
        "name": p.get("companyName"),
        "exchange": p.get("exchangeShortName"),
        "sector": p.get("sector"),
        "industry": p.get("industry"),
        "market_cap": p.get("mktCap"),
        "price": p.get("price"),
        "beta": p.get("beta"),
        "vol_avg": p.get("volAvg"),
        "description": p.get("description"),
        "ceo": p.get("ceo"),
        "country": p.get("country"),
        "employees": p.get("fullTimeEmployees"),
        "ipo_date": p.get("ipoDate"),
        "website": p.get("website"),
        "image": p.get("image"),
        "timestamp": _ts(),
    }


@app.get("/income")
async def get_income(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("annual", description="annual or quarter"),
    limit: int = Query(4, description="Number of periods", ge=1, le=40),
):
    """Get income statement."""
    data = await _fmp_request(f"/income-statement/{symbol.upper()}", {"period": period, "limit": limit})
    if not data:
        raise HTTPException(status_code=404, detail=f"No income data for {symbol}")

    statements = []
    for item in data:
        statements.append({
            "date": item.get("date"),
            "period": item.get("period"),
            "revenue": item.get("revenue"),
            "cost_of_revenue": item.get("costOfRevenue"),
            "gross_profit": item.get("grossProfit"),
            "gross_margin": item.get("grossProfitRatio"),
            "operating_income": item.get("operatingIncome"),
            "operating_margin": item.get("operatingIncomeRatio"),
            "net_income": item.get("netIncome"),
            "net_margin": item.get("netIncomeRatio"),
            "eps": item.get("eps"),
            "eps_diluted": item.get("epsdiluted"),
            "ebitda": item.get("ebitda"),
            "weighted_avg_shares": item.get("weightedAverageShsOut"),
        })

    return {"symbol": symbol.upper(), "period": period, "statements": statements, "timestamp": _ts()}


@app.get("/balance")
async def get_balance(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("annual", description="annual or quarter"),
    limit: int = Query(4, ge=1, le=40),
):
    """Get balance sheet."""
    data = await _fmp_request(f"/balance-sheet-statement/{symbol.upper()}", {"period": period, "limit": limit})
    if not data:
        raise HTTPException(status_code=404, detail=f"No balance sheet for {symbol}")

    statements = []
    for item in data:
        statements.append({
            "date": item.get("date"),
            "period": item.get("period"),
            "total_assets": item.get("totalAssets"),
            "total_liabilities": item.get("totalLiabilities"),
            "total_equity": item.get("totalStockholdersEquity"),
            "cash_and_equivalents": item.get("cashAndCashEquivalents"),
            "total_debt": item.get("totalDebt"),
            "net_debt": item.get("netDebt"),
            "total_current_assets": item.get("totalCurrentAssets"),
            "total_current_liabilities": item.get("totalCurrentLiabilities"),
            "retained_earnings": item.get("retainedEarnings"),
            "goodwill": item.get("goodwill"),
        })

    return {"symbol": symbol.upper(), "period": period, "statements": statements, "timestamp": _ts()}


@app.get("/cashflow")
async def get_cashflow(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("annual", description="annual or quarter"),
    limit: int = Query(4, ge=1, le=40),
):
    """Get cash flow statement."""
    data = await _fmp_request(f"/cash-flow-statement/{symbol.upper()}", {"period": period, "limit": limit})
    if not data:
        raise HTTPException(status_code=404, detail=f"No cash flow data for {symbol}")

    statements = []
    for item in data:
        statements.append({
            "date": item.get("date"),
            "period": item.get("period"),
            "operating_cash_flow": item.get("operatingCashFlow"),
            "capex": item.get("capitalExpenditure"),
            "free_cash_flow": item.get("freeCashFlow"),
            "dividends_paid": item.get("dividendsPaid"),
            "stock_repurchased": item.get("commonStockRepurchased"),
            "net_investing": item.get("netCashUsedForInvestingActivites"),
            "net_financing": item.get("netCashUsedProvidedByFinancingActivities"),
            "net_change_in_cash": item.get("netChangeInCash"),
        })

    return {"symbol": symbol.upper(), "period": period, "statements": statements, "timestamp": _ts()}


@app.get("/ratios")
async def get_ratios(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("annual", description="annual or quarter"),
    limit: int = Query(4, ge=1, le=10),
):
    """Get financial ratios."""
    data = await _fmp_request(f"/ratios/{symbol.upper()}", {"period": period, "limit": limit})
    if not data:
        raise HTTPException(status_code=404, detail=f"No ratios for {symbol}")

    ratios = []
    for item in data:
        ratios.append({
            "date": item.get("date"),
            "period": item.get("period"),
            "pe_ratio": item.get("priceEarningsRatio"),
            "pb_ratio": item.get("priceToBookRatio"),
            "ps_ratio": item.get("priceToSalesRatio"),
            "peg_ratio": item.get("priceEarningsToGrowthRatio"),
            "roe": item.get("returnOnEquity"),
            "roa": item.get("returnOnAssets"),
            "roic": item.get("returnOnCapitalEmployed"),
            "debt_equity": item.get("debtEquityRatio"),
            "current_ratio": item.get("currentRatio"),
            "quick_ratio": item.get("quickRatio"),
            "gross_margin": item.get("grossProfitMargin"),
            "operating_margin": item.get("operatingProfitMargin"),
            "net_margin": item.get("netProfitMargin"),
            "dividend_yield": item.get("dividendYield"),
            "ev_ebitda": item.get("enterpriseValueMultiple"),
        })

    return {"symbol": symbol.upper(), "period": period, "ratios": ratios, "timestamp": _ts()}


@app.get("/dcf")
async def get_dcf(symbol: str = Query(..., description="Stock symbol")):
    """Get discounted cash flow valuation."""
    data = await _fmp_request(f"/discounted-cash-flow/{symbol.upper()}")
    if not data:
        raise HTTPException(status_code=404, detail=f"No DCF data for {symbol}")

    d = data[0] if isinstance(data, list) else data
    return {
        "symbol": d.get("symbol"),
        "dcf": d.get("dcf"),
        "stock_price": d.get("Stock Price"),
        "date": d.get("date"),
        "timestamp": _ts(),
    }


@app.get("/metrics")
async def get_metrics(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("annual", description="annual or quarter"),
    limit: int = Query(4, ge=1, le=10),
):
    """Get key financial metrics."""
    data = await _fmp_request(f"/key-metrics/{symbol.upper()}", {"period": period, "limit": limit})
    if not data:
        raise HTTPException(status_code=404, detail=f"No metrics for {symbol}")

    metrics = []
    for item in data:
        metrics.append({
            "date": item.get("date"),
            "period": item.get("period"),
            "market_cap": item.get("marketCap"),
            "enterprise_value": item.get("enterpriseValue"),
            "pe_ratio": item.get("peRatio"),
            "ev_ebitda": item.get("evToOperatingCashFlow"),
            "revenue_per_share": item.get("revenuePerShare"),
            "earnings_yield": item.get("earningsYield"),
            "free_cash_flow_yield": item.get("freeCashFlowYield"),
            "dividend_yield": item.get("dividendYield"),
            "book_value_per_share": item.get("bookValuePerShare"),
            "tangible_book_value_per_share": item.get("tangibleBookValuePerShare"),
            "roe": item.get("roe"),
            "roic": item.get("roic"),
        })

    return {"symbol": symbol.upper(), "period": period, "metrics": metrics, "timestamp": _ts()}


@app.get("/search")
async def search_companies(query: str = Query(..., description="Search query")):
    """Search for companies by name or ticker."""
    data = await _fmp_request("/search", {"query": query, "limit": 10})
    if not data:
        return {"query": query, "results": [], "timestamp": _ts()}

    results = []
    for item in data:
        results.append({
            "symbol": item.get("symbol"),
            "name": item.get("name"),
            "exchange": item.get("exchangeShortName"),
            "currency": item.get("currency"),
        })

    return {"query": query, "results": results, "timestamp": _ts()}
