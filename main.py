import uvicorn
import argparse
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False, user_agent: str = None):
    """Run the FastAPI application."""
    logger.info(f"Starting API server on {host}:{port}")
    
    # Set environment variable for User-Agent if provided
    if user_agent:
        os.environ["SEC_API_USER_AGENT"] = user_agent
        
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload
    )


def run_frontend(port: int = 8501):
    """Run the Streamlit frontend."""
    logger.info(f"Starting Streamlit frontend on port {port}")
    os.system(f"streamlit run frontend/app.py --server.port {port}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEC Filings Dashboard")
    parser.add_argument(
        "--component",
        type=str,
        choices=["api", "frontend", "both"],
        default="both",
        help="Component to run (api, frontend, or both)"
    )
    parser.add_argument(
        "--api-host",
        type=str,
        default="0.0.0.0",
        help="Host for the API server"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Port for the API server"
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="Port for the Streamlit frontend"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        help="User-Agent for SEC API requests (should include your email)"
    )
    
    args = parser.parse_args()
    
    if args.component in ["api", "both"]:
        # Run in a separate process if running both components
        if args.component == "both":
            import multiprocessing
            api_process = multiprocessing.Process(
                target=run_api,
                args=(args.api_host, args.api_port, args.reload, args.user_agent)
            )
            api_process.start()
        else:
            run_api(args.api_host, args.api_port, args.reload, args.user_agent)
    
    if args.component in ["frontend", "both"]:
        run_frontend(args.frontend_port) 