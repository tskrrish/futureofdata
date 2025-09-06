# YMCA Volunteer PathFinder Admin CLI

A comprehensive command-line interface for bulk operations, data imports, backups, and scripted tasks for the YMCA Volunteer PathFinder system.

## Features

### 🔧 Bulk Operations
- **Bulk Create**: Create multiple users from CSV/JSON files
- **Bulk Update**: Update existing user records in batches
- **Bulk Delete**: Delete multiple users (with safety confirmations)
- **Batch Processing**: Process large datasets efficiently with configurable batch sizes

### 📥 Data Import
- **Volunteer History**: Import volunteer activity data from Excel/CSV files
- **Project Data**: Import volunteer project information
- **Flexible Formats**: Support for CSV, JSON, and Excel formats
- **Data Validation**: Automatic data validation and error reporting

### 💾 Backup & Restore
- **Full Backups**: Complete system backup including database and files
- **Database Backups**: Database-only backups for quick restoration
- **File Backups**: Configuration and important files backup
- **Automated Retention**: Configurable backup retention policies

### 🤖 Scripted Tasks
- **Python Scripts**: Execute custom Python automation scripts
- **YAML Workflows**: Define complex task sequences in YAML format
- **Scheduled Tasks**: Support for maintenance and recurring operations
- **Task Monitoring**: Progress tracking and error handling

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Make CLI Executable**:
   ```bash
   chmod +x admin_cli.py
   ```

3. **Configure Settings**:
   - Copy and customize `cli_config.yaml`
   - Ensure database credentials are configured

## Usage Examples

### System Status
```bash
python admin_cli.py status
```

### Bulk Operations

**Create Users**:
```bash
# Dry run to preview
python admin_cli.py bulk create users_data.csv --dry-run

# Actually create users
python admin_cli.py bulk create users_data.csv
```

**Update Users**:
```bash
# Update users matching by email
python admin_cli.py bulk update user_updates.csv --match-field email

# Update users matching by ID
python admin_cli.py bulk update user_updates.csv --match-field id --dry-run
```

**Delete Users**:
```bash
# Requires confirmation
python admin_cli.py bulk delete users_to_delete.csv --confirm

# Dry run to see what would be deleted
python admin_cli.py bulk delete users_to_delete.csv --dry-run
```

### Data Import

**Import Volunteer History**:
```bash
python admin_cli.py import volunteer_data.xlsx volunteer_history
```

**Import Projects**:
```bash
python admin_cli.py import projects.csv projects --merge
```

### Backups

**Full Backup**:
```bash
python admin_cli.py backup --type full
```

**Database Only**:
```bash
python admin_cli.py backup --type database --output-dir ./my-backups
```

### Scripted Tasks

**Run Python Script**:
```bash
python admin_cli.py script volunteer_sync.py --file data.xlsx --verbose
```

**Run YAML Workflow**:
```bash
python admin_cli.py script daily_maintenance.yaml
```

## File Formats

### User Import CSV Format
```csv
email,first_name,last_name,phone,age,gender,city,state,zip_code,is_ymca_member,member_branch
john.doe@email.com,John,Doe,555-1234,35,Male,Cincinnati,OH,45202,TRUE,Blue Ash YMCA
```

### User Update CSV Format
```csv
email,phone,city,member_branch
john.doe@email.com,555-1111,Cincinnati,M.E. Lyons YMCA
```

### YAML Task Format
```yaml
name: "My Maintenance Tasks"
description: "Custom maintenance workflow"

tasks:
  - name: "Create Backup"
    type: "backup"
    backup_type: "database"
    
  - name: "Clean Old Files"
    type: "cleanup"
    target: "temp"
```

## Configuration

Edit `cli_config.yaml` to customize:

```yaml
# Batch processing
batch_size: 100
max_concurrent: 10

# Directories
backup_dir: "./backups"
import_dir: "./imports"
scripts_dir: "./scripts"

# Safety settings
require_confirmation: true
max_batch_delete: 1000

# Performance
memory_limit: "1GB"
script_timeout: 3600
```

## Available Scripts

### Pre-built Scripts
- **`volunteer_sync.py`**: Sync volunteer data from Excel files
- **`cleanup_old_data.py`**: Clean old backups, logs, and temporary files
- **`daily_maintenance.yaml`**: Daily automated maintenance tasks
- **`weekly_maintenance.yaml`**: Weekly comprehensive maintenance

### Custom Scripts
Place custom scripts in the `scripts/` directory. They can be:
- Python files (`.py`) for custom logic
- YAML files (`.yaml`) for task sequences

## Safety Features

### Dry Run Mode
All destructive operations support `--dry-run` to preview changes:
```bash
python admin_cli.py bulk delete users.csv --dry-run
```

### Confirmation Requirements
Destructive operations require explicit confirmation:
```bash
python admin_cli.py bulk delete users.csv --confirm
```

### Batch Limits
Configurable limits prevent accidental mass operations:
- `max_batch_delete`: Maximum records to delete in one operation
- `batch_size`: Records processed per batch

### Backup Before Changes
Always create backups before major operations:
```bash
python admin_cli.py backup --type database
```

## Logging

The CLI provides comprehensive logging:
- **Console Output**: Real-time progress with rich formatting
- **Log Files**: Detailed logs saved to `admin_cli.log`
- **Error Tracking**: Full error details and stack traces
- **Statistics**: Operation summaries and performance metrics

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database credentials in configuration
   - Verify Supabase connection settings

2. **File Not Found**
   - Use absolute paths or check working directory
   - Verify file permissions

3. **Memory Issues**
   - Reduce batch_size in configuration
   - Use streaming for large files

4. **Script Timeout**
   - Increase script_timeout in configuration
   - Optimize script performance

### Getting Help

```bash
python admin_cli.py --help
python admin_cli.py bulk --help
python admin_cli.py script --help
```

## Development

### Adding New Commands
1. Extend the `AdminCLI` class in `admin_cli.py`
2. Add argument parsing in `create_parser()`
3. Add command handling in `main()`

### Custom Task Types
For YAML workflows, add new task types in `_run_yaml_tasks()` method.

### Testing
```bash
# Test with dry-run mode
python admin_cli.py bulk create test_data.csv --dry-run

# Test scripts
python scripts/volunteer_sync.py --help
```

## Security Considerations

- **Sensitive Data**: Never commit files containing real user data
- **Permissions**: Ensure proper file and directory permissions
- **Backups**: Store backups securely and encrypt if necessary
- **Access Control**: Limit CLI access to authorized administrators only

## Support

For issues and feature requests:
- Check logs for detailed error information
- Use dry-run mode to test operations safely
- Review configuration settings
- Contact system administrators for database issues