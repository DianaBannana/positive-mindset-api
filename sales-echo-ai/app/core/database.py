"""
Database Connection and Prisma Client
"""

from prisma import Prisma
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Prisma client instance
prisma = Prisma()


async def connect_db():
    """Connect to the database"""
    try:
        await prisma.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def disconnect_db():
    """Disconnect from the database"""
    try:
        await prisma.disconnect()
        logger.info("Database disconnected successfully")
    except Exception as e:
        logger.error(f"Failed to disconnect from database: {e}")


def get_db():
    """Dependency for getting database client"""
    return prisma
