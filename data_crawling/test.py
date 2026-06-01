# data_crawling/jobkorea_data_collecting.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html2text
import io
import os
import base64
import json
import re
import time
from openai import OpenAI
from dotenv import load_dotenv, dotenv_values, find_dotenv
from data_crawling.constants import DEFAULT_HEADERS, BASE_URL, TARGET_EXTRACTION_FIELDS, USER_PROMPT_FOR_TEXT,USER_PROMPT_FOR_IMAGE, SYSTEM_PROMPT
from data_crawling.logger import setup_logger

# 환경 변수 로드
config = dotenv_values(dotenv_path=find_dotenv())

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=config.get("OPENAI_API_KEY"),
    base_url=config.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
)
MODEL_NAME = config.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

img_url = "https://file1.jobkorea.co.kr/Mng/2026/6/satreci1_0601_002.png"
session = requests.Session()

response = session.get(img_url, headers=DEFAULT_HEADERS)

content_type = response.headers.get('Content-Type', 'image/jpeg')
image_content = response.content
base64_image = base64.b64encode(image_content).decode('utf-8')


completion = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
                {"role": "system", "content": "너는 이미지 속 텍스트 추출 전문가이다"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text":"This is the job description image to be analyzed."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{base64_image}",
                                "detail": "high"
                            },
                        },
                    ],
                },
                {"role": "user", "content":  "이미지에 있는 내용을 빠짐없이 구조화된 형태로 작성하라. 문장을 변형해서는 안된다."},
            ],
    temperature=0.0
)

result = completion.choices[0].message.content
print(result)