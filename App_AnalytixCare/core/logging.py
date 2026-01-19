import logging
import sys

def setup_logging():
    """
    Configure logging format and handlers.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Add FileHandler if needed
        ]
    )
    return logging.getLogger("manufacturing_app")

logger = setup_logging()
