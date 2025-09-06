"""
Advanced Schema Inference and Versioning System
Automatically infers data types, tracks schema evolution, detects drift, and suggests migrations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import hashlib
import re
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter
import warnings
from database import VolunteerDatabase

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class DataType(Enum):
    """Enumeration of supported data types"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"
    JSON = "json"
    CATEGORICAL = "categorical"
    TEXT = "text"
    BINARY = "binary"
    UNKNOWN = "unknown"

class ChangeType(Enum):
    """Types of schema changes"""
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed" 
    TYPE_CHANGED = "type_changed"
    CONSTRAINT_CHANGED = "constraint_changed"
    NULL_TOLERANCE_CHANGED = "null_tolerance_changed"
    VALUE_RANGE_CHANGED = "value_range_changed"
    PATTERN_CHANGED = "pattern_changed"
    CARDINALITY_CHANGED = "cardinality_changed"

@dataclass
class ColumnSchema:
    """Schema definition for a single column"""
    name: str
    data_type: DataType
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    default_value: Optional[Any] = None
    cardinality: Optional[int] = None
    null_percentage: float = 0.0
    sample_values: List[str] = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.sample_values is None:
            self.sample_values = []

@dataclass 
class TableSchema:
    """Schema definition for a table"""
    name: str
    columns: List[ColumnSchema]
    row_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    version: str = "1.0.0"
    checksum: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for schema version tracking"""
        schema_dict = {
            'name': self.name,
            'columns': [asdict(col) for col in self.columns],
            'version': self.version
        }
        schema_json = json.dumps(schema_dict, sort_keys=True, default=str)
        return hashlib.sha256(schema_json.encode()).hexdigest()

@dataclass
class SchemaChange:
    """Represents a change in schema"""
    change_type: ChangeType
    table_name: str
    column_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    impact_score: float = 0.0
    description: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class SchemaInferenceEngine:
    """Main engine for schema inference and type detection"""
    
    def __init__(self):
        self.type_detectors = {
            DataType.UUID: self._detect_uuid,
            DataType.EMAIL: self._detect_email,
            DataType.PHONE: self._detect_phone,
            DataType.URL: self._detect_url,
            DataType.DATETIME: self._detect_datetime,
            DataType.DATE: self._detect_date,
            DataType.TIME: self._detect_time,
            DataType.BOOLEAN: self._detect_boolean,
            DataType.INTEGER: self._detect_integer,
            DataType.FLOAT: self._detect_float,
            DataType.JSON: self._detect_json,
            DataType.CATEGORICAL: self._detect_categorical,
            DataType.TEXT: self._detect_text,
            DataType.STRING: self._detect_string
        }
    
    def infer_column_schema(self, series: pd.Series, column_name: str) -> ColumnSchema:
        """Infer schema for a single column"""
        # Remove null values for analysis
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return ColumnSchema(
                name=column_name,
                data_type=DataType.UNKNOWN,
                nullable=True,
                null_percentage=1.0,
                confidence_score=0.0
            )
        
        # Detect data type with confidence scoring
        detected_type, confidence = self._detect_data_type(non_null_series)
        
        # Calculate basic statistics
        nullable = series.isnull().any()
        null_percentage = series.isnull().sum() / len(series)
        unique_count = series.nunique()
        cardinality = unique_count
        
        # Get sample values
        sample_values = non_null_series.sample(min(5, len(non_null_series))).astype(str).tolist()
        
        # Create column schema
        column_schema = ColumnSchema(
            name=column_name,
            data_type=detected_type,
            nullable=nullable,
            null_percentage=null_percentage,
            cardinality=cardinality,
            sample_values=sample_values,
            confidence_score=confidence
        )
        
        # Set type-specific attributes
        self._set_type_specific_attributes(column_schema, non_null_series)
        
        return column_schema
    
    def _detect_data_type(self, series: pd.Series) -> Tuple[DataType, float]:
        """Detect the most likely data type for a series"""
        sample_size = min(100, len(series))
        sample = series.sample(sample_size) if len(series) > sample_size else series
        
        # Test each detector and calculate confidence
        type_scores = {}
        
        for data_type, detector in self.type_detectors.items():
            try:
                confidence = detector(sample)
                if confidence > 0:
                    type_scores[data_type] = confidence
            except Exception as e:
                logger.debug(f"Error detecting {data_type} for column: {e}")
                continue
        
        if not type_scores:
            return DataType.UNKNOWN, 0.0
        
        # Return type with highest confidence
        best_type = max(type_scores, key=type_scores.get)
        best_confidence = type_scores[best_type]
        
        return best_type, best_confidence
    
    def _detect_uuid(self, series: pd.Series) -> float:
        """Detect UUID pattern"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        matches = series.astype(str).str.match(uuid_pattern, case=False).sum()
        return matches / len(series) if len(series) > 0 else 0
    
    def _detect_email(self, series: pd.Series) -> float:
        """Detect email pattern"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        matches = series.astype(str).str.match(email_pattern, case=False).sum()
        return matches / len(series) if len(series) > 0 else 0
    
    def _detect_phone(self, series: pd.Series) -> float:
        """Detect phone number pattern"""
        phone_patterns = [
            r'^\d{10}$',  # 10 digits
            r'^\d{3}-\d{3}-\d{4}$',  # xxx-xxx-xxxx
            r'^\(\d{3}\)\s*\d{3}-\d{4}$',  # (xxx) xxx-xxxx
            r'^\+\d{1,3}\s*\d{10}$'  # +x xxxxxxxxxx
        ]
        
        total_matches = 0
        for pattern in phone_patterns:
            matches = series.astype(str).str.match(pattern).sum()
            total_matches += matches
        
        return min(total_matches / len(series), 1.0) if len(series) > 0 else 0
    
    def _detect_url(self, series: pd.Series) -> float:
        """Detect URL pattern"""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        matches = series.astype(str).str.match(url_pattern, case=False).sum()
        return matches / len(series) if len(series) > 0 else 0
    
    def _detect_datetime(self, series: pd.Series) -> float:
        """Detect datetime values"""
        try:
            converted = pd.to_datetime(series, errors='coerce')
            valid_dates = converted.notna().sum()
            confidence = valid_dates / len(series)
            
            # Additional check for time component
            has_time = converted.dt.time.apply(lambda x: x != x.replace(hour=0, minute=0, second=0, microsecond=0) if pd.notna(x) else False).sum()
            
            return confidence if has_time > 0 else 0
        except:
            return 0
    
    def _detect_date(self, series: pd.Series) -> float:
        """Detect date-only values"""
        try:
            converted = pd.to_datetime(series, errors='coerce')
            valid_dates = converted.notna().sum()
            confidence = valid_dates / len(series)
            
            # Check if most values are dates without time
            has_time = converted.dt.time.apply(lambda x: x != x.replace(hour=0, minute=0, second=0, microsecond=0) if pd.notna(x) else False).sum()
            time_ratio = has_time / valid_dates if valid_dates > 0 else 0
            
            return confidence * (1 - time_ratio) if confidence > 0.7 else 0
        except:
            return 0
    
    def _detect_time(self, series: pd.Series) -> float:
        """Detect time values"""
        time_patterns = [
            r'^\d{1,2}:\d{2}$',  # HH:MM
            r'^\d{1,2}:\d{2}:\d{2}$',  # HH:MM:SS
            r'^\d{1,2}:\d{2}\s*(AM|PM)$'  # HH:MM AM/PM
        ]
        
        total_matches = 0
        for pattern in time_patterns:
            matches = series.astype(str).str.match(pattern, case=False).sum()
            total_matches += matches
        
        return min(total_matches / len(series), 1.0) if len(series) > 0 else 0
    
    def _detect_boolean(self, series: pd.Series) -> float:
        """Detect boolean values"""
        bool_values = {'true', 'false', '1', '0', 'yes', 'no', 'y', 'n', 't', 'f'}
        string_series = series.astype(str).str.lower().str.strip()
        matches = string_series.isin(bool_values).sum()
        return matches / len(series) if len(series) > 0 else 0
    
    def _detect_integer(self, series: pd.Series) -> float:
        """Detect integer values"""
        try:
            # Try to convert to numeric
            numeric = pd.to_numeric(series, errors='coerce')
            valid_numeric = numeric.notna()
            
            if valid_numeric.sum() == 0:
                return 0
            
            # Check if all valid numeric values are integers
            integer_check = numeric[valid_numeric] == numeric[valid_numeric].astype(int)
            integer_ratio = integer_check.sum() / valid_numeric.sum()
            
            return integer_ratio * (valid_numeric.sum() / len(series))
        except:
            return 0
    
    def _detect_float(self, series: pd.Series) -> float:
        """Detect float values"""
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            valid_numeric = numeric.notna()
            
            if valid_numeric.sum() == 0:
                return 0
            
            # Check if values have decimal places
            has_decimals = (numeric[valid_numeric] % 1 != 0).sum()
            
            return (has_decimals / valid_numeric.sum()) * (valid_numeric.sum() / len(series))
        except:
            return 0
    
    def _detect_json(self, series: pd.Series) -> float:
        """Detect JSON values"""
        def is_json(x):
            try:
                json.loads(str(x))
                return True
            except:
                return False
        
        json_count = series.apply(is_json).sum()
        return json_count / len(series) if len(series) > 0 else 0
    
    def _detect_categorical(self, series: pd.Series) -> float:
        """Detect categorical data"""
        unique_ratio = series.nunique() / len(series)
        
        # Consider categorical if unique ratio is low and not obviously other types
        if unique_ratio < 0.1 and series.nunique() > 1:
            return 0.8
        elif unique_ratio < 0.05:
            return 0.9
        else:
            return 0
    
    def _detect_text(self, series: pd.Series) -> float:
        """Detect text (long strings)"""
        string_series = series.astype(str)
        avg_length = string_series.str.len().mean()
        
        # Consider text if average length > 50 characters
        if avg_length > 50:
            return min(avg_length / 200, 1.0)
        else:
            return 0
    
    def _detect_string(self, series: pd.Series) -> float:
        """Detect generic string (fallback)"""
        return 0.1  # Low confidence fallback
    
    def _set_type_specific_attributes(self, column_schema: ColumnSchema, series: pd.Series):
        """Set attributes specific to detected data type"""
        if column_schema.data_type in [DataType.INTEGER, DataType.FLOAT]:
            numeric_series = pd.to_numeric(series, errors='coerce').dropna()
            if len(numeric_series) > 0:
                column_schema.min_value = float(numeric_series.min())
                column_schema.max_value = float(numeric_series.max())
        
        elif column_schema.data_type in [DataType.STRING, DataType.TEXT, DataType.EMAIL]:
            str_series = series.astype(str)
            lengths = str_series.str.len()
            column_schema.min_length = int(lengths.min())
            column_schema.max_length = int(lengths.max())
        
        elif column_schema.data_type == DataType.CATEGORICAL:
            unique_values = series.unique()
            if len(unique_values) <= 20:  # Only store if reasonable number
                column_schema.allowed_values = [str(v) for v in unique_values if pd.notna(v)]
        
        # Check for uniqueness
        column_schema.unique = series.nunique() == len(series)

class SchemaVersioningSystem:
    """System for tracking schema versions and changes"""
    
    def __init__(self, database: VolunteerDatabase = None):
        self.database = database
        self.schema_history: Dict[str, List[TableSchema]] = defaultdict(list)
        self.change_log: List[SchemaChange] = []
    
    async def initialize_schema_tables(self):
        """Initialize schema tracking tables in database"""
        if not self.database or not self.database._is_available():
            logger.warning("Database not available for schema tracking")
            return False
        
        # Schema versions table
        schema_versions_sql = """
        CREATE TABLE IF NOT EXISTS schema_versions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            version VARCHAR(20) NOT NULL,
            schema_definition JSONB NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            row_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(table_name, version)
        );
        """
        
        # Schema changes table
        schema_changes_sql = """
        CREATE TABLE IF NOT EXISTS schema_changes (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            version_from VARCHAR(20),
            version_to VARCHAR(20),
            change_type VARCHAR(50) NOT NULL,
            column_name VARCHAR(100),
            old_value JSONB,
            new_value JSONB,
            impact_score DECIMAL(3,2) DEFAULT 0.0,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        print("🗄️  Schema tracking tables ready for setup")
        print("📝 Run these SQL commands in your database:")
        print(schema_versions_sql)
        print(schema_changes_sql)
        return True
    
    def register_schema_version(self, schema: TableSchema) -> bool:
        """Register a new schema version"""
        try:
            # Add to in-memory history
            self.schema_history[schema.name].append(schema)
            
            # Store in database if available
            if self.database and self.database._is_available():
                return self._store_schema_in_database(schema)
            
            return True
        except Exception as e:
            logger.error(f"Error registering schema version: {e}")
            return False
    
    def _store_schema_in_database(self, schema: TableSchema) -> bool:
        """Store schema version in database"""
        try:
            schema_data = {
                'table_name': schema.name,
                'version': schema.version,
                'schema_definition': json.dumps(asdict(schema), default=str),
                'checksum': schema.checksum,
                'row_count': schema.row_count,
                'created_at': schema.created_at.isoformat(),
                'updated_at': schema.updated_at.isoformat()
            }
            
            result = self.database.supabase.table('schema_versions').insert(schema_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error storing schema in database: {e}")
            return False
    
    def detect_schema_drift(self, old_schema: TableSchema, new_schema: TableSchema) -> List[SchemaChange]:
        """Detect changes between two schema versions"""
        changes = []
        
        # Create column lookup maps
        old_columns = {col.name: col for col in old_schema.columns}
        new_columns = {col.name: col for col in new_schema.columns}
        
        # Detect added columns
        for col_name, col_schema in new_columns.items():
            if col_name not in old_columns:
                changes.append(SchemaChange(
                    change_type=ChangeType.COLUMN_ADDED,
                    table_name=new_schema.name,
                    column_name=col_name,
                    new_value=asdict(col_schema),
                    impact_score=0.3,
                    description=f"Column '{col_name}' added with type {col_schema.data_type.value}"
                ))
        
        # Detect removed columns
        for col_name, col_schema in old_columns.items():
            if col_name not in new_columns:
                changes.append(SchemaChange(
                    change_type=ChangeType.COLUMN_REMOVED,
                    table_name=new_schema.name,
                    column_name=col_name,
                    old_value=asdict(col_schema),
                    impact_score=0.8,  # High impact
                    description=f"Column '{col_name}' removed"
                ))
        
        # Detect changed columns
        for col_name in set(old_columns.keys()) & set(new_columns.keys()):
            old_col = old_columns[col_name]
            new_col = new_columns[col_name]
            
            column_changes = self._detect_column_changes(old_col, new_col, new_schema.name)
            changes.extend(column_changes)
        
        # Store changes
        self.change_log.extend(changes)
        
        # Store in database if available
        if self.database and self.database._is_available():
            for change in changes:
                self._store_change_in_database(change, old_schema.version, new_schema.version)
        
        return changes
    
    def _detect_column_changes(self, old_col: ColumnSchema, new_col: ColumnSchema, table_name: str) -> List[SchemaChange]:
        """Detect changes in a specific column"""
        changes = []
        
        # Type change
        if old_col.data_type != new_col.data_type:
            changes.append(SchemaChange(
                change_type=ChangeType.TYPE_CHANGED,
                table_name=table_name,
                column_name=old_col.name,
                old_value=old_col.data_type.value,
                new_value=new_col.data_type.value,
                impact_score=0.7,
                description=f"Column '{old_col.name}' type changed from {old_col.data_type.value} to {new_col.data_type.value}"
            ))
        
        # Null tolerance change
        if old_col.nullable != new_col.nullable:
            changes.append(SchemaChange(
                change_type=ChangeType.NULL_TOLERANCE_CHANGED,
                table_name=table_name,
                column_name=old_col.name,
                old_value=old_col.nullable,
                new_value=new_col.nullable,
                impact_score=0.5,
                description=f"Column '{old_col.name}' null tolerance changed"
            ))
        
        # Value range change (for numeric types)
        if old_col.data_type in [DataType.INTEGER, DataType.FLOAT]:
            if (old_col.min_value != new_col.min_value or 
                old_col.max_value != new_col.max_value):
                changes.append(SchemaChange(
                    change_type=ChangeType.VALUE_RANGE_CHANGED,
                    table_name=table_name,
                    column_name=old_col.name,
                    old_value={"min": old_col.min_value, "max": old_col.max_value},
                    new_value={"min": new_col.min_value, "max": new_col.max_value},
                    impact_score=0.3,
                    description=f"Column '{old_col.name}' value range changed"
                ))
        
        # Cardinality change
        if old_col.cardinality and new_col.cardinality:
            cardinality_change = abs(new_col.cardinality - old_col.cardinality) / old_col.cardinality
            if cardinality_change > 0.2:  # 20% change threshold
                changes.append(SchemaChange(
                    change_type=ChangeType.CARDINALITY_CHANGED,
                    table_name=table_name,
                    column_name=old_col.name,
                    old_value=old_col.cardinality,
                    new_value=new_col.cardinality,
                    impact_score=min(cardinality_change, 1.0),
                    description=f"Column '{old_col.name}' cardinality changed significantly"
                ))
        
        return changes
    
    def _store_change_in_database(self, change: SchemaChange, version_from: str, version_to: str):
        """Store schema change in database"""
        try:
            change_data = {
                'table_name': change.table_name,
                'version_from': version_from,
                'version_to': version_to,
                'change_type': change.change_type.value,
                'column_name': change.column_name,
                'old_value': json.dumps(change.old_value, default=str) if change.old_value is not None else None,
                'new_value': json.dumps(change.new_value, default=str) if change.new_value is not None else None,
                'impact_score': change.impact_score,
                'description': change.description,
                'created_at': change.timestamp.isoformat()
            }
            
            self.database.supabase.table('schema_changes').insert(change_data).execute()
        except Exception as e:
            logger.error(f"Error storing change in database: {e}")
    
    def get_schema_history(self, table_name: str) -> List[TableSchema]:
        """Get schema history for a table"""
        return self.schema_history.get(table_name, [])
    
    def get_latest_schema(self, table_name: str) -> Optional[TableSchema]:
        """Get the latest schema version for a table"""
        history = self.get_schema_history(table_name)
        return history[-1] if history else None

class MigrationSuggestionEngine:
    """Engine for suggesting database migrations based on schema changes"""
    
    def __init__(self):
        self.migration_templates = {
            ChangeType.COLUMN_ADDED: self._suggest_add_column,
            ChangeType.COLUMN_REMOVED: self._suggest_remove_column,
            ChangeType.TYPE_CHANGED: self._suggest_change_type,
            ChangeType.NULL_TOLERANCE_CHANGED: self._suggest_change_nullable,
            ChangeType.VALUE_RANGE_CHANGED: self._suggest_add_constraints,
            ChangeType.CARDINALITY_CHANGED: self._suggest_optimize_indexes
        }
    
    def generate_migration_suggestions(self, changes: List[SchemaChange]) -> Dict[str, List[str]]:
        """Generate migration suggestions for detected changes"""
        suggestions = defaultdict(list)
        
        # Group changes by table
        changes_by_table = defaultdict(list)
        for change in changes:
            changes_by_table[change.table_name].append(change)
        
        # Generate suggestions for each table
        for table_name, table_changes in changes_by_table.items():
            table_suggestions = []
            
            for change in sorted(table_changes, key=lambda x: x.impact_score, reverse=True):
                if change.change_type in self.migration_templates:
                    suggestion = self.migration_templates[change.change_type](change)
                    if suggestion:
                        table_suggestions.extend(suggestion)
            
            if table_suggestions:
                suggestions[table_name] = table_suggestions
        
        return dict(suggestions)
    
    def _suggest_add_column(self, change: SchemaChange) -> List[str]:
        """Suggest SQL for adding a column"""
        col_data = change.new_value
        data_type = col_data.get('data_type', 'string')
        nullable = col_data.get('nullable', True)
        default_value = col_data.get('default_value')
        
        # Map data types to SQL types
        sql_type_map = {
            'integer': 'INTEGER',
            'float': 'DECIMAL',
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'boolean': 'BOOLEAN',
            'datetime': 'TIMESTAMP',
            'date': 'DATE',
            'time': 'TIME',
            'email': 'VARCHAR(255)',
            'phone': 'VARCHAR(20)',
            'uuid': 'UUID'
        }
        
        sql_type = sql_type_map.get(data_type, 'VARCHAR(255)')
        null_clause = '' if nullable else ' NOT NULL'
        default_clause = f" DEFAULT '{default_value}'" if default_value else ''
        
        return [
            f"-- Add new column {change.column_name}",
            f"ALTER TABLE {change.table_name} ADD COLUMN {change.column_name} {sql_type}{null_clause}{default_clause};"
        ]
    
    def _suggest_remove_column(self, change: SchemaChange) -> List[str]:
        """Suggest SQL for removing a column"""
        return [
            f"-- Remove column {change.column_name} (HIGH IMPACT - Review before applying)",
            f"-- Consider backing up data first: CREATE TABLE backup_table AS SELECT {change.column_name} FROM {change.table_name};",
            f"ALTER TABLE {change.table_name} DROP COLUMN {change.column_name};"
        ]
    
    def _suggest_change_type(self, change: SchemaChange) -> List[str]:
        """Suggest SQL for changing column type"""
        old_type = change.old_value
        new_type = change.new_value
        
        return [
            f"-- Change column {change.column_name} type from {old_type} to {new_type}",
            f"-- Review data compatibility before applying",
            f"ALTER TABLE {change.table_name} ALTER COLUMN {change.column_name} TYPE {new_type};"
        ]
    
    def _suggest_change_nullable(self, change: SchemaChange) -> List[str]:
        """Suggest SQL for changing null constraints"""
        if change.new_value:  # Making nullable
            return [f"ALTER TABLE {change.table_name} ALTER COLUMN {change.column_name} DROP NOT NULL;"]
        else:  # Making not nullable
            return [
                f"-- Set NOT NULL constraint on {change.column_name}",
                f"-- First ensure no null values exist:",
                f"-- UPDATE {change.table_name} SET {change.column_name} = 'default_value' WHERE {change.column_name} IS NULL;",
                f"ALTER TABLE {change.table_name} ALTER COLUMN {change.column_name} SET NOT NULL;"
            ]
    
    def _suggest_add_constraints(self, change: SchemaChange) -> List[str]:
        """Suggest adding value constraints"""
        return [
            f"-- Consider adding constraints based on new value range for {change.column_name}",
            f"-- ALTER TABLE {change.table_name} ADD CONSTRAINT check_{change.column_name}_range",
            f"--   CHECK ({change.column_name} >= {change.new_value.get('min', 'min_value')} AND {change.column_name} <= {change.new_value.get('max', 'max_value')});"
        ]
    
    def _suggest_optimize_indexes(self, change: SchemaChange) -> List[str]:
        """Suggest index optimization for cardinality changes"""
        if change.new_value > change.old_value * 2:  # Significant increase
            return [
                f"-- Consider adding index due to increased cardinality in {change.column_name}",
                f"CREATE INDEX idx_{change.table_name}_{change.column_name} ON {change.table_name}({change.column_name});"
            ]
        return []

class SchemaInferenceManager:
    """Main manager class that orchestrates schema inference and versioning"""
    
    def __init__(self, database: VolunteerDatabase = None):
        self.inference_engine = SchemaInferenceEngine()
        self.versioning_system = SchemaVersioningSystem(database)
        self.migration_engine = MigrationSuggestionEngine()
        self.database = database
    
    async def initialize(self):
        """Initialize the schema tracking system"""
        await self.versioning_system.initialize_schema_tables()
        return True
    
    def infer_table_schema(self, dataframe: pd.DataFrame, table_name: str, version: str = None) -> TableSchema:
        """Infer schema for an entire table"""
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🔍 Inferring schema for table: {table_name}")
        
        # Infer schema for each column
        columns = []
        for column_name in dataframe.columns:
            print(f"  📊 Analyzing column: {column_name}")
            column_schema = self.inference_engine.infer_column_schema(dataframe[column_name], column_name)
            columns.append(column_schema)
        
        # Create table schema
        table_schema = TableSchema(
            name=table_name,
            columns=columns,
            row_count=len(dataframe),
            version=version
        )
        
        # Register the schema version
        self.versioning_system.register_schema_version(table_schema)
        
        print(f"✅ Schema inferred for {table_name} with {len(columns)} columns")
        return table_schema
    
    def detect_and_analyze_drift(self, table_name: str, new_schema: TableSchema) -> Dict[str, Any]:
        """Detect schema drift and provide analysis"""
        print(f"🔍 Detecting schema drift for: {table_name}")
        
        # Get previous schema
        previous_schema = self.versioning_system.get_latest_schema(table_name)
        
        if not previous_schema:
            print("ℹ️  No previous schema found - this is the first version")
            return {
                'has_drift': False,
                'changes': [],
                'migration_suggestions': {},
                'summary': 'First schema version registered'
            }
        
        # Detect changes
        changes = self.versioning_system.detect_schema_drift(previous_schema, new_schema)
        
        # Generate migration suggestions
        migration_suggestions = self.migration_engine.generate_migration_suggestions(changes)
        
        # Create summary
        summary = self._create_drift_summary(changes)
        
        result = {
            'has_drift': len(changes) > 0,
            'changes': [asdict(change) for change in changes],
            'migration_suggestions': migration_suggestions,
            'summary': summary,
            'previous_version': previous_schema.version,
            'new_version': new_schema.version
        }
        
        if changes:
            print(f"⚠️  Detected {len(changes)} schema changes")
            for change in changes[:5]:  # Show first 5
                print(f"   • {change.description}")
        else:
            print("✅ No schema drift detected")
        
        return result
    
    def _create_drift_summary(self, changes: List[SchemaChange]) -> str:
        """Create a human-readable summary of schema changes"""
        if not changes:
            return "No changes detected"
        
        change_counts = Counter(change.change_type for change in changes)
        high_impact_changes = [c for c in changes if c.impact_score > 0.5]
        
        summary_parts = []
        for change_type, count in change_counts.items():
            summary_parts.append(f"{count} {change_type.value.replace('_', ' ')}")
        
        summary = f"Detected: {', '.join(summary_parts)}"
        
        if high_impact_changes:
            summary += f". {len(high_impact_changes)} high-impact changes require attention."
        
        return summary
    
    async def analyze_data_source(self, data_source, table_name: str, version: str = None) -> Dict[str, Any]:
        """Analyze a data source (DataFrame, CSV, Excel) for schema inference and drift"""
        
        # Convert data source to DataFrame
        if isinstance(data_source, str):
            if data_source.endswith('.csv'):
                df = pd.read_csv(data_source)
            elif data_source.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(data_source)
            else:
                raise ValueError("Unsupported file format")
        elif isinstance(data_source, pd.DataFrame):
            df = data_source
        else:
            raise ValueError("Data source must be DataFrame, CSV path, or Excel path")
        
        # Infer schema
        schema = self.infer_table_schema(df, table_name, version)
        
        # Detect drift
        drift_analysis = self.detect_and_analyze_drift(table_name, schema)
        
        # Generate comprehensive analysis
        analysis = {
            'table_name': table_name,
            'schema': asdict(schema),
            'drift_analysis': drift_analysis,
            'data_quality': self._assess_data_quality(df, schema),
            'recommendations': self._generate_recommendations(schema, drift_analysis)
        }
        
        return analysis
    
    def _assess_data_quality(self, df: pd.DataFrame, schema: TableSchema) -> Dict[str, Any]:
        """Assess data quality metrics"""
        return {
            'completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'uniqueness': df.nunique().to_dict(),
            'consistency': {col.name: col.confidence_score for col in schema.columns},
            'row_count': len(df),
            'column_count': len(df.columns)
        }
    
    def _generate_recommendations(self, schema: TableSchema, drift_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Low confidence columns
        low_confidence_cols = [col for col in schema.columns if col.confidence_score < 0.7]
        if low_confidence_cols:
            recommendations.append(f"Review data types for {len(low_confidence_cols)} columns with low confidence scores")
        
        # High impact changes
        if drift_analysis['has_drift']:
            high_impact = [c for c in drift_analysis['changes'] if c.get('impact_score', 0) > 0.5]
            if high_impact:
                recommendations.append(f"Plan migrations for {len(high_impact)} high-impact schema changes")
        
        # Data quality issues
        high_null_cols = [col for col in schema.columns if col.null_percentage > 0.5]
        if high_null_cols:
            recommendations.append(f"Address data quality issues in {len(high_null_cols)} columns with high null percentages")
        
        return recommendations

# Usage example and testing
async def main():
    """Example usage of the schema inference system"""
    
    # Initialize system
    db = VolunteerDatabase()
    manager = SchemaInferenceManager(db)
    await manager.initialize()
    
    # Example: Analyze volunteer data
    try:
        # Load sample data (assuming the Excel file exists)
        excel_path = "Y Volunteer Raw Data - Jan- August 2025.xlsx"
        analysis = await manager.analyze_data_source(excel_path, "volunteer_data", "v1.0")
        
        print("\n📊 SCHEMA ANALYSIS RESULTS:")
        print(f"Table: {analysis['table_name']}")
        print(f"Columns: {len(analysis['schema']['columns'])}")
        print(f"Rows: {analysis['schema']['row_count']}")
        
        if analysis['drift_analysis']['has_drift']:
            print(f"\n⚠️  SCHEMA DRIFT DETECTED:")
            print(analysis['drift_analysis']['summary'])
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
            
    except FileNotFoundError:
        print("📝 Example file not found - system ready for your data!")
        
        # Demo with sample data
        sample_data = pd.DataFrame({
            'id': range(100),
            'email': [f'user{i}@example.com' for i in range(100)],
            'age': np.random.randint(18, 65, 100),
            'is_member': np.random.choice([True, False], 100),
            'join_date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'hours': np.random.uniform(1, 10, 100)
        })
        
        analysis = await manager.analyze_data_source(sample_data, "sample_volunteers", "v1.0")
        print("\n📊 SAMPLE DATA ANALYSIS COMPLETE!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())