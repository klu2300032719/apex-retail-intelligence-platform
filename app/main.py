from fastapi import FastAPI, Request
import time
import logging
import uvicorn

from app.api import router as api_router
from app.metrics import router as metrics_router
from app.funnel import router as funnel_router
from app.anomalies import router as anomalies_router
from app.health import router as health_router

logging.basicConfig(level=logging.INFO, format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
logger = logging.getLogger("IntelligenceAPI")

app = FastAPI(title="Intelligence API", version="1.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency_ms = int((time.time() - start_time) * 1000)
    
    trace_id = request.headers.get("X-Trace-Id", "trace-" + str(int(time.time()*1000)))
    
    logger.info(f'{{"trace_id": "{trace_id}", "endpoint": "{request.url.path}", "latency_ms": {latency_ms}, "status_code": {response.status_code}}}')
    return response

@app.get("/")
def root():
    return {
        "message": "Apex Retail Intelligence API Running",
        "docs_url": "/docs",
        "health_url": "/health"
    }

app.include_router(api_router)
app.include_router(metrics_router)
app.include_router(funnel_router)
app.include_router(anomalies_router)
app.include_router(health_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
