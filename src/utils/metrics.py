from prometheus_client import Counter ,Histogram ,generate_latest ,CONTENT_TYPE_LATEST
from fastapi import FastAPI ,Request ,Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

# define some constants before constructing Minddleware
REQUEST_COUNT =Counter('http_requests_total','Total HTTP Requests',['methods','status','endpoint'])
REQUEST_LATENCY =Histogram('http_request_duration_seconds','HTTP Request Latency',['method','endpoint'])


class PrometheusMeddileware(BaseHTTPMiddleware):

    async def dispatch(self, request:Request, call_next):
        
        start_time =time.time()
        response = await call_next(request)
        
        # record metrics after request is processed
        duration =time.time() - start_time 
        endpoint =request.url.path

        REQUEST_COUNT.labels(method =request.method ,endpoint =endpoint ,status =request.status_code).inc()
        REQUEST_LATENCY.labels(method =request.method ,endpoint =endpoint ).observe(duration)

        return response 
    

# setup fuction to pass meddileware to fastapi 

def setup_metrics(app:FastAPI):
    """setup prometheus Middleware and endpoint"""
    # Add Promethues Middleware 
    app.add_middleware(PrometheusMeddileware)


    @app.get('/shrouk_1234_metrics',include_in_schema=False)
    def metrics():
        return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
