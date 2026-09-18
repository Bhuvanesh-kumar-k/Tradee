import httpx
import json
from typing import Optional, Dict
from app.core.config import settings


class AIService:
    """AI service for trade analysis and signal validation with structured JSON output"""
    
    # Default models
    DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
    
    @staticmethod
    async def analyze_signal(
        provider: str,
        api_key: str,
        signal: Dict,
        market_context: Dict
    ) -> Dict:
        """
        Analyze a trading signal using AI with strict JSON schema enforcement
        Returns: {verdict: "APPROVED"|"REJECTED", confidence: float, reason: str}
        """
        
        prompt = f"""
        You are a professional cryptocurrency trading analyst. Evaluate the following trading signal:
        
        SIGNAL DETAILS:
        - Coin Pair: {signal.get('coin_pair')}
        - Direction: {signal.get('direction')}
        - Leverage: {signal.get('leverage')}
        - Entry Zone: {signal.get('entry_zone')}
        - Take Profit: {signal.get('take_profit_targets')}
        - Stop Loss: {signal.get('stop_loss')}
        
        CURRENT MARKET CONTEXT:
        - BTC Trend: {market_context.get('btc_trend')}
        - Coin 1D Trend: {market_context.get('coin_1d_trend')}
        - Coin 1H Trend: {market_context.get('coin_1h_trend')}
        - RSI: {market_context.get('rsi')}
        - MACD Histogram: {market_context.get('macd_hist')}
        - ADX: {market_context.get('adx')}
        - EMA50: {market_context.get('ema50')}
        - EMA200: {market_context.get('ema200')}
        
        TASK:
        1. Analyze if the signal aligns with current market structure
        2. Check if the direction matches the multi-timeframe trend
        3. Evaluate risk-reward based on entry, TP, and SL
        4. Consider overall market conditions
        
        Return ONLY valid JSON with this exact schema:
        {{
            "verdict": "APPROVE" or "REJECT",
            "confidence": 85,
            "reason": "Detailed institutional reason based on EMA/MACD/RSI confluence..."
        }}
        """
        
        if provider == "OpenAI":
            return await AIService._call_openai(api_key, prompt)
        elif provider == "Gemini":
            return await AIService._call_gemini(api_key, prompt)
        elif provider == "Copilot":
            return await AIService._call_copilot(api_key, prompt)
        else:
            return {
                "verdict": "REJECT",
                "confidence": 0,
                "reason": "AI provider not configured"
            }
    
    @staticmethod
    async def _call_openai(api_key: str, prompt: str) -> Dict:
        """Call OpenAI API with structured JSON output"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": AIService.DEFAULT_OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return AIService._parse_json_response(content)
                else:
                    return {
                        "verdict": "REJECT",
                        "confidence": 0,
                        "reason": f"OpenAI API error: {response.status_code}"
                    }
        except Exception as e:
            return {
                "verdict": "REJECT",
                "confidence": 0,
                "reason": f"OpenAI call failed: {str(e)}"
            }
    
    @staticmethod
    async def _call_gemini(api_key: str, prompt: str) -> Dict:
        """Call Google Gemini API with structured JSON output"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{AIService.DEFAULT_GEMINI_MODEL}:generateContent?key={api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 500,
                            "response_mime_type": "application/json"
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return AIService._parse_json_response(content)
                else:
                    return {
                        "verdict": "REJECT",
                        "confidence": 0,
                        "reason": f"Gemini API error: {response.status_code}"
                    }
        except Exception as e:
            return {
                "verdict": "REJECT",
                "confidence": 0,
                "reason": f"Gemini call failed: {str(e)}"
            }
    
    @staticmethod
    async def _call_copilot(api_key: str, prompt: str) -> Dict:
        """Call Microsoft Copilot API (placeholder - needs specific endpoint)"""
        return {
            "verdict": "REJECT",
            "confidence": 0,
            "reason": "Copilot integration not yet implemented"
        }
    
    @staticmethod
    def _parse_json_response(content: str) -> Dict:
        """Parse JSON response from AI"""
        try:
            parsed = json.loads(content)
            
            # Normalize verdict to match expected format
            verdict = parsed.get("verdict", "REJECT").upper()
            if verdict == "APPROVED":
                verdict = "APPROVE"
            elif verdict not in ["APPROVE", "REJECT"]:
                verdict = "REJECT"
            
            return {
                "verdict": verdict,
                "confidence": int(parsed.get("confidence", 50)),
                "reason": parsed.get("reason", "No reasoning provided")
            }
        except json.JSONDecodeError:
            # Fallback to regex parsing if JSON fails
            import re
            verdict = "REJECT"
            reason = content
            confidence = 50
            
            verdict_match = re.search(r'["\']?verdict["\']?\s*:\s*["\']?(APPROVE|REJECT|APPROVED|REJECTED)["\']?', content, re.IGNORECASE)
            if verdict_match:
                verdict = verdict_match.group(1).upper()
                if verdict == "APPROVED":
                    verdict = "APPROVE"
                elif verdict == "REJECTED":
                    verdict = "REJECT"
            
            reason_match = re.search(r'["\']?reason["\']?\s*:\s*["\']?([^"\']+)["\']?', content, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
            
            confidence_match = re.search(r'["\']?confidence["\']?\s*:\s*(\d+)', content)
            if confidence_match:
                confidence = int(confidence_match.group(1))
            
            return {
                "verdict": verdict,
                "confidence": confidence,
                "reason": reason
            }
