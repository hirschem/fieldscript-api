$port = $env:PORT
if (-not $port) { $port = 8000 }
uvicorn app.main:app --host 0.0.0.0 --port $port
