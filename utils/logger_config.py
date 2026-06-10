import logging

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define log message format
    handlers=[logging.StreamHandler()]  # Output logs to the console (stdout)
)

# Create a logger instance for use in other modules
logger = logging.getLogger(__name__)
