from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import httpx
import pandas as pd

app = FastAPI()

@app.get("/")
async def show_table():
    # Get data from YOUR Hetzner server
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://91.99.137.123:3456/Calendars")
        data = resp.json()
    
    # MAGIC TABLE LINE! ✨
    df = pd.DataFrame(data)
    html_table = df.head(20).to_html(index=False, table_id="magic-table")
    
    return f"""
    <h1 style='color: navy;'>🚀 Your Hetzner Data Table!</h1>
    {html_table}
    <style>
    body {{ font-family: Arial; margin: 40px; }}
    #magic-table {{ border-collapse: collapse; width: 100%; }}
    #magic-table th {{ background: #4CAF50; color: white; padding: 12px; }}
    #magic-table td {{ border: 1px solid #ddd; padding: 12px; }}
    #magic-table tr:nth-child(even) {{ background: #f9f9f9; }}
    #magic-table tr:hover {{ background: #f5f5f5; }}
    </style>
    """
