import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pytz import timezone

IST = timezone("Asia/Kolkata")

# High-impact economic events that trigger circuit breaker
HIGH_IMPACT_EVENTS = [
    "CPI", "Core CPI", "FOMC", "Federal Reserve", "Interest Rate Decision",
    "NFP", "Non-Farm Payrolls", "Unemployment Rate", "GDP", "PCE",
    "Core PCE", "Retail Sales", "ISM Manufacturing", "ISM Services",
    "Consumer Confidence", "CB Consumer Confidence"
]


class EconomicEvent:
    def __init__(self, name: str, time: datetime, impact: str = "High"):
        self.name = name
        self.time = time
        self.impact = impact
    
    def is_high_impact(self) -> bool:
        return self.impact == "High" or any(
            event.lower() in self.name.lower() 
            for event in HIGH_IMPACT_EVENTS
        )


class NewsCircuitBreaker:
    def __init__(self):
        self.events: List[EconomicEvent] = []
        self.freeze_window_minutes = 30  # Freeze before and after events
    
    async def fetch_economic_calendar(self, days_ahead: int = 7) -> List[EconomicEvent]:
        """Fetch economic calendar from Trading Economics or similar API"""
        try:
            # Using Trading Economics API (free tier available)
            # Alternative: ForexFactory, Investing.com, etc.
            async with httpx.AsyncClient(timeout=10.0) as client:
                today = datetime.now(IST).strftime("%Y-%m-%d")
                end_date = (datetime.now(IST) + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                
                # Trading Economics API endpoint
                url = f"https://api.tradingeconomics.com/calendar?country=United States&c={today}&f={end_date}"
                
                # Note: This requires an API key. For production, integrate with proper service.
                # For now, we'll return empty and implement manual event addition
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    events = []
                    for item in data:
                        if item.get("impact", "Low") in ["High", "Medium"]:
                            event_time = datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S")
                            event_time = IST.localize(event_time)
                            events.append(EconomicEvent(
                                name=item["Event"],
                                time=event_time,
                                impact=item["impact"]
                            ))
                    self.events = events
                    return events
        except Exception as e:
            print(f"Failed to fetch economic calendar: {e}")
        
        return []
    
    def add_manual_event(self, name: str, time: datetime, impact: str = "High"):
        """Manually add a high-impact event"""
        event = EconomicEvent(name, time, impact)
        self.events.append(event)
    
    def is_trading_frozen(self) -> tuple[bool, Optional[EconomicEvent]]:
        """Check if trading should be frozen due to upcoming high-impact news"""
        now = datetime.now(IST)
        
        for event in self.events:
            if not event.is_high_impact():
                continue
            
            time_diff = abs((event.time - now).total_seconds() / 60)
            
            if time_diff <= self.freeze_window_minutes:
                return True, event
        
        return False, None
    
    def get_frozen_status_message(self) -> Optional[str]:
        """Get status message if trading is frozen"""
        is_frozen, event = self.is_trading_frozen()
        
        if is_frozen and event:
            event_time_ist = event.time.strftime("%I:%M %p")
            return f"• SCAN PAUSED: High-impact {event.name} at {event_time_ist} IST. Waiting for volatility to settle."
        
        return None
    
    def get_upcoming_events(self, hours: int = 24) -> List[Dict]:
        """Get upcoming high-impact events within specified hours"""
        now = datetime.now(IST)
        upcoming = []
        
        for event in self.events:
            if not event.is_high_impact():
                continue
            
            time_diff = (event.time - now).total_seconds() / 3600
            if 0 < time_diff <= hours:
                upcoming.append({
                    "name": event.name,
                    "time": event.time.isoformat(),
                    "time_ist": event.time.strftime("%Y-%m-%d %I:%M %p"),
                    "impact": event.impact,
                    "hours_until": round(time_diff, 1)
                })
        
        return sorted(upcoming, key=lambda x: x["hours_until"])


# Global circuit breaker instance
circuit_breaker = NewsCircuitBreaker()
