import os
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class TradingConfig:
    # Bybit API Configuration
    BYBIT_TESTNET: bool = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    
    # Trading Parameters
    SYMBOL: str = "BTCUSDT"
    TIMEFRAME: str = "1"  # 1 minute
    LEVERAGE: int = 5
    MAX_POSITION_SIZE: float = 0.001  # BTC
    MAX_OPEN_TRADES: int = 2
    STOP_LOSS_PCT: float = 0.3  # 0.3%
    TAKE_PROFIT_PCT: float = 0.2  # 0.2%
    MAX_DAILY_LOSS_PCT: float = 1.0  # 1%
    
    # ML Configuration
    ML_MODEL_PATH: str = "models/scalping_model.joblib"
    PREDICTION_CONFIDENCE: float = 0.70
    ML_TRAIN_INTERVAL_HOURS: int = 24
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Risk Management
    ENABLE_AUTO_LEVERAGE_ADJUSTMENT: bool = True
    VOLATILITY_THRESHOLD: float = 1.5
    MAX_CONSECUTIVE_LOSSES: int = 3
    
    # Performance
    HEARTBEAT_INTERVAL: int = 30  # seconds
    ORDER_TIMEOUT: int = 10  # seconds
    DATA_FETCH_INTERVAL: float = 0.5  # seconds
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/trades.db"
    
    # Render Specific
    RENDER: bool = os.getenv('RENDER', 'false').lower() == 'true'
    HEALTH_CHECK_PORT: int = 8080
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        config = cls()
        
        # Bybit
        config.BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
        config.BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
        
        # Telegram
        config.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        config.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Trading parameters
        config.SYMBOL = os.getenv('TRADING_SYMBOL', config.SYMBOL)
        config.LEVERAGE = int(os.getenv('LEVERAGE', config.LEVERAGE))
        config.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', config.MAX_POSITION_SIZE))
        config.STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', config.STOP_LOSS_PCT))
        config.TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', config.TAKE_PROFIT_PCT))
        
        # Database
        config.DATABASE_URL = os.getenv('DATABASE_URL', config.DATABASE_URL)
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.BYBIT_API_KEY or not self.BYBIT_API_SECRET:
            return False
        
        if self.LEVERAGE < 1 or self.LEVERAGE > 100:
            return False
        
        if self.MAX_POSITION_SIZE <= 0:
            return False
        
        return True
