# type: ignore
import logging
import os

import google.generativeai as genai

from a2a_mcp.common.types import ServerConfig

logger = logging.getLogger(__name__)


def init_api_key():
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY is not set")
        raise ValueError("GOOGLE_API_KEY is not set")

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def config_logger(logger):
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_mcp_server_config() -> ServerConfig:
    return ServerConfig(
        host="localhost", port=10100, transport="sse", url="http://localhost:10100/sse"
    )
