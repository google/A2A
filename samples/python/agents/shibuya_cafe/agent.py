"""Crew AI based sample for A2A protocol.

Handles the agents and also presents the tools required.
"""

import base64
import logging
import os
import re
import requests

from collections.abc import AsyncIterable
from io import BytesIO
from typing import Any
from uuid import uuid4

from PIL import Image
from common.utils.in_memory_cache import InMemoryCache
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import google.generativeai as genai


load_dotenv()

logger = logging.getLogger(__name__)


class Imagedata(BaseModel):
    """Represents image data.

    Attributes:
      id: Unique identifier for the image.
      name: Name of the image.
      mime_type: MIME type of the image.
      bytes: Base64 encoded image data.
      error: Error message if there was an issue with the image.
    """

    id: str | None = None
    name: str | None = None
    mime_type: str | None = None
    bytes: str | None = None
    error: str | None = None

class ShibuyaCafeAgent:
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise RuntimeError('GOOGLE_API_KEYが設定されていません')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # 利用可能なモデル名に合わせてください

    def invoke(self, query: str, session_id: str) -> str:
        prompt = f"""
        あなたは渋谷のカフェ案内エージェントです。
        ユーザーからのリクエストに基づき、渋谷に実在するカフェのみをリストアップし、最適な店舗を日本語で丁寧に提案してください。
        必ず実在する店舗のみを案内してください。架空の店舗や存在しない情報は絶対に案内しないでください。

        ユーザーリクエスト: {query}
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            print(f"Gemini response: {response}")  # デバッグ用
            return response.text if response and response.text else "申し訳ありません。回答を生成できませんでした。"
        except Exception as e:
            print(f"Exception in invoke: {e}")
            return f"エラーが発生しました: {e}"
