import httpx
import hmac
import hashlib
import time
import json
from typing import Dict, Optional, List
from app.core.config import settings
from app.core.encryption import decrypt_data


class CoinDCXExecutor:
    """Execute trades on CoinDCX Futures"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = settings.COINDCX_BASE_URL
    
    def _generate_signature(self, payload: Dict) -> str:
        """Generate HMAC SHA256 signature for CoinDCX API"""
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            self.api_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make authenticated request to CoinDCX API"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "X-AUTH-APIKEY": self.api_key
            }
            
            if payload:
                timestamp = int(time.time() * 1000)
                payload["timestamp"] = timestamp
                signature = self._generate_signature(payload)
                headers["X-AUTH-SIGNATURE"] = signature
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=payload)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, json=payload)
                else:
                    return None
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"CoinDCX API Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"CoinDCX Request Failed: {e}")
            return None
    
    async def get_futures_balance(self) -> Optional[Dict]:
        """Get futures account balance"""
        payload = {}
        result = await self._make_request("GET", "/exchange/v1/derivatives/futures/balance", payload)
        return result
    
    async def get_open_positions(self) -> Optional[List[Dict]]:
        """Get all open futures positions"""
        payload = {}
        result = await self._make_request("GET", "/exchange/v1/derivatives/futures/positions", payload)
        if result and isinstance(result, list):
            return result
        return None
    
    async def place_market_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        leverage: Optional[int] = None
    ) -> Optional[Dict]:
        """Place a market order on CoinDCX Futures"""
        payload = {
            "symbol": symbol,
            "side": side,
            "order_type": "market_order",
            "quantity": quantity,
            "leverage": leverage
        }
        
        result = await self._make_request("POST", "/exchange/v1/derivatives/futures/orders/create", payload)
        return result
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        leverage: Optional[int] = None
    ) -> Optional[Dict]:
        """Place a limit order with TP/SL"""
        payload = {
            "symbol": symbol,
            "side": side,
            "order_type": "limit_order",
            "price_per_unit": price,
            "quantity": quantity,
            "leverage": leverage
        }
        
        result = await self._make_request("POST", "/exchange/v1/derivatives/futures/orders/create", payload)
        return result
    
    async def place_order_with_tp_sl(
        self,
        symbol: str,
        side: str,
        quantity: float,
        leverage: int,
        take_profit: float,
        stop_loss: float
    ) -> Optional[Dict]:
        """Place order with take profit and stop loss"""
        # CoinDCX may require separate orders for TP/SL
        # This is a simplified implementation
        payload = {
            "symbol": symbol,
            "side": side,
            "order_type": "market_order",
            "quantity": quantity,
            "leverage": leverage
        }
        
        result = await self._make_request("POST", "/exchange/v1/derivatives/futures/orders/create", payload)
        
        if result and result.get("order"):
            # After order fills, place TP and SL orders
            order_id = result["order"]["id"]
            # Implementation would place TP/SL orders here
            pass
        
        return result
    
    async def cancel_order(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Cancel an order"""
        payload = {
            "id": order_id,
            "symbol": symbol
        }
        result = await self._make_request("DELETE", "/exchange/v1/derivatives/futures/orders/cancel", payload)
        return result
    
    async def close_position(self, symbol: str, quantity: float) -> Optional[Dict]:
        """Close a position with market order"""
        # Determine side based on current position
        positions = await self.get_open_positions()
        if positions:
            for pos in positions:
                if pos.get("symbol") == symbol:
                    current_side = pos.get("side")
                    close_side = "sell" if current_side == "buy" else "buy"
                    return await self.place_market_order(symbol, close_side, quantity)
        
        return None


async def get_user_executor(user) -> Optional[CoinDCXExecutor]:
    """Get CoinDCX executor for a user with decrypted credentials"""
    if not user.encrypted_coindcx_api_key or not user.encrypted_coindcx_api_secret:
        return None
    
    try:
        api_key = decrypt_data(user.encrypted_coindcx_api_key)
        api_secret = decrypt_data(user.encrypted_coindcx_api_secret)
        return CoinDCXExecutor(api_key, api_secret)
    except Exception as e:
        print(f"Failed to decrypt CoinDCX credentials: {e}")
        return None
