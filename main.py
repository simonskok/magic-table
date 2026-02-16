from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Literal
import httpx
import asyncio
import time

app = FastAPI()

# --------------------------------------------------
# GLOBAL HTTP CLIENT (connection pooling)
# --------------------------------------------------
client: httpx.AsyncClient | None = None

@app.on_event("startup")
async def startup():
    global client
    client = httpx.AsyncClient(timeout=20.0)

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()


# --------------------------------------------------
# SIMPLE IN-MEMORY CACHE
# --------------------------------------------------
CACHE_TTL = 30  # seconds
cache = {}
lock = asyncio.Lock()

async def get_cache(interval: str):
    async with lock:
        entry = cache.get(interval)
        if entry and (time.time() - entry["time"] < CACHE_TTL):
            return entry["data"]
        return None

async def set_cache(interval: str, data):
    async with lock:
        cache[interval] = {
            "data": data,
            "time": time.time()
        }


# --------------------------------------------------
# HTML SERVED ONCE
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>🚀 OHLCV Statistics</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css">

    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>

    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh; padding: 20px; }
        .container { background: white; border-radius: 20px;
                     box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    </style>
</head>
<body>

<div class="container my-5 p-5 mx-auto" style="max-width: 1400px;">
    <h1 class="text-center mb-4">🚀 OHLCV Statistics (Futures)</h1>

    <div class="mb-4">
        <label class="form-label">Select Interval</label>
        <select id="intervalSelect" class="form-select">
            <option value="Last">Last</option>
            <option value="1M">1M</option>
            <option value="5M">5M</option>
            <option value="15M">15M</option>
            <option value="30M">30M</option>
            <option value="60M">60M</option>
        </select>
    </div>

    <div class="table-responsive">
        <table id="dataTable" class="table table-striped table-hover" style="width:100%"></table>
    </div>
</div>

<script>
let table;

async function loadData(interval) {
    const res = await fetch(`/data?interval=${interval}`);
    const data = await res.json();

    if (!data || data.length === 0) return;

    // Collect ALL unique keys across rows
    const allKeys = [...new Set(
        data.flatMap(row => Object.keys(row))
    )];

    const columns = allKeys.map(key => ({
        title: key,
        data: key,
        defaultContent: ""   // prevents unknown parameter errors
    }));

    if (table) {
        table.destroy();
        $('#dataTable').empty();
    }

    table = $('#dataTable').DataTable({
        data: data,
        columns: columns,
        pageLength: 25,
        responsive: true
    });
}

// Initial load
loadData("Last");

// Dropdown change
document.getElementById("intervalSelect")
    .addEventListener("change", function() {
        loadData(this.value);
    });
</script>

</body>
</html>
"""


# --------------------------------------------------
# DATA ENDPOINT (FAST + CACHED)
# --------------------------------------------------
@app.get("/data")
async def get_data(
    interval: Literal["Last","1M","5M","15M","30M","60M"] = Query("Last")
):
    # 1️⃣ Check cache
    cached = await get_cache(interval)
    if cached:
        return JSONResponse(cached)

    # 2️⃣ Build upstream URL
    url = (
        "http://91.99.137.123:3456/"
        f"OHLCV_Statistics?Asset_Class=Futures&Interval={interval}"
    )

    # 3️⃣ Fetch from upstream (connection pooled)
    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()

    # 4️⃣ Limit rows server-side (avoid pandas overhead)
    if isinstance(data, list):
    data = data[:50]

    # 🔥 Normalize all rows to same keys
    all_keys = set()
    for row in data:
        all_keys.update(row.keys())

    for row in data:
        for key in all_keys:
            row.setdefault(key, None)

    # 5️⃣ Store in cache
    await set_cache(interval, data)

    return JSONResponse(data)
