from telethon import TelegramClient, events
from telethon.tl.types import Message
import re
import asyncio
import os
from typing import Optional, Dict, List
from datetime import datetime
from app.core.config import settings


class TelegramSignalParser:
    """Parse trading signals from Telegram messages"""
    
    @staticmethod
    def parse_signal(message: str) -> Optional[Dict]:
        """
        Extract trading signal components from message text
        Returns dict with: coin, direction, leverage, entry_zone, take_profits, stop_loss
        """
        message = message.upper()
        
        # Extract coin pair (e.g., BTC/USDT, BTCUSDT, B-BTC_USDT)
        coin_pattern = r'([A-Z]{2,10})(?:/USDT|USDT|_USDT|_PERP)'
        coin_match = re.search(coin_pattern, message)
        coin = coin_match.group(1) + "_USDT" if coin_match else None
        
        # Extract direction
        direction = None
        if "LONG" in message or "BUY" in message:
            direction = "LONG"
        elif "SHORT" in message or "SELL" in message:
            direction = "SHORT"
        
        # Extract leverage
        leverage_pattern = r'(\d+)X'
        leverage_match = re.search(leverage_pattern, message)
        leverage = leverage_match.group(1) if leverage_match else None
        
        # Extract entry zone
        entry_pattern = r'ENTRY[:\s]*([0-9.,\s-]+)'
        entry_match = re.search(entry_pattern, message)
        entry_zone = entry_match.group(1).strip() if entry_match else None
        
        # Extract take profit targets
        tp_pattern = r'TP[:\s]*([0-9.,\s-]+)|TAKE\s*PROFIT[:\s]*([0-9.,\s-]+)'
        tp_match = re.search(tp_pattern, message)
        take_profits = []
        if tp_match:
            tp_text = tp_match.group(1) or tp_match.group(2)
            take_profits = [x.strip() for x in tp_text.split(',') if x.strip()]
        
        # Extract stop loss
        sl_pattern = r'SL[:\s]*([0-9.,]+)|STOP\s*LOSS[:\s]*([0-9.,]+)'
        sl_match = re.search(sl_pattern, message)
        stop_loss = None
        if sl_match:
            stop_loss = sl_match.group(1) or sl_match.group(2)
        
        if coin and direction:
            return {
                "coin_pair": coin,
                "direction": direction,
                "leverage": leverage,
                "entry_zone": entry_zone,
                "take_profit_targets": take_profits,
                "stop_loss": stop_loss,
                "raw_message": message
            }
        
        return None


class TelegramSignalListener:
    """Listen to Telegram channels for trading signals with multi-tenant session isolation"""
    
    def __init__(self, user_id: int, api_id: str, api_hash: str, channels: List[str]):
        self.user_id = user_id
        os.makedirs("sessions", exist_ok=True)
        session_path = os.path.join("sessions", f"user_{user_id}_session")
        self.client = TelegramClient(session_path, int(api_id), api_hash)
        
        # Clean channels - convert to int if possible
        cleaned_channels = []
        for ch in channels:
            try:
                cleaned_channels.append(int(ch))
            except ValueError:
                cleaned_channels.append(ch)
        self.channels = cleaned_channels
        self.parser = TelegramSignalParser()
        self.callback = None
        self.is_running = False
    
    def set_signal_callback(self, callback):
        """Set callback function to handle parsed signals"""
        self.callback = callback
    
    async def start(self):
        """Start listening to channels"""
        if self.is_running:
            return
        
        await self.client.start()
        self.is_running = True
        
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handle_new_message(event):
            message = event.message
            if not message.text:
                return
            
            parsed_signal = self.parser.parse_signal(message.text)
            if parsed_signal:
                parsed_signal.update({
                    "channel_id": str(event.chat_id),
                    "channel_name": event.chat.title if hasattr(event.chat, 'title') else str(event.chat_id),
                    "message_id": message.id,
                    "timestamp": datetime.now().isoformat()
                })
                
                if self.callback:
                    await self.callback(parsed_signal)
    
    async def stop(self):
        """Stop listening and clean up session"""
        self.is_running = False
        await self.client.disconnect()
        # Optionally clean up session file for security
        # session_file = os.path.join("sessions", f"user_{self.user_id}_session.session")
        # if os.path.exists(session_file):
        #     os.remove(session_file)
    
    async def get_channel_history(self, channel: str, limit: int = 100):
        """Fetch recent messages from a channel"""
        messages = []
        async for message in self.client.iter_messages(channel, limit=limit):
            if message.text:
                parsed = self.parser.parse_signal(message.text)
                if parsed:
                    parsed.update({
                        "channel_id": str(channel),
                        "message_id": message.id,
                        "timestamp": message.date.isoformat() if message.date else None
                    })
                    messages.append(parsed)
        return messages

