#!/usr/bin/env python3
"""
Admin CLI for YMCA Volunteer PathFinder - Simplified Version
Provides bulk operations, imports, backups, and scripted tasks functionality
Works with minimal dependencies
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Basic imports that should be available
import subprocess
import shutil

# Try to import optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from database import VolunteerDatabase
    from data_processor import VolunteerDataProcessor
    from matching_engine import VolunteerMatchingEngine
    HAS_DB_MODULES = True
except ImportError:
    HAS_DB_MODULES = False
    # Create mock classes for testing
    class VolunteerDatabase:
        def __init__(self): pass
        def _is_available(self): return False
        async def create_user(self, data): return None
        async def get_user(self, **kwargs): return None
        async def update_user(self, user_id, updates): return False
        async def export_volunteer_data(self): return {}
    
    class VolunteerDataProcessor:
        def __init__(self, path): pass
        def get_volunteer_recommendations_data(self): return {"volunteers": [], "interactions": []}
    
    class VolunteerMatchingEngine:
        def __init__(self, data): pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("admin_cli")


def print_status(message: str, status: str = "info"):
    """Print status message with simple formatting"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbols = {
        "info": "ℹ",
        "success": "✓",
        "error": "✗",
        "warning": "⚠"
    }
    symbol = status_symbols.get(status, "•")
    print(f"[{timestamp}] {symbol} {message}")


def print_table(data: List[Dict], title: str = None):
    """Print data in a simple table format"""
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    
    if not data:
        print("No data to display")
        return
    
    # Get all keys
    keys = set()
    for row in data:
        keys.update(row.keys())
    keys = sorted(keys)
    
    # Calculate column widths
    widths = {}
    for key in keys:
        widths[key] = max(len(str(key)), max(len(str(row.get(key, ""))) for row in data))
    
    # Print header
    header = " | ".join(str(key).ljust(widths[key]) for key in keys)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in data:
        row_str = " | ".join(str(row.get(key, "")).ljust(widths[key]) for key in keys)
        print(row_str)
    print()


class AdminCLI:
    """Admin CLI for bulk operations and management tasks"""
    
    def __init__(self):
        self.db = VolunteerDatabase() if HAS_DB_MODULES else None
        self.data_processor = None
        self.matching_engine = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load CLI configuration from JSON file (fallback for YAML)"""
        # Try YAML first
        config_path = Path("cli_config.yaml")
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except ImportError:
                print_status("YAML not available, trying JSON config", "warning")
        
        # Try JSON fallback
        json_config_path = Path("cli_config.json")
        if json_config_path.exists():
            with open(json_config_path, 'r') as f:
                return json.load(f)
        
        # Default config
        return {
            "batch_size": 100,
            "backup_dir": "./backups",
            "import_dir": "./imports",
            "scripts_dir": "./scripts",
            "log_level": "INFO"
        }
    
    async def bulk_create_users(self, file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """Bulk create users from CSV/JSON file"""
        print_status(f"Bulk creating users from: {file_path}")
        
        if not Path(file_path).exists():
            print_status(f"File {file_path} not found", "error")
            return {"success": False, "error": "File not found"}
        
        try:
            # Load data based on file extension
            if file_path.endswith('.csv'):
                users_data = []
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    users_data = list(reader)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    users_data = json.load(f)
            else:
                print_status("Unsupported file format. Use CSV or JSON", "error")
                return {"success": False, "error": "Unsupported file format"}
            
            results = {"created": 0, "errors": 0, "skipped": 0, "details": []}
            batch_size = self.config["batch_size"]
            total = len(users_data)
            
            print_status(f"Processing {total} users in batches of {batch_size}")
            
            for i in range(0, total, batch_size):
                batch = users_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total + batch_size - 1) // batch_size
                
                print_status(f"Processing batch {batch_num}/{total_batches}")
                
                for j, user_data in enumerate(batch):
                    current = i + j + 1
                    
                    if dry_run:
                        print(f"  [{current}/{total}] DRY RUN: Would create user: {user_data.get('email', 'N/A')}")
                        results["created"] += 1
                    else:
                        try:
                            # Validate required fields
                            if not user_data.get('email'):
                                results["skipped"] += 1
                                results["details"].append({"row": current, "error": "Missing email"})
                                continue
                            
                            if self.db:
                                user = await self.db.create_user(user_data)
                                if user:
                                    results["created"] += 1
                                    print(f"  [{current}/{total}] ✓ Created user: {user_data['email']}")
                                else:
                                    results["errors"] += 1
                                    results["details"].append({"row": current, "error": "Database error"})
                            else:
                                print(f"  [{current}/{total}] ✓ Would create user: {user_data['email']} (no database)")
                                results["created"] += 1
                        
                        except Exception as e:
                            results["errors"] += 1
                            results["details"].append({"row": current, "error": str(e)})
                            print_status(f"Error creating user {user_data.get('email', 'N/A')}: {e}", "error")
                
                # Small delay between batches
                if not dry_run:
                    await asyncio.sleep(0.1)
            
            # Print summary
            print_status("Summary:")
            print(f"  Created: {results['created']}")
            print(f"  Errors: {results['errors']}")
            print(f"  Skipped: {results['skipped']}")
            
            return {"success": True, "results": results}
            
        except Exception as e:
            print_status(f"Bulk create failed: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def backup_data(self, backup_type: str = "full", output_dir: str = None) -> Dict[str, Any]:
        """Create backup of volunteer system data"""
        backup_dir = Path(output_dir or self.config["backup_dir"])
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"volunteer_backup_{backup_type}_{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        print_status(f"Creating {backup_type} backup: {backup_path}")
        
        try:
            results = {"files_created": 0, "total_records": 0, "errors": []}
            
            if backup_type in ["full", "database"]:
                print_status("Exporting database tables...")
                if self.db:
                    tables_data = await self.db.export_volunteer_data()
                    
                    for table_name, df in tables_data.items():
                        try:
                            if hasattr(df, 'empty') and not df.empty:
                                file_path = backup_path / f"{table_name}.csv"
                                df.to_csv(file_path, index=False)
                                results["files_created"] += 1
                                results["total_records"] += len(df)
                                print_status(f"Exported {table_name}: {len(df)} records", "success")
                        except Exception as e:
                            results["errors"].append(f"Failed to export {table_name}: {e}")
                else:
                    print_status("Database not available", "warning")
            
            if backup_type in ["full", "files"]:
                print_status("Backing up configuration files...")
                
                config_files = [
                    "config.py", "cli_config.yaml", "cli_config.json", 
                    "requirements.txt", "setup_supabase.sql"
                ]
                
                for config_file in config_files:
                    if Path(config_file).exists():
                        shutil.copy2(config_file, backup_path / config_file)
                        results["files_created"] += 1
                        print_status(f"Backed up {config_file}", "success")
            
            # Create backup metadata
            metadata = {
                "backup_type": backup_type,
                "timestamp": datetime.now().isoformat(),
                "files_created": results["files_created"],
                "total_records": results["total_records"],
                "version": "1.0.0"
            }
            
            metadata_path = backup_path / "backup_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print_status("Backup completed successfully!", "success")
            print(f"Files created: {results['files_created']}")
            print(f"Total records: {results['total_records']}")
            print(f"Backup location: {backup_path}")
            
            return {"success": True, "backup_path": str(backup_path), "results": results}
            
        except Exception as e:
            print_status(f"Backup failed: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def run_script(self, script_path: str, args: List[str] = None) -> Dict[str, Any]:
        """Run a scripted task"""
        script_file = Path(script_path)
        
        if not script_file.exists():
            # Try looking in scripts directory
            script_file = Path(self.config["scripts_dir"]) / script_path
            if not script_file.exists():
                return {"success": False, "error": "Script not found"}
        
        print_status(f"Running script: {script_file}")
        
        try:
            if script_file.suffix == '.py':
                # Run Python script
                cmd = [sys.executable, str(script_file)] + (args or [])
                
                print_status(f"Command: {' '.join(cmd)}")
                
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                end_time = time.time()
                
                if result.returncode == 0:
                    print_status("Script completed successfully", "success")
                    print(f"Execution time: {end_time - start_time:.2f} seconds")
                    
                    if result.stdout:
                        print("Output:")
                        print(result.stdout)
                    
                    return {
                        "success": True,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": end_time - start_time
                    }
                else:
                    print_status(f"Script failed with exit code {result.returncode}", "error")
                    if result.stderr:
                        print("Error output:")
                        print(result.stderr)
                    
                    return {
                        "success": False,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": end_time - start_time
                    }
            
            else:
                return {"success": False, "error": "Only Python scripts supported in simple mode"}
                
        except Exception as e:
            print_status(f"Script execution failed: {e}", "error")
            return {"success": False, "error": str(e)}
    
    def show_status(self):
        """Show system status and statistics"""
        print_status("YMCA Volunteer PathFinder Admin Status")
        print("=" * 50)
        
        # System info
        status_data = [
            {
                "Component": "Database",
                "Status": "Connected" if (self.db and self.db._is_available()) else "Disconnected",
                "Details": "Supabase" if (self.db and self.db._is_available()) else "Not configured"
            },
            {
                "Component": "Data Processor", 
                "Status": "Ready" if self.data_processor else "Not loaded",
                "Details": "Volunteer data processing"
            },
            {
                "Component": "Matching Engine",
                "Status": "Ready" if self.matching_engine else "Not loaded", 
                "Details": "AI-powered matching"
            },
            {
                "Component": "Pandas",
                "Status": "Available" if HAS_PANDAS else "Not available",
                "Details": "Data processing library"
            }
        ]
        
        print_table(status_data, "System Information")
        
        # Configuration
        config_data = [{"Setting": key, "Value": str(value)} for key, value in self.config.items()]
        print_table(config_data, "Current Configuration")


def create_parser():
    """Create argument parser for the CLI"""
    parser = argparse.ArgumentParser(
        description="YMCA Volunteer PathFinder Admin CLI (Simplified)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Bulk operations
    bulk_parser = subparsers.add_parser('bulk', help='Bulk operations')
    bulk_subparsers = bulk_parser.add_subparsers(dest='bulk_command')
    
    # Bulk create
    create_parser_cmd = bulk_subparsers.add_parser('create', help='Bulk create users')
    create_parser_cmd.add_argument('file', help='CSV or JSON file with user data')
    create_parser_cmd.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument('--type', choices=['full', 'database', 'files'], 
                             default='full', help='Backup type')
    backup_parser.add_argument('--output-dir', help='Output directory')
    
    # Script command
    script_parser = subparsers.add_parser('script', help='Run scripted task')
    script_parser.add_argument('script_path', help='Path to script file')
    script_parser.add_argument('args', nargs='*', help='Script arguments')
    
    return parser


async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    admin_cli = AdminCLI()
    
    try:
        if args.command == 'status':
            admin_cli.show_status()
        
        elif args.command == 'bulk':
            if args.bulk_command == 'create':
                result = await admin_cli.bulk_create_users(args.file, args.dry_run)
                if not result["success"]:
                    print_status(f"Operation failed: {result.get('error')}", "error")
                    sys.exit(1)
            else:
                print_status("Only 'create' bulk command implemented in simple mode", "warning")
        
        elif args.command == 'backup':
            result = await admin_cli.backup_data(args.type, args.output_dir)
            if not result["success"]:
                print_status(f"Backup failed: {result.get('error')}", "error")
                sys.exit(1)
        
        elif args.command == 'script':
            result = await admin_cli.run_script(args.script_path, args.args)
            if not result["success"]:
                print_status(f"Script failed: {result.get('error')}", "error")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print_status("Operation cancelled by user", "warning")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())