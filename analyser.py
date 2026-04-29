import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from fastapi import HTTPException
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")
model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")
client = genai.Client(api_key=api_key)
prompt = """
You are a payment fraud detection expert specializing in Indian payment apps, 
especially Paytm and UPI-based transactions. Your job is to analyze payment 
screenshots and determine if they are real or fake/manipulated.

Analyze the screenshot carefully for the following:

1. VISUAL INTEGRITY
   - Is the image crisp or does it show signs of editing (blurriness, pixelation, 
     compression artifacts around specific elements)?
   - Are there any copy-paste artifacts or inconsistent backgrounds?

2. UI CONSISTENCY
   - Does the layout match the genuine Paytm app UI?
   - Are logos, icons, and colors consistent with the real Paytm app?
   - Are spacing and alignment consistent throughout?

3. TEXT & FONT ANALYSIS
   - Are all fonts consistent throughout the screenshot?
   - Does any text look like it was added or modified (different rendering, 
     anti-aliasing, or weight)?

4. TRANSACTION DATA VALIDITY
   - UPI Ref ID: Should be exactly 12 digits, all numeric
   - Amount: Check if the written amount (e.g. "Rupees Three Hundred Forty Only") 
     matches the numeric amount shown (e.g. ₹340)
   - Date and time: Should be realistic and plausible
   - Bank details: Should follow standard formats

5. COMMON FAKE INDICATORS
   - Amount or recipient name that looks different from surrounding text
   - Missing or incorrect "Powered by UPI" branding
   - Generic or incorrect tick/checkmark icons
   - Status bar anomalies (if visible)
   - Extra spaces in names or amounts

You must respond with ONLY a valid JSON object. No explanation outside the JSON.
No markdown. No code blocks. Just the raw JSON object.

The JSON must follow this exact structure:
{
  "verdict": "REAL" or "FAKE" or "SUSPICIOUS",
  "confidence": <integer 0-100>,
  "risk_score": <integer 0-100>,
  "summary": "<2-3 sentence summary of your overall assessment>",
  "flags": [
    {
      "severity": "HIGH" or "MEDIUM" or "LOW",
      "label": "<short name of the issue>",
      "found": true or false
    }
  ]
}

Rules:
- verdict REAL means you are confident this is a genuine screenshot
- verdict FAKE means you have found clear evidence of manipulation
- verdict SUSPICIOUS means something is off but you cannot confirm manipulation
- confidence is how confident you are in your verdict (0-100)
- risk_score is how risky it would be to trust this screenshot (0-100)
- flags must always contain ALL checks you performed, 
  with found: true if the issue was detected, found: false if the check passed
- Always include at least 6 flags covering different aspects of your analysis
"""
def analyze(image_bytes: bytes, content_type: str) -> dict:
    try:
        r=client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes,mime_type=content_type),types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        raw=r.text.strip()
        if raw.startswith("```"):
            raw=raw.split("\n",1)[1]
            raw=raw.rsplit("```",1)[0]
        result=json.loads(raw)
        return result
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="AI model returned an unexpected response format. Please try again."
        )

    except Exception as e:
        error_message = str(e)

        if "API_KEY" in error_message or "credentials" in error_message.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing Gemini API key."
            )

        if "quota" in error_message.lower() or "limit" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit reached. Please wait and try again."
            )

        if "timeout" in error_message.lower():
            raise HTTPException(
                status_code=504,
                detail="Request to AI model timed out. Please try again."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {error_message}"
        )