# utils/summarizer.py
import requests
from config.settings import GEMINI_API_KEY

def summarize_with_gemini(text: str, max_length=600) -> str:
    """
    Tóm tắt đoạn văn dài sử dụng Gemini Flash API
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Tóm tắt đoạn sau thành 3–5 câu tiếng Việt súc tích, giữ nguyên thông tin quan trọng:\n\n{text[:max_length]}"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        summary = result["candidates"][0]["content"]["parts"][0]["text"]
        return summary.strip()
    except Exception as e:
        print(f"[Gemini Error] {e}")
        return "Không thể tóm tắt"
