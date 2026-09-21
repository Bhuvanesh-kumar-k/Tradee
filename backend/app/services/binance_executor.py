import ccxt.async_support as ccxt
from typing import Optional, Dict, Any

class BinanceExecutor:
    """Async Binance USDT-M Futures execution engine powered by CCXT"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.client = ccxt.binanceusdm({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        if testnet:
            self.client.set_sandbox_mode(True)

    async def close(self):
        await self.client.close()

    async def get_futures_balance(self) -> float:
        try:
            balance = await self.client.fetch_balance()
            usdt_bal = balance.get('USDT', {}).get('free', 0.0)
            return float(usdt_bal or 0.0)
        except Exception as e:
            print(f"Binance balance error: {e}")
            return 0.0
        finally:
            await self.close()

    async def set_leverage(self, symbol: str, leverage: int = 5):
        try:
            clean_symbol = symbol.replace("B-", "").replace("_", "/")
            await self.client.set_leverage(leverage, clean_symbol)
        except Exception as e:
            print(f"Binance set leverage error: {e}")
        finally:
            await self.close()

    async def place_order(self, symbol: str, side: str, amount: float, leverage: int = 5) -> Optional[Dict[str, Any]]:
        try:
            clean_symbol = symbol.replace("B-", "").replace("_", "/")
            await self.client.set_leverage(leverage, clean_symbol)
            order = await self.client.create_market_order(
                symbol=clean_symbol,
                side=side.lower(),
                amount=amount
            )
            return order
        except Exception as e:
            print(f"Binance order execution error: {e}")
            return None
        finally:
            await self.close()
