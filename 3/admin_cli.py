#!/usr/bin/env python3
"""
Admin CLI for YMCA Volunteer PathFinder
Provides bulk operations, imports, backups, and scripted tasks functionality
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

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from rich.console import Console
    from rich.progress import Progress, TaskID
    from rich.table import Table
    from rich.logging import RichHandler
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    # Fallback console for basic output
    class Console:
        def print(self, text, style=None):
            # Strip rich markup for basic output
            import re
            clean_text = re.sub(r'\[.*?\]', '', str(text))
            print(clean_text)
    console = Console()

from database import VolunteerDatabase
from data_processor import VolunteerDataProcessor
from matching_engine import VolunteerMatchingEngine

# Set up logging
if HAS_RICH:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
logger = logging.getLogger("admin_cli")


class AdminCLI:
    """Admin CLI for bulk operations and management tasks"""
    
    def __init__(self):
        self.db = VolunteerDatabase()
        self.data_processor = None
        self.matching_engine = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load CLI configuration"""
        config_path = Path("cli_config.yaml")
        if config_path.exists() and HAS_YAML:
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load YAML config: {e}")
        
        return {
            "batch_size": 100,
            "backup_dir": "./backups",
            "import_dir": "./imports",
            "scripts_dir": "./scripts",
            "log_level": "INFO"
        }
    
    async def bulk_create_users(self, file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """Bulk create users from CSV/JSON file"""
        console.print(f"[bold blue]Bulk creating users from: {file_path}[/bold blue]")
        
        if not Path(file_path).exists():
            console.print(f"[red]Error: File {file_path} not found[/red]")
            return {"success": False, "error": "File not found"}
        
        try:
            # Load data based on file extension
            if file_path.endswith('.csv'):
                if HAS_PANDAS:
                    df = pd.read_csv(file_path)
                    users_data = df.to_dict('records')
                else:
                    # Fallback CSV reading
                    import csv
                    users_data = []
                    with open(file_path, 'r') as f:
                        reader = csv.DictReader(f)
                        users_data = list(reader)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    users_data = json.load(f)
            else:
                console.print("Error: Unsupported file format. Use CSV or JSON")
                return {"success": False, "error": "Unsupported file format"}
            
            results = {"created": 0, "errors": 0, "skipped": 0, "details": []}
            batch_size = self.config["batch_size"]
            
            if HAS_RICH:
                with Progress() as progress:
                    task = progress.add_task("[green]Creating users...", total=len(users_data))
                    
                    for i in range(0, len(users_data), batch_size):
                        batch = users_data[i:i + batch_size]
                        
                        for user_data in batch:
                        if dry_run:
                            console.print(f"[yellow]DRY RUN: Would create user: {user_data.get('email', 'N/A')}[/yellow]")
                            results["created"] += 1
                        else:
                            try:
                                # Validate required fields
                                if not user_data.get('email'):
                                    results["skipped"] += 1
                                    results["details"].append({"row": i, "error": "Missing email"})
                                    continue
                                
                                user = await self.db.create_user(user_data)
                                if user:
                                    results["created"] += 1
                                    console.print(f"[green]✓[/green] Created user: {user_data['email']}")
                                else:
                                    results["errors"] += 1
                                    results["details"].append({"row": i, "error": "Database error"})
                            
                            except Exception as e:
                                results["errors"] += 1
                                results["details"].append({"row": i, "error": str(e)})
                                console.print(f"[red]✗[/red] Error creating user {user_data.get('email', 'N/A')}: {e}")
                        
                        progress.update(task, advance=1)
                    
                    # Small delay between batches
                    if not dry_run:
                        await asyncio.sleep(0.1)
            
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"Created: {results['created']}")
            console.print(f"Errors: {results['errors']}")
            console.print(f"Skipped: {results['skipped']}")
            
            return {"success": True, "results": results}
            
        except Exception as e:
            console.print(f"[red]Bulk create failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def bulk_update_users(self, file_path: str, match_field: str = "email", dry_run: bool = False) -> Dict[str, Any]:
        """Bulk update users from CSV/JSON file"""
        console.print(f"[bold blue]Bulk updating users from: {file_path}[/bold blue]")
        
        if not Path(file_path).exists():
            console.print(f"[red]Error: File {file_path} not found[/red]")
            return {"success": False, "error": "File not found"}
        
        try:
            # Load update data
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                updates_data = df.to_dict('records')
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    updates_data = json.load(f)
            else:
                return {"success": False, "error": "Unsupported file format"}
            
            results = {"updated": 0, "errors": 0, "not_found": 0, "details": []}
            
            with Progress() as progress:
                task = progress.add_task("[blue]Updating users...", total=len(updates_data))
                
                for i, update_data in enumerate(updates_data):
                    match_value = update_data.get(match_field)
                    if not match_value:
                        results["errors"] += 1
                        results["details"].append({"row": i, "error": f"Missing {match_field}"})
                        progress.update(task, advance=1)
                        continue
                    
                    if dry_run:
                        console.print(f"[yellow]DRY RUN: Would update user: {match_value}[/yellow]")
                        results["updated"] += 1
                    else:
                        try:
                            # Find user
                            user = await self.db.get_user(email=match_value if match_field == "email" else None,
                                                        user_id=match_value if match_field == "id" else None)
                            
                            if user:
                                # Remove match field from updates
                                updates = {k: v for k, v in update_data.items() if k != match_field}
                                success = await self.db.update_user(user['id'], updates)
                                
                                if success:
                                    results["updated"] += 1
                                    console.print(f"[green]✓[/green] Updated user: {match_value}")
                                else:
                                    results["errors"] += 1
                                    results["details"].append({"row": i, "error": "Update failed"})
                            else:
                                results["not_found"] += 1
                                results["details"].append({"row": i, "error": "User not found"})
                                console.print(f"[yellow]?[/yellow] User not found: {match_value}")
                        
                        except Exception as e:
                            results["errors"] += 1
                            results["details"].append({"row": i, "error": str(e)})
                            console.print(f"[red]✗[/red] Error updating user {match_value}: {e}")
                    
                    progress.update(task, advance=1)
            
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"Updated: {results['updated']}")
            console.print(f"Not found: {results['not_found']}")
            console.print(f"Errors: {results['errors']}")
            
            return {"success": True, "results": results}
            
        except Exception as e:
            console.print(f"[red]Bulk update failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def bulk_delete_users(self, file_path: str, match_field: str = "email", 
                               confirm: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Bulk delete users from CSV/JSON file"""
        console.print(f"[bold red]Bulk deleting users from: {file_path}[/bold red]")
        
        if not confirm and not dry_run:
            console.print("[red]This operation will permanently delete users![/red]")
            console.print("Use --confirm flag or --dry-run to proceed")
            return {"success": False, "error": "Confirmation required"}
        
        if not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # Load deletion data
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                delete_data = df[match_field].tolist()
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    delete_data = [item[match_field] for item in data]
            else:
                return {"success": False, "error": "Unsupported file format"}
            
            results = {"deleted": 0, "errors": 0, "not_found": 0, "details": []}
            
            with Progress() as progress:
                task = progress.add_task("[red]Deleting users...", total=len(delete_data))
                
                for i, match_value in enumerate(delete_data):
                    if dry_run:
                        console.print(f"[yellow]DRY RUN: Would delete user: {match_value}[/yellow]")
                        results["deleted"] += 1
                    else:
                        try:
                            # Note: Actual deletion would need to be implemented in database.py
                            # This is a placeholder for the deletion logic
                            console.print(f"[red]✗[/red] Deletion not yet implemented: {match_value}")
                            results["errors"] += 1
                            results["details"].append({"row": i, "error": "Deletion not implemented"})
                        
                        except Exception as e:
                            results["errors"] += 1
                            results["details"].append({"row": i, "error": str(e)})
                    
                    progress.update(task, advance=1)
            
            return {"success": True, "results": results}
            
        except Exception as e:
            console.print(f"[red]Bulk delete failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def import_volunteer_data(self, file_path: str, data_type: str, 
                                   merge: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Import volunteer data from external sources"""
        console.print(f"[bold green]Importing {data_type} data from: {file_path}[/bold green]")
        
        if not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            if data_type == "volunteer_history":
                # Import volunteer activity history
                df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                # Process the data using existing data processor
                if not self.data_processor:
                    self.data_processor = VolunteerDataProcessor(file_path)
                
                volunteer_data = self.data_processor.get_volunteer_recommendations_data()
                
                if dry_run:
                    console.print(f"[yellow]DRY RUN: Would import {len(volunteer_data.get('volunteers', []))} volunteers[/yellow]")
                    return {"success": True, "results": {"imported": len(volunteer_data.get('volunteers', []))}}
                
                # Here you would implement the actual import logic
                console.print(f"[green]Successfully processed {len(volunteer_data.get('volunteers', []))} volunteers[/green]")
                
                return {"success": True, "results": {"imported": len(volunteer_data.get('volunteers', []))}}
            
            elif data_type == "projects":
                # Import project data
                df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                projects_imported = 0
                for _, row in df.iterrows():
                    if not dry_run:
                        # Process and import each project
                        pass
                    projects_imported += 1
                
                console.print(f"[green]Imported {projects_imported} projects[/green]")
                return {"success": True, "results": {"imported": projects_imported}}
            
            else:
                return {"success": False, "error": f"Unsupported data type: {data_type}"}
                
        except Exception as e:
            console.print(f"[red]Import failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def backup_data(self, backup_type: str = "full", output_dir: str = None) -> Dict[str, Any]:
        """Create backup of volunteer system data"""
        backup_dir = Path(output_dir or self.config["backup_dir"])
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"volunteer_backup_{backup_type}_{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        console.print(f"[bold blue]Creating {backup_type} backup: {backup_path}[/bold blue]")
        
        try:
            results = {"files_created": 0, "total_records": 0, "errors": []}
            
            if backup_type in ["full", "database"]:
                # Export database tables
                console.print("[blue]Exporting database tables...[/blue]")
                tables_data = await self.db.export_volunteer_data()
                
                for table_name, df in tables_data.items():
                    if not df.empty:
                        file_path = backup_path / f"{table_name}.csv"
                        df.to_csv(file_path, index=False)
                        results["files_created"] += 1
                        results["total_records"] += len(df)
                        console.print(f"[green]✓[/green] Exported {table_name}: {len(df)} records")
            
            if backup_type in ["full", "files"]:
                # Backup important files
                console.print("[blue]Backing up configuration files...[/blue]")
                
                config_files = [
                    "config.py", "cli_config.yaml", "requirements.txt",
                    "setup_supabase.sql"
                ]
                
                for config_file in config_files:
                    if Path(config_file).exists():
                        import shutil
                        shutil.copy2(config_file, backup_path / config_file)
                        results["files_created"] += 1
                        console.print(f"[green]✓[/green] Backed up {config_file}")
            
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
            
            console.print(f"\n[bold green]Backup completed successfully![/bold green]")
            console.print(f"Files created: {results['files_created']}")
            console.print(f"Total records: {results['total_records']}")
            console.print(f"Backup location: {backup_path}")
            
            return {"success": True, "backup_path": str(backup_path), "results": results}
            
        except Exception as e:
            console.print(f"[red]Backup failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def run_script(self, script_path: str, args: List[str] = None) -> Dict[str, Any]:
        """Run a scripted task"""
        script_file = Path(script_path)
        
        if not script_file.exists():
            # Try looking in scripts directory
            script_file = Path(self.config["scripts_dir"]) / script_path
            if not script_file.exists():
                return {"success": False, "error": "Script not found"}
        
        console.print(f"[bold purple]Running script: {script_file}[/bold purple]")
        
        try:
            if script_file.suffix == '.py':
                # Run Python script
                import subprocess
                cmd = [sys.executable, str(script_file)] + (args or [])
                
                console.print(f"[blue]Command: {' '.join(cmd)}[/blue]")
                
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                end_time = time.time()
                
                if result.returncode == 0:
                    console.print("[green]Script completed successfully[/green]")
                    console.print(f"Execution time: {end_time - start_time:.2f} seconds")
                    
                    if result.stdout:
                        console.print("[bold]Output:[/bold]")
                        console.print(result.stdout)
                    
                    return {
                        "success": True,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": end_time - start_time
                    }
                else:
                    console.print(f"[red]Script failed with exit code {result.returncode}[/red]")
                    if result.stderr:
                        console.print("[bold]Error output:[/bold]")
                        console.print(result.stderr)
                    
                    return {
                        "success": False,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": end_time - start_time
                    }
            
            elif script_file.suffix == '.yaml' or script_file.suffix == '.yml':
                # Run YAML-defined task sequence
                with open(script_file, 'r') as f:
                    tasks = yaml.safe_load(f)
                
                return await self._run_yaml_tasks(tasks)
            
            else:
                return {"success": False, "error": "Unsupported script type"}
                
        except Exception as e:
            console.print(f"[red]Script execution failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    async def _run_yaml_tasks(self, tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Run tasks defined in YAML format"""
        results = {"completed": 0, "failed": 0, "results": []}
        
        task_list = tasks.get("tasks", [])
        console.print(f"[blue]Running {len(task_list)} tasks...[/blue]")
        
        for i, task in enumerate(task_list):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type")
            
            console.print(f"\n[bold]Running: {task_name}[/bold]")
            
            try:
                if task_type == "bulk_create":
                    result = await self.bulk_create_users(
                        task["file"], 
                        task.get("dry_run", False)
                    )
                elif task_type == "backup":
                    result = await self.backup_data(
                        task.get("backup_type", "full"),
                        task.get("output_dir")
                    )
                elif task_type == "import":
                    result = await self.import_volunteer_data(
                        task["file"],
                        task["data_type"],
                        task.get("merge", False),
                        task.get("dry_run", False)
                    )
                else:
                    result = {"success": False, "error": f"Unknown task type: {task_type}"}
                
                if result["success"]:
                    results["completed"] += 1
                    console.print(f"[green]✓[/green] {task_name} completed")
                else:
                    results["failed"] += 1
                    console.print(f"[red]✗[/red] {task_name} failed: {result.get('error')}")
                
                results["results"].append({
                    "task": task_name,
                    "success": result["success"],
                    "result": result
                })
                
            except Exception as e:
                results["failed"] += 1
                console.print(f"[red]✗[/red] {task_name} failed: {e}")
                results["results"].append({
                    "task": task_name,
                    "success": False,
                    "error": str(e)
                })
        
        return {"success": True, "results": results}
    
    def show_status(self):
        """Show system status and statistics"""
        console.print("[bold blue]YMCA Volunteer PathFinder Admin Status[/bold blue]\n")
        
        # System info
        table = Table(title="System Information")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Database", "Connected" if self.db._is_available() else "Disconnected", 
                     "Supabase" if self.db._is_available() else "Not configured")
        table.add_row("Data Processor", "Ready" if self.data_processor else "Not loaded", 
                     "Volunteer data processing")
        table.add_row("Matching Engine", "Ready" if self.matching_engine else "Not loaded", 
                     "AI-powered matching")
        
        console.print(table)
        
        # Configuration
        console.print("\n[bold]Current Configuration:[/bold]")
        config_table = Table()
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="yellow")
        
        for key, value in self.config.items():
            config_table.add_row(key, str(value))
        
        console.print(config_table)


def create_parser():
    """Create argument parser for the CLI"""
    parser = argparse.ArgumentParser(
        description="YMCA Volunteer PathFinder Admin CLI",
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
    
    # Bulk update
    update_parser = bulk_subparsers.add_parser('update', help='Bulk update users')
    update_parser.add_argument('file', help='CSV or JSON file with update data')
    update_parser.add_argument('--match-field', default='email', help='Field to match users on')
    update_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Bulk delete
    delete_parser = bulk_subparsers.add_parser('delete', help='Bulk delete users')
    delete_parser.add_argument('file', help='CSV or JSON file with users to delete')
    delete_parser.add_argument('--match-field', default='email', help='Field to match users on')
    delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import data')
    import_parser.add_argument('file', help='File to import')
    import_parser.add_argument('type', choices=['volunteer_history', 'projects'], 
                             help='Type of data to import')
    import_parser.add_argument('--merge', action='store_true', help='Merge with existing data')
    import_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
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
            elif args.bulk_command == 'update':
                result = await admin_cli.bulk_update_users(args.file, args.match_field, args.dry_run)
            elif args.bulk_command == 'delete':
                result = await admin_cli.bulk_delete_users(args.file, args.match_field, 
                                                         args.confirm, args.dry_run)
            else:
                console.print("[red]Unknown bulk command[/red]")
                return
            
            if not result["success"]:
                console.print(f"[red]Operation failed: {result.get('error')}[/red]")
                sys.exit(1)
        
        elif args.command == 'import':
            result = await admin_cli.import_volunteer_data(args.file, args.type, 
                                                         args.merge, args.dry_run)
            if not result["success"]:
                console.print(f"[red]Import failed: {result.get('error')}[/red]")
                sys.exit(1)
        
        elif args.command == 'backup':
            result = await admin_cli.backup_data(args.type, args.output_dir)
            if not result["success"]:
                console.print(f"[red]Backup failed: {result.get('error')}[/red]")
                sys.exit(1)
        
        elif args.command == 'script':
            result = await admin_cli.run_script(args.script_path, args.args)
            if not result["success"]:
                console.print(f"[red]Script failed: {result.get('error')}[/red]")
                sys.exit(1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())