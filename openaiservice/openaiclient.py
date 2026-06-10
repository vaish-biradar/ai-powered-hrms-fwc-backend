import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Read environment variables
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# Ensure endpoint does not include the '/openai' path segment
if AZURE_OPENAI_ENDPOINT:
    AZURE_OPENAI_ENDPOINT = AZURE_OPENAI_ENDPOINT.rstrip("/")
    if AZURE_OPENAI_ENDPOINT.endswith("/openai/v1"):
        AZURE_OPENAI_ENDPOINT = AZURE_OPENAI_ENDPOINT[: -len("/openai/v1")]
    elif AZURE_OPENAI_ENDPOINT.endswith("/openai"):
        AZURE_OPENAI_ENDPOINT = AZURE_OPENAI_ENDPOINT[: -len("/openai")]

# Validate Azure OpenAI configuration
missing = [
    name for name, value in [
        ("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_API_KEY", AZURE_OPENAI_API_KEY),
        ("AZURE_OPENAI_API_VERSION", AZURE_OPENAI_API_VERSION),
        ("AZURE_OPENAI_DEPLOYMENT_NAME", AZURE_OPENAI_DEPLOYMENT_NAME),
    ]
    if not value
]
if missing:
    raise ValueError(f"Missing Azure OpenAI config values: {', '.join(missing)}")

print(f"Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")
print(f"Azure OpenAI deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)
