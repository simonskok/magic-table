from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import httpx
import pandas as pd

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def show_table():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get("http://91.99.137.123:3456/Calendars")
            data = resp.json()
        
        df = pd.DataFrame(data)
        table_data = df.head(50).to_dict('records')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Interactive Hetzner Table</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        h1 { background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; border-radius: 15px 15px 0 0; }
    </style>
</head>
<body>
    <div class="container my-5 p-5 mx-auto" style="max-width: 1400px;">
        <h1 class="text-center mb-4">🚀 Hetzner Calendars Data</h1>
        <div class="table-responsive">
            <table id="dataTable" class="table table-striped table-hover" style="width:100%">
                <thead><tr><th>Loading...</th></tr></thead>
            </table>
        </div>
        <p class="text-center text-muted mt-4">Live data from 91.99.137.123:3456 | {len(table_data)} rows</p>
    </div>

    <script>
        $(document).ready(function() {{
            $('#dataTable').DataTable({{
                data: {table_data},
                pageLength: 25,
                responsive: true,
                dom: '<"top"lf>rt<"bottom"ip><"clear">',
                language: {{ search: "🔍 Search table..." }}
            }});
        }});
    </script>
</body>
</html>
        """
    except Exception as e:
        return f"<h1 style='color:red;text-align:center;padding:50px;'>❌ Can't reach Hetzner: {str(e)}</h1>"
