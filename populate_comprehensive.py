#!/usr/bin/env python3
"""
Comprehensive Database Population Script
Populates database with comprehensive ingredient data from EWG and other sources
"""

import asyncio
import logging
from database import populate_comprehensive_database

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to populate database comprehensively"""
    logger.info("Starting comprehensive database population...")
    
    try:
        await populate_comprehensive_database()
        logger.info("Comprehensive database population completed successfully!")
    except Exception as e:
        logger.error(f"Error during database population: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())