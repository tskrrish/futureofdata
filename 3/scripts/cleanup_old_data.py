#!/usr/bin/env python3
"""
Data Cleanup Script
Removes old data, temporary files, and performs maintenance tasks
"""

import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import VolunteerDatabase

logger = logging.getLogger(__name__)


class DataCleanup:
    """Handles cleanup of old data and temporary files"""
    
    def __init__(self):
        self.db = VolunteerDatabase()
        self.stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "records_cleaned": 0,
            "errors": 0
        }
    
    async def cleanup_old_backups(self, backup_dir: str = "./backups", days: int = 30) -> dict:
        """Remove backup files older than specified days"""
        logger.info(f"Cleaning up backups older than {days} days from {backup_dir}")
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            logger.warning(f"Backup directory does not exist: {backup_dir}")
            return {"cleaned": 0}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        bytes_freed = 0
        
        try:
            for item in backup_path.iterdir():
                if item.is_file() or item.is_dir():
                    # Check modification time
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                            bytes_freed += size
                            cleaned_count += 1
                            logger.debug(f"Deleted file: {item}")
                        elif item.is_dir():
                            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                            bytes_freed += size
                            cleaned_count += 1
                            logger.debug(f"Deleted directory: {item}")
            
            self.stats["files_deleted"] += cleaned_count
            self.stats["bytes_freed"] += bytes_freed
            
            logger.info(f"Cleaned {cleaned_count} backup items, freed {bytes_freed / 1024 / 1024:.2f} MB")
            
            return {
                "cleaned": cleaned_count,
                "bytes_freed": bytes_freed,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error cleaning backups: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    async def cleanup_temp_files(self, temp_dir: str = "./temp") -> dict:
        """Remove temporary files"""
        logger.info(f"Cleaning up temporary files from {temp_dir}")
        
        temp_path = Path(temp_dir)
        if not temp_path.exists():
            logger.info("Temp directory does not exist, nothing to clean")
            return {"cleaned": 0}
        
        cleaned_count = 0
        bytes_freed = 0
        
        try:
            for item in temp_path.rglob('*'):
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    bytes_freed += size
                    cleaned_count += 1
                    logger.debug(f"Deleted temp file: {item}")
            
            # Remove empty directories
            for item in temp_path.rglob('*'):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
                    logger.debug(f"Deleted empty directory: {item}")
            
            self.stats["files_deleted"] += cleaned_count
            self.stats["bytes_freed"] += bytes_freed
            
            logger.info(f"Cleaned {cleaned_count} temp files, freed {bytes_freed / 1024 / 1024:.2f} MB")
            
            return {
                "cleaned": cleaned_count,
                "bytes_freed": bytes_freed,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    async def cleanup_old_logs(self, log_dir: str = ".", days: int = 30) -> dict:
        """Remove log files older than specified days"""
        logger.info(f"Cleaning up log files older than {days} days")
        
        log_path = Path(log_dir)
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        bytes_freed = 0
        
        try:
            # Look for log files (*.log, *.log.*)
            log_patterns = ['*.log', '*.log.*']
            
            for pattern in log_patterns:
                for log_file in log_path.glob(pattern):
                    if log_file.is_file():
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        
                        if mtime < cutoff_date:
                            size = log_file.stat().st_size
                            log_file.unlink()
                            bytes_freed += size
                            cleaned_count += 1
                            logger.debug(f"Deleted log file: {log_file}")
            
            self.stats["files_deleted"] += cleaned_count
            self.stats["bytes_freed"] += bytes_freed
            
            logger.info(f"Cleaned {cleaned_count} log files, freed {bytes_freed / 1024 / 1024:.2f} MB")
            
            return {
                "cleaned": cleaned_count,
                "bytes_freed": bytes_freed,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error cleaning log files: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    async def cleanup_old_conversations(self, days: int = 90) -> dict:
        """Remove old conversation data from database"""
        logger.info(f"Cleaning up conversations older than {days} days")
        
        if not self.db._is_available():
            logger.warning("Database not available, skipping conversation cleanup")
            return {"cleaned": 0}
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            # This would require implementing deletion methods in database.py
            # For now, this is a placeholder
            logger.info("Conversation cleanup not yet implemented in database layer")
            
            return {
                "cleaned": 0,
                "success": True,
                "note": "Database cleanup methods need implementation"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning conversations: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    def get_disk_usage(self, path: str = ".") -> dict:
        """Get disk usage statistics"""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return {"error": "Path does not exist"}
        
        total_size = 0
        file_count = 0
        
        if path_obj.is_file():
            return {
                "path": str(path_obj),
                "size_bytes": path_obj.stat().st_size,
                "size_mb": path_obj.stat().st_size / 1024 / 1024,
                "files": 1
            }
        
        for item in path_obj.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
        
        return {
            "path": str(path_obj),
            "size_bytes": total_size,
            "size_mb": total_size / 1024 / 1024,
            "files": file_count
        }
    
    def print_stats(self):
        """Print cleanup statistics"""
        logger.info("=== Cleanup Statistics ===")
        logger.info(f"Files deleted: {self.stats['files_deleted']}")
        logger.info(f"Space freed: {self.stats['bytes_freed'] / 1024 / 1024:.2f} MB")
        logger.info(f"Records cleaned: {self.stats['records_cleaned']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=== End Statistics ===")


async def main():
    """Main script execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old data and temporary files")
    parser.add_argument("--backups", type=int, default=30, help="Days to keep backups (default: 30)")
    parser.add_argument("--logs", type=int, default=30, help="Days to keep logs (default: 30)")
    parser.add_argument("--conversations", type=int, default=90, help="Days to keep conversations (default: 90)")
    parser.add_argument("--temp", action="store_true", help="Clean temporary files")
    parser.add_argument("--all", action="store_true", help="Run all cleanup tasks")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be deleted")
        return
    
    cleanup = DataCleanup()
    
    # Show disk usage before cleanup
    logger.info("Disk usage before cleanup:")
    for path in ["./backups", "./temp", "."]:
        usage = cleanup.get_disk_usage(path)
        if "error" not in usage:
            logger.info(f"  {usage['path']}: {usage['size_mb']:.2f} MB ({usage['files']} files)")
    
    # Run cleanup tasks
    if args.all or args.backups:
        await cleanup.cleanup_old_backups(days=args.backups)
    
    if args.all or args.temp:
        await cleanup.cleanup_temp_files()
    
    if args.all or args.logs:
        await cleanup.cleanup_old_logs(days=args.logs)
    
    if args.all or args.conversations:
        await cleanup.cleanup_old_conversations(days=args.conversations)
    
    # Print final statistics
    cleanup.print_stats()
    
    logger.info("Cleanup completed successfully")


if __name__ == "__main__":
    asyncio.run(main())