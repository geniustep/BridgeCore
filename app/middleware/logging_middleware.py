"""
Logging Middleware for request/response tracking
"""
from fastapi import Request
import time
import uuid
from loguru import logger


async def logging_middleware(request: Request, call_next):
    """
    Log all requests and responses with detailed information

    Features:
    - Generate unique request ID
    - Log client information (IP, user agent)
    - Track request duration
    - Add custom headers to response
    """
    # Generate unique Request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Request information
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get("user-agent", "unknown")

    # Request start
    start_time = time.time()

    logger.info(
        f"Request started | ID: {request_id} | {method} {url} | IP: {client_ip}"
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = (time.time() - start_time) * 1000  # milliseconds

        # Log response
        logger.info(
            f"Request completed | ID: {request_id} | Status: {response.status_code} | Duration: {duration:.2f}ms"
        )

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed | ID: {request_id} | Error: {str(e)} | Duration: {duration:.2f}ms"
        )
        raise
