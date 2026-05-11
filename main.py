import os
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
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


HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FMP - Financial Modeling Prep</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #0a0a0a;
  color: #e0e0e0;
  padding: 40px 20px;
  line-height: 1.6;
}
.container { max-width: 640px; margin: 0 auto; opacity: 0; animation: fadeIn 0.6s ease forwards; }
@keyframes fadeIn { to { opacity: 1; } }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.title { font-family: 'Courier New', monospace; font-style: italic; font-size: 28px; color: #E67E22; font-weight: bold; }
.health {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #888;
  background: rgba(255,255,255,.03);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.07);
}
.dot { width: 6px; height: 6px; border-radius: 50%; background: #4ade80; }
.subtitle { color: #888; margin-bottom: 32px; font-size: 15px; }
.card {
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(230,126,34,.15);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}
.hero { text-align: center; padding: 32px 24px; }
.hero-symbol { font-size: 48px; font-weight: bold; color: #E67E22; font-family: 'Courier New', monospace; }
.hero-name { font-size: 20px; margin: 8px 0; color: #fff; }
.hero-sector { font-size: 14px; color: #888; margin-bottom: 20px; }
.hero-price { font-size: 36px; font-weight: bold; color: #fff; font-family: 'Courier New', monospace; margin: 16px 0 8px; }
.hero-cap { font-size: 14px; color: #888; }
.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.metric { text-align: center; padding: 16px; background: rgba(255,255,255,.02); border-radius: 12px; border: 1px solid rgba(255,255,255,.05); }
.metric-label { font-size: 11px; color: #E67E22; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; font-weight: 600; }
.metric-value { font-size: 24px; font-weight: bold; color: #fff; font-family: 'Courier New', monospace; }
.dcf-section { padding: 20px 0; }
.dcf-title { font-size: 13px; color: #E67E22; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 16px; font-weight: 600; }
.dcf-comparison { display: flex; justify-content: space-around; align-items: center; text-align: center; }
.dcf-item { flex: 1; }
.dcf-label { font-size: 12px; color: #888; margin-bottom: 6px; }
.dcf-value { font-size: 28px; font-weight: bold; font-family: 'Courier New', monospace; color: #fff; }
.dcf-verdict { flex: 0.5; font-size: 14px; font-weight: bold; padding: 8px 16px; border-radius: 8px; }
.undervalued { color: #4ade80; background: rgba(74,222,128,.1); border: 1px solid rgba(74,222,128,.3); }
.overvalued { color: #f87171; background: rgba(248,113,113,.1); border: 1px solid rgba(248,113,113,.3); }
.input-section { margin-top: 32px; }
.input-row { display: flex; gap: 8px; margin-bottom: 12px; }
.input-field {
  flex: 1;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  padding: 12px 16px;
  color: #fff;
  font-size: 15px;
  font-family: 'Courier New', monospace;
}
.input-field:focus { outline: none; border-color: #E67E22; }
.btn {
  background: #E67E22;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn:hover { background: #d35400; transform: translateY(-1px); }
.suggestions { font-size: 13px; color: #888; }
.suggestions span { color: #E67E22; cursor: pointer; margin: 0 4px; transition: color 0.2s; }
.suggestions span:hover { color: #d35400; text-decoration: underline; }
.result {
  margin-top: 20px;
  padding: 16px;
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(230,126,34,.15);
  border-radius: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
  display: none;
}
.loading { color: #E67E22; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title">FMP</div>
    <div class="health"><span class="dot"></span><span id="health-status">checking...</span></div>
  </div>
  <div class="subtitle">Company fundamentals, financial statements, and DCF analysis</div>

  <div class="card hero" id="hero-card">
    <div class="hero-symbol" id="hero-symbol">--</div>
    <div class="hero-name" id="hero-name">Loading...</div>
    <div class="hero-sector" id="hero-sector">--</div>
    <div class="hero-price" id="hero-price">$--</div>
    <div class="hero-cap" id="hero-cap">Market Cap: --</div>
  </div>

  <div class="card">
    <div class="metrics-grid" id="metrics-grid">
      <div class="metric"><div class="metric-label">P/E Ratio</div><div class="metric-value" id="pe">--</div></div>
      <div class="metric"><div class="metric-label">EPS</div><div class="metric-value" id="eps">--</div></div>
      <div class="metric"><div class="metric-label">Revenue TTM</div><div class="metric-value" id="revenue">--</div></div>
      <div class="metric"><div class="metric-label">Beta</div><div class="metric-value" id="beta">--</div></div>
      <div class="metric"><div class="metric-label">Div Yield</div><div class="metric-value" id="div-yield">--</div></div>
      <div class="metric"><div class="metric-label">ROE</div><div class="metric-value" id="roe">--</div></div>
    </div>
  </div>

  <div class="card">
    <div class="dcf-section">
      <div class="dcf-title">DCF VALUATION</div>
      <div class="dcf-comparison">
        <div class="dcf-item">
          <div class="dcf-label">Intrinsic Value</div>
          <div class="dcf-value" id="dcf-intrinsic">$--</div>
        </div>
        <div class="dcf-verdict" id="dcf-verdict">--</div>
        <div class="dcf-item">
          <div class="dcf-label">Current Price</div>
          <div class="dcf-value" id="dcf-current">$--</div>
        </div>
      </div>
    </div>
  </div>

  <div class="input-section">
    <form id="lookup-form" class="input-row">
      <input type="text" class="input-field" id="symbol-input" placeholder="AAPL" maxlength="10">
      <button type="submit" class="btn">\\u2192 profile</button>
    </form>
    <div class="suggestions">
      Try:
      <span onclick="trySymbol('TSLA')">TSLA</span> \\u00B7
      <span onclick="trySymbol('MSFT')">MSFT</span> \\u00B7
      <span onclick="trySymbol('GOOGL')">GOOGL</span> \\u00B7
      <span onclick="trySymbol('NVDA')">NVDA</span> \\u00B7
      <span onclick="trySymbol('META')">META</span>
    </div>
    <div class="result" id="result"></div>
  </div>
</div>

<script>
const fmt = (num) => {
  if (!num || isNaN(num)) return '--';
  const abs = Math.abs(num);
  if (abs >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T';
  if (abs >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B';
  if (abs >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M';
  return '$' + num.toFixed(2);
};

const fmtNum = (num, decimals = 2) => {
  if (!num || isNaN(num)) return '--';
  return num.toFixed(decimals);
};

const fmtPct = (num) => {
  if (!num || isNaN(num)) return '--';
  return (num * 100).toFixed(2) + '%';
};

async function fetchData() {
  const symbol = 'AAPL';

  // Health check
  try {
    const startHealth = Date.now();
    const health = await fetch('/health').then(r => r.json());
    const latency = Date.now() - startHealth;
    document.getElementById('health-status').textContent = 'online \\u00B7 ' + latency + 'ms';
  } catch (e) {
    document.getElementById('health-status').textContent = 'offline';
  }

  // Profile
  try {
    const profile = await fetch('/profile?symbol=' + symbol).then(r => r.json());
    document.getElementById('hero-symbol').textContent = profile.symbol || '--';
    document.getElementById('hero-name').textContent = profile.name || '--';
    document.getElementById('hero-sector').textContent = (profile.sector || '') + (profile.industry ? ' \\u00B7 ' + profile.industry : '');
    document.getElementById('hero-price').textContent = profile.price ? fmt(profile.price) : '$--';
    document.getElementById('hero-cap').textContent = 'Market Cap: ' + (profile.market_cap ? fmt(profile.market_cap) : '--');
    document.getElementById('beta').textContent = profile.beta ? fmtNum(profile.beta, 2) : '--';
  } catch (e) {
    console.error('Profile error:', e);
  }

  // Ratios
  try {
    const ratiosData = await fetch('/ratios?symbol=' + symbol + '&limit=1').then(r => r.json());
    if (ratiosData.ratios && ratiosData.ratios[0]) {
      const r = ratiosData.ratios[0];
      document.getElementById('pe').textContent = r.pe_ratio ? fmtNum(r.pe_ratio, 1) : '--';
      document.getElementById('div-yield').textContent = r.dividend_yield ? fmtPct(r.dividend_yield) : '--';
      document.getElementById('roe').textContent = r.roe ? fmtPct(r.roe) : '--';
    }
  } catch (e) {
    console.error('Ratios error:', e);
  }

  // Metrics
  try {
    const metricsData = await fetch('/metrics?symbol=' + symbol + '&limit=1').then(r => r.json());
    if (metricsData.metrics && metricsData.metrics[0]) {
      const m = metricsData.metrics[0];
      document.getElementById('revenue').textContent = m.revenue_per_share ? fmt(m.revenue_per_share * 15e9) : '--';
    }
  } catch (e) {
    console.error('Metrics error:', e);
  }

  // Income for EPS
  try {
    const incomeData = await fetch('/income?symbol=' + symbol + '&limit=1').then(r => r.json());
    if (incomeData.statements && incomeData.statements[0]) {
      const s = incomeData.statements[0];
      document.getElementById('eps').textContent = s.eps ? '$' + fmtNum(s.eps, 2) : '--';
      if (s.revenue) {
        document.getElementById('revenue').textContent = fmt(s.revenue);
      }
    }
  } catch (e) {
    console.error('Income error:', e);
  }

  // DCF
  try {
    const dcf = await fetch('/dcf?symbol=' + symbol).then(r => r.json());
    const intrinsic = dcf.dcf;
    const current = dcf.stock_price;

    document.getElementById('dcf-intrinsic').textContent = intrinsic ? fmt(intrinsic) : '$--';
    document.getElementById('dcf-current').textContent = current ? fmt(current) : '$--';

    if (intrinsic && current) {
      const verdict = document.getElementById('dcf-verdict');
      if (intrinsic > current) {
        verdict.textContent = '\\u2191 Buy';
        verdict.className = 'dcf-verdict undervalued';
      } else {
        verdict.textContent = '\\u2193 Sell';
        verdict.className = 'dcf-verdict overvalued';
      }
    }
  } catch (e) {
    console.error('DCF error:', e);
  }
}

async function lookupSymbol(symbol) {
  const result = document.getElementById('result');
  result.style.display = 'block';
  result.textContent = 'Loading profile for ' + symbol + '...';
  result.className = 'result loading';

  try {
    const data = await fetch('/profile?symbol=' + symbol.toUpperCase()).then(r => r.json());
    result.className = 'result';
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = 'Error: ' + e.message;
  }
}

function trySymbol(symbol) {
  document.getElementById('symbol-input').value = symbol;
  lookupSymbol(symbol);
}

document.getElementById('lookup-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const symbol = document.getElementById('symbol-input').value.trim();
  if (symbol) lookupSymbol(symbol);
});

// Load data on page load
fetchData();
</script>
</body>
</html>
"""

# ── Endpoints ────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def root():
    return HOME_HTML


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
