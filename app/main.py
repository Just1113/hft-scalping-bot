import asyncio
import logging
import sys
import signal
import os
from datetime import datetime
from dotenv import load_dotenv

from app.config import TradingConfig
from core.trading_engine import TradingEngine
from telegram_bot.bot import TelegramBot
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class ScalpingBot:
    def __init__(self):
        load_dotenv()
        self.config = TradingConfig.from_env()
        
        # Validate required configuration
        self._validate_config()
        
        self.trading_engine = TradingEngine(self.config)
        self.telegram_bot = TelegramBot(self.config, self.trading_engine)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Health check endpoint for Render
        self.health_check_port = int(os.getenv('HEALTH_CHECK_PORT', 8080))
    
    def _validate_config(self):
        """Validate required configuration"""
        required_vars = ['BYBIT_API_KEY', 'BYBIT_API_SECRET']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            logger.error(f"Missing required environment variables: {missing}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Graceful shutdown procedure"""
        logger.info("Shutting down trading bot...")
        
        # Stop trading engine
        if hasattr(self, 'trading_engine'):
            await self.trading_engine.stop()
        
        logger.info("Shutdown complete")
        sys.exit(0)
    
    async def start_health_check(self):
        """Start health check endpoint for Render"""
        from fastapi import FastAPI
        import uvicorn
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            yield
            # Shutdown
        
        app = FastAPI(lifespan=lifespan)
        
        @app.get("/")
        async def root():
            return {
                "status": "running",
                "service": "hft-scalping-bot",
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "engine_running": self.trading_engine.is_running,
                "open_trades": len(self.trading_engine.open_trades),
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/metrics")
        async def get_metrics():
            return {
                "metrics": self.trading_engine.metrics,
                "config": {
                    "symbol": self.config.SYMBOL,
                    "leverage": self.config.LEVERAGE,
                    "max_position_size": self.config.MAX_POSITION_SIZE
                }
            }
        
        # Start health check server in background
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.health_check_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run server in background task
        asyncio.create_task(server.serve())
        logger.info(f"Health check server started on port {self.health_check_port}")
    
    async def run(self):
        """Main application runner"""
        try:
            logger.info("=" * 60)
            logger.info("Starting High Frequency Scalping Bot")
            logger.info(f"Environment: {'TESTNET' if self.config.BYBIT_TESTNET else 'LIVE'}")
            logger.info(f"Trading Symbol: {self.config.SYMBOL}")
            logger.info(f"Leverage: {self.config.LEVERAGE}x")
            logger.info("=" * 60)
            
            # Start health check endpoint for Render
            await self.start_health_check()
            
            # Initialize database
            from app.database import init_db
            await init_db()
            
            # Start Telegram bot in background (if token provided)
            if self.config.TELEGRAM_BOT_TOKEN:
                import threading
                telegram_thread = threading.Thread(
                    target=self.telegram_bot.run_polling,
                    daemon=True
                )
                telegram_thread.start()
                logger.info("Telegram bot started")
            else:
                logger.warning("Telegram bot token not configured")
            
            # Start trading engine
            await self.trading_engine.start()
            
            # Send startup notification
            if self.config.TELEGRAM_BOT_TOKEN and self.config.TELEGRAM_CHAT_ID:
                await self.telegram_bot.send_notification(
                    f"🤖 *Bot Started*\n\n"
                    f"• Environment: {'TESTNET' if self.config.BYBIT_TESTNET else 'LIVE'}\n"
                    f"• Symbol: {self.config.SYMBOL}\n"
                    f"• Leverage: {self.config.LEVERAGE}x\n"
                    f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            # Keep application running
            logger.info("Bot is now running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(3600)  # Check every hour
                
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            
            # Send error notification
            if self.config.TELEGRAM_BOT_TOKEN and self.config.TELEGRAM_CHAT_ID:
                await self.telegram_bot.send_notification(
                    f"❌ *Bot Crashed*\n\nError: {str(e)[:200]}"
                )
            
            await self.shutdown()

def main():
    """Application entry point"""
    try:
        bot = ScalpingBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
