from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from datetime import datetime
import os
from app.config import TradingConfig

config = TradingConfig.from_env()

# Use SQLite for Render (file-based)
if config.RENDER:
    # Use file-based SQLite on Render
    DATABASE_URL = "sqlite+aiosqlite:///./data/trades.db"
else:
    DATABASE_URL = config.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class TradeLog(Base):
    __tablename__ = 'trades'
    
    id = Column(String, primary_key=True)
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    leverage = Column(Integer)
    status = Column(String)
    pnl = Column(Float)
    pnl_percentage = Column(Float)
    opened_at = Column(DateTime, index=True)
    closed_at = Column(DateTime)
    reason = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session

async def log_trade(trade_data: dict):
    """Log a trade to database"""
    async with AsyncSessionLocal() as session:
        try:
            trade_log = TradeLog(**trade_data)
            session.add(trade_log)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise e

async def get_recent_trades(limit: int = 50):
    """Get recent trades"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import desc
        result = await session.execute(
            TradeLog.__table__.select()
            .order_by(desc(TradeLog.opened_at))
            .limit(limit)
        )
        return result.fetchall()

async def update_trade(trade_id: str, update_data: dict):
    """Update trade record"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                TradeLog.__table__.update()
                .where(TradeLog.id == trade_id)
                .values(**update_data)
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            await session.rollback()
            raise e

async def get_bot_setting(key: str):
    """Get bot setting"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            BotSettings.__table__.select()
            .where(BotSettings.key == key)
        )
        row = result.fetchone()
        return row.value if row else None

async def set_bot_setting(key: str, value):
    """Set bot setting"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if setting exists
            result = await session.execute(
                BotSettings.__table__.select()
                .where(BotSettings.key == key)
            )
            row = result.fetchone()
            
            if row:
                # Update existing
                await session.execute(
                    BotSettings.__table__.update()
                    .where(BotSettings.key == key)
                    .values(value=value)
                )
            else:
                # Insert new
                setting = BotSettings(key=key, value=value)
                session.add(setting)
            
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise e
