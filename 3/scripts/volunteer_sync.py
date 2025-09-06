#!/usr/bin/env python3
"""
Volunteer Data Synchronization Script
Syncs volunteer data from external sources and updates the database
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import VolunteerDatabase
from data_processor import VolunteerDataProcessor

logger = logging.getLogger(__name__)


class VolunteerSync:
    """Handles synchronization of volunteer data from external sources"""
    
    def __init__(self):
        self.db = VolunteerDatabase()
        self.stats = {
            "processed": 0,
            "updated": 0,
            "created": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
    
    async def sync_from_excel(self, file_path: str) -> dict:
        """Sync volunteer data from Excel file"""
        logger.info(f"Starting sync from Excel file: {file_path}")
        
        try:
            # Process the Excel file
            processor = VolunteerDataProcessor(file_path)
            volunteer_data = processor.get_volunteer_recommendations_data()
            
            volunteers = volunteer_data.get('volunteers', [])
            interactions = volunteer_data.get('interactions', [])
            
            logger.info(f"Found {len(volunteers)} volunteers and {len(interactions)} interactions")
            
            # Sync volunteers
            for volunteer in volunteers:
                self.stats["processed"] += 1
                
                try:
                    # Check if volunteer exists
                    existing_user = await self.db.get_user(email=volunteer.get('email'))
                    
                    if existing_user:
                        # Update existing volunteer
                        updates = {k: v for k, v in volunteer.items() if k != 'id'}
                        success = await self.db.update_user(existing_user['id'], updates)
                        if success:
                            self.stats["updated"] += 1
                            logger.debug(f"Updated volunteer: {volunteer.get('email')}")
                    else:
                        # Create new volunteer
                        new_user = await self.db.create_user(volunteer)
                        if new_user:
                            self.stats["created"] += 1
                            logger.debug(f"Created volunteer: {volunteer.get('email')}")
                
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Error processing volunteer {volunteer.get('email')}: {e}")
            
            # Log final statistics
            self._log_stats()
            
            return {
                "success": True,
                "stats": self.stats,
                "message": f"Sync completed: {self.stats['processed']} processed, {self.stats['created']} created, {self.stats['updated']} updated"
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats
            }
    
    async def sync_volunteer_preferences(self, data: dict) -> dict:
        """Sync volunteer preferences from processed data"""
        logger.info("Syncing volunteer preferences")
        
        preferences_synced = 0
        
        for volunteer_id, prefs in data.items():
            try:
                success = await self.db.save_user_preferences(volunteer_id, prefs)
                if success:
                    preferences_synced += 1
                    logger.debug(f"Synced preferences for volunteer: {volunteer_id}")
            except Exception as e:
                logger.error(f"Error syncing preferences for {volunteer_id}: {e}")
                self.stats["errors"] += 1
        
        logger.info(f"Synced preferences for {preferences_synced} volunteers")
        return {"preferences_synced": preferences_synced}
    
    def _log_stats(self):
        """Log synchronization statistics"""
        duration = datetime.now() - self.stats["start_time"]
        logger.info("=== Synchronization Statistics ===")
        logger.info(f"Duration: {duration}")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Created: {self.stats['created']}")
        logger.info(f"Updated: {self.stats['updated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=== End Statistics ===")


async def main():
    """Main script execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync volunteer data from external sources")
    parser.add_argument("--file", required=True, help="Path to Excel file to sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        return
    
    # Check if file exists
    if not Path(args.file).exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # Run synchronization
    sync = VolunteerSync()
    result = await sync.sync_from_excel(args.file)
    
    if result["success"]:
        logger.info("Synchronization completed successfully")
        print(json.dumps(result, indent=2, default=str))
    else:
        logger.error("Synchronization failed")
        print(json.dumps(result, indent=2, default=str))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())