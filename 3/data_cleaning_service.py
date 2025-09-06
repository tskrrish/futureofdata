"""
AI-Powered Conversational Data Cleaning Service
Provides intelligent data cleaning through natural language conversations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
import re
from difflib import SequenceMatcher
from collections import Counter, defaultdict
import json
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import asyncio
import httpx


class ConversationalDataCleaner:
    """AI-powered conversational data cleaning system"""
    
    def __init__(self, ai_assistant=None):
        self.ai_assistant = ai_assistant
        self.data = None
        self.original_data = None
        self.cleaning_history = []
        self.suggested_fixes = []
        self.data_issues = {}
        self.cleaning_context = {}
        
    def load_data(self, data: Union[pd.DataFrame, str, dict]) -> bool:
        """Load data for cleaning - accepts DataFrame, file path, or dict"""
        try:
            if isinstance(data, pd.DataFrame):
                self.data = data.copy()
            elif isinstance(data, str):
                if data.endswith('.csv'):
                    self.data = pd.read_csv(data)
                elif data.endswith(('.xlsx', '.xls')):
                    self.data = pd.read_excel(data)
                else:
                    raise ValueError("Unsupported file format")
            elif isinstance(data, dict):
                self.data = pd.DataFrame(data)
            else:
                raise ValueError("Unsupported data type")
            
            self.original_data = self.data.copy()
            print(f"✅ Data loaded: {len(self.data)} rows, {len(self.data.columns)} columns")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    async def analyze_data_quality(self) -> Dict[str, Any]:
        """Analyze data quality and identify issues"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        print("🔍 Analyzing data quality...")
        
        issues = {
            "missing_values": self._detect_missing_values(),
            "duplicates": self._detect_duplicates(),
            "data_types": self._analyze_data_types(),
            "outliers": self._detect_outliers(),
            "inconsistencies": self._detect_inconsistencies(),
            "column_issues": self._analyze_columns()
        }
        
        # Generate AI insights about the issues
        if self.ai_assistant:
            ai_analysis = await self._get_ai_analysis(issues)
            issues["ai_insights"] = ai_analysis
        
        self.data_issues = issues
        return issues
    
    def _detect_missing_values(self) -> Dict[str, Any]:
        """Detect missing values and patterns"""
        missing_info = {}
        
        for col in self.data.columns:
            missing_count = self.data[col].isnull().sum()
            missing_pct = (missing_count / len(self.data)) * 100
            
            if missing_count > 0:
                missing_info[col] = {
                    "count": int(missing_count),
                    "percentage": round(missing_pct, 2),
                    "missing_patterns": self._analyze_missing_patterns(col)
                }
        
        return missing_info
    
    def _analyze_missing_patterns(self, column: str) -> Dict[str, Any]:
        """Analyze patterns in missing data"""
        mask = self.data[column].isnull()
        
        patterns = {
            "random": not mask.any() or mask.sum() < 3,
            "consecutive_groups": self._find_consecutive_missing(mask),
            "correlated_missing": self._find_correlated_missing(column)
        }
        
        return patterns
    
    def _find_consecutive_missing(self, mask: pd.Series) -> List[Tuple[int, int]]:
        """Find consecutive groups of missing values"""
        groups = []
        in_group = False
        start = None
        
        for i, is_missing in enumerate(mask):
            if is_missing and not in_group:
                start = i
                in_group = True
            elif not is_missing and in_group:
                groups.append((start, i - 1))
                in_group = False
        
        if in_group:
            groups.append((start, len(mask) - 1))
        
        return groups
    
    def _find_correlated_missing(self, column: str) -> Dict[str, float]:
        """Find columns with correlated missing patterns"""
        correlations = {}
        target_mask = self.data[column].isnull()
        
        for other_col in self.data.columns:
            if other_col != column:
                other_mask = self.data[other_col].isnull()
                if other_mask.sum() > 0:
                    # Calculate correlation between missing patterns
                    correlation = target_mask.corr(other_mask)
                    if abs(correlation) > 0.3:  # Threshold for significant correlation
                        correlations[other_col] = round(correlation, 3)
        
        return correlations
    
    def _detect_duplicates(self) -> Dict[str, Any]:
        """Detect various types of duplicates"""
        duplicate_info = {
            "exact_duplicates": {
                "count": self.data.duplicated().sum(),
                "rows": self.data[self.data.duplicated()].index.tolist()
            },
            "near_duplicates": self._find_near_duplicates(),
            "duplicate_columns": self._find_duplicate_columns()
        }
        
        return duplicate_info
    
    def _find_near_duplicates(self, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Find near-duplicate rows based on similarity"""
        near_dupes = []
        text_cols = self.data.select_dtypes(include=['object']).columns
        
        if len(text_cols) == 0:
            return near_dupes
        
        for i in range(len(self.data)):
            for j in range(i + 1, len(self.data)):
                similarity = self._calculate_row_similarity(i, j, text_cols)
                if similarity >= threshold:
                    near_dupes.append({
                        "row1": i,
                        "row2": j,
                        "similarity": round(similarity, 3)
                    })
        
        return near_dupes
    
    def _calculate_row_similarity(self, row1_idx: int, row2_idx: int, columns: List[str]) -> float:
        """Calculate similarity between two rows"""
        similarities = []
        
        for col in columns:
            val1 = str(self.data.iloc[row1_idx][col]) if pd.notna(self.data.iloc[row1_idx][col]) else ""
            val2 = str(self.data.iloc[row2_idx][col]) if pd.notna(self.data.iloc[row2_idx][col]) else ""
            
            if val1 == "" and val2 == "":
                similarities.append(1.0)
            elif val1 == "" or val2 == "":
                similarities.append(0.0)
            else:
                similarities.append(SequenceMatcher(None, val1.lower(), val2.lower()).ratio())
        
        return np.mean(similarities) if similarities else 0.0
    
    def _find_duplicate_columns(self) -> List[List[str]]:
        """Find columns with identical content"""
        duplicate_groups = []
        checked_cols = set()
        
        for col1 in self.data.columns:
            if col1 in checked_cols:
                continue
            
            group = [col1]
            for col2 in self.data.columns:
                if col2 != col1 and col2 not in checked_cols:
                    if self.data[col1].equals(self.data[col2]):
                        group.append(col2)
                        checked_cols.add(col2)
            
            if len(group) > 1:
                duplicate_groups.append(group)
            
            checked_cols.add(col1)
        
        return duplicate_groups
    
    def _analyze_data_types(self) -> Dict[str, Any]:
        """Analyze data types and suggest improvements"""
        type_issues = {}
        
        for col in self.data.columns:
            current_type = str(self.data[col].dtype)
            suggested_type = self._suggest_data_type(col)
            
            if suggested_type != current_type:
                type_issues[col] = {
                    "current": current_type,
                    "suggested": suggested_type,
                    "confidence": self._calculate_type_confidence(col, suggested_type)
                }
        
        return type_issues
    
    def _suggest_data_type(self, column: str) -> str:
        """Suggest optimal data type for a column"""
        col_data = self.data[column].dropna()
        
        if len(col_data) == 0:
            return str(self.data[column].dtype)
        
        # Check for datetime
        if self._looks_like_datetime(col_data):
            return "datetime64[ns]"
        
        # Check for boolean
        if self._looks_like_boolean(col_data):
            return "bool"
        
        # Check for categorical
        if self._looks_like_categorical(col_data):
            return "category"
        
        # Check for numeric
        if self._looks_like_numeric(col_data):
            if self._looks_like_integer(col_data):
                return "int64"
            else:
                return "float64"
        
        return "object"
    
    def _looks_like_datetime(self, series: pd.Series) -> bool:
        """Check if series looks like datetime"""
        sample = series.head(100)
        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{4}/\d{2}/\d{2}'
        ]
        
        matches = 0
        for value in sample.astype(str):
            for pattern in datetime_patterns:
                if re.search(pattern, value):
                    matches += 1
                    break
        
        return matches / len(sample) > 0.8
    
    def _looks_like_boolean(self, series: pd.Series) -> bool:
        """Check if series looks like boolean"""
        unique_vals = set(str(v).lower() for v in series.unique())
        boolean_patterns = [
            {'true', 'false'},
            {'yes', 'no'},
            {'y', 'n'},
            {'1', '0'},
            {'on', 'off'},
            {'active', 'inactive'}
        ]
        
        return any(unique_vals <= pattern for pattern in boolean_patterns)
    
    def _looks_like_categorical(self, series: pd.Series) -> bool:
        """Check if series should be categorical"""
        unique_ratio = len(series.unique()) / len(series)
        return unique_ratio < 0.5 and len(series.unique()) < 100
    
    def _looks_like_numeric(self, series: pd.Series) -> bool:
        """Check if series looks like numeric"""
        try:
            pd.to_numeric(series, errors='raise')
            return True
        except:
            # Check if most values are numeric
            numeric_count = 0
            for value in series:
                try:
                    float(str(value).replace(',', '').replace('$', '').replace('%', ''))
                    numeric_count += 1
                except:
                    pass
            
            return numeric_count / len(series) > 0.8
    
    def _looks_like_integer(self, series: pd.Series) -> bool:
        """Check if numeric series should be integer"""
        try:
            numeric_series = pd.to_numeric(series, errors='coerce')
            return (numeric_series == numeric_series.astype(int)).all()
        except:
            return False
    
    def _calculate_type_confidence(self, column: str, suggested_type: str) -> float:
        """Calculate confidence in suggested type conversion"""
        col_data = self.data[column].dropna()
        
        if len(col_data) == 0:
            return 0.0
        
        try:
            if suggested_type == "datetime64[ns]":
                pd.to_datetime(col_data, errors='raise')
            elif suggested_type == "bool":
                # Already checked in _looks_like_boolean
                pass
            elif suggested_type in ["int64", "float64"]:
                pd.to_numeric(col_data, errors='raise')
            
            return 0.9
        except:
            return 0.5
    
    def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers in numeric columns"""
        outlier_info = {}
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = self.data[col].dropna()
            if len(col_data) > 0:
                outliers = self._find_outliers(col_data)
                if len(outliers) > 0:
                    outlier_info[col] = {
                        "count": len(outliers),
                        "percentage": round((len(outliers) / len(col_data)) * 100, 2),
                        "indices": outliers.tolist(),
                        "values": col_data.iloc[outliers].tolist()
                    }
        
        return outlier_info
    
    def _find_outliers(self, series: pd.Series) -> np.ndarray:
        """Find outliers using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        return series[outlier_mask].index.to_numpy()
    
    def _detect_inconsistencies(self) -> Dict[str, Any]:
        """Detect data inconsistencies"""
        inconsistencies = {
            "format_inconsistencies": self._find_format_inconsistencies(),
            "case_inconsistencies": self._find_case_inconsistencies(),
            "encoding_issues": self._find_encoding_issues()
        }
        
        return inconsistencies
    
    def _find_format_inconsistencies(self) -> Dict[str, List[str]]:
        """Find format inconsistencies in text columns"""
        format_issues = {}
        text_cols = self.data.select_dtypes(include=['object']).columns
        
        for col in text_cols:
            patterns = self._analyze_text_patterns(col)
            if len(patterns) > 1:
                format_issues[col] = patterns
        
        return format_issues
    
    def _analyze_text_patterns(self, column: str) -> List[str]:
        """Analyze text patterns in a column"""
        patterns = set()
        col_data = self.data[column].dropna().astype(str)
        
        for value in col_data.head(100):  # Sample for performance
            # Create pattern by replacing digits/letters with placeholders
            pattern = re.sub(r'\d+', 'N', value)
            pattern = re.sub(r'[A-Za-z]+', 'A', pattern)
            patterns.add(pattern)
        
        return list(patterns)
    
    def _find_case_inconsistencies(self) -> Dict[str, Dict[str, int]]:
        """Find case inconsistencies"""
        case_issues = {}
        text_cols = self.data.select_dtypes(include=['object']).columns
        
        for col in text_cols:
            case_variants = defaultdict(list)
            col_data = self.data[col].dropna().astype(str)
            
            for value in col_data:
                key = value.lower().strip()
                case_variants[key].append(value)
            
            # Find keys with multiple case variants
            inconsistent = {k: len(v) for k, v in case_variants.items() if len(set(v)) > 1}
            
            if inconsistent:
                case_issues[col] = inconsistent
        
        return case_issues
    
    def _find_encoding_issues(self) -> List[str]:
        """Find potential encoding issues"""
        encoding_issues = []
        text_cols = self.data.select_dtypes(include=['object']).columns
        
        suspicious_chars = ['Ã', 'â€', 'Â', '�']
        
        for col in text_cols:
            col_data = self.data[col].dropna().astype(str)
            for value in col_data:
                if any(char in value for char in suspicious_chars):
                    encoding_issues.append(f"Column '{col}': potential encoding issue in value '{value}'")
                    break
        
        return encoding_issues
    
    def _analyze_columns(self) -> Dict[str, Any]:
        """Analyze column names and structure"""
        column_issues = {
            "naming_issues": self._find_naming_issues(),
            "empty_columns": self._find_empty_columns(),
            "single_value_columns": self._find_single_value_columns()
        }
        
        return column_issues
    
    def _find_naming_issues(self) -> Dict[str, List[str]]:
        """Find column naming issues"""
        issues = {
            "whitespace": [],
            "special_chars": [],
            "case_inconsistent": [],
            "too_long": []
        }
        
        for col in self.data.columns:
            if col != col.strip():
                issues["whitespace"].append(col)
            
            if re.search(r'[^\w\s]', col):
                issues["special_chars"].append(col)
            
            if len(col) > 50:
                issues["too_long"].append(col)
        
        # Check for case inconsistencies in similar column names
        col_lower = {col.lower(): col for col in self.data.columns}
        if len(col_lower) < len(self.data.columns):
            issues["case_inconsistent"] = [col for col in self.data.columns 
                                         if col.lower() in col_lower and col_lower[col.lower()] != col]
        
        return {k: v for k, v in issues.items() if v}
    
    def _find_empty_columns(self) -> List[str]:
        """Find completely empty columns"""
        return [col for col in self.data.columns if self.data[col].isnull().all()]
    
    def _find_single_value_columns(self) -> List[Tuple[str, Any]]:
        """Find columns with only one unique value"""
        single_value_cols = []
        
        for col in self.data.columns:
            unique_vals = self.data[col].dropna().unique()
            if len(unique_vals) == 1:
                single_value_cols.append((col, unique_vals[0]))
        
        return single_value_cols
    
    async def _get_ai_analysis(self, issues: Dict[str, Any]) -> Dict[str, str]:
        """Get AI analysis of data issues"""
        if not self.ai_assistant:
            return {}
        
        # Create a summary of issues for AI analysis
        issue_summary = self._create_issue_summary(issues)
        
        analysis_prompt = f"""Analyze these data quality issues and provide recommendations:

DATA OVERVIEW:
- Rows: {len(self.data)}
- Columns: {len(self.data.columns)}
- Column names: {list(self.data.columns)[:10]}...

IDENTIFIED ISSUES:
{issue_summary}

Please provide:
1. Priority ranking of issues (high/medium/low)
2. Recommended cleaning actions
3. Potential risks of each issue
4. Suggested automation opportunities

Be specific and actionable in your recommendations."""
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert data analyst providing actionable data cleaning recommendations."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.ai_assistant._call_inference_api(messages)
            
            if response:
                return {"analysis": response["content"], "success": True}
            else:
                return {"analysis": "AI analysis temporarily unavailable", "success": False}
                
        except Exception as e:
            print(f"Error getting AI analysis: {e}")
            return {"analysis": f"Error in AI analysis: {str(e)}", "success": False}
    
    def _create_issue_summary(self, issues: Dict[str, Any]) -> str:
        """Create a concise summary of issues for AI analysis"""
        summary_lines = []
        
        # Missing values
        missing = issues.get("missing_values", {})
        if missing:
            summary_lines.append(f"Missing values in {len(missing)} columns")
            for col, info in list(missing.items())[:3]:
                summary_lines.append(f"  - {col}: {info['percentage']}% missing")
        
        # Duplicates
        duplicates = issues.get("duplicates", {})
        exact_dupes = duplicates.get("exact_duplicates", {}).get("count", 0)
        if exact_dupes > 0:
            summary_lines.append(f"Exact duplicates: {exact_dupes} rows")
        
        # Data types
        type_issues = issues.get("data_types", {})
        if type_issues:
            summary_lines.append(f"Data type issues in {len(type_issues)} columns")
        
        # Outliers
        outliers = issues.get("outliers", {})
        if outliers:
            total_outliers = sum(info["count"] for info in outliers.values())
            summary_lines.append(f"Outliers: {total_outliers} values across {len(outliers)} columns")
        
        return "\n".join(summary_lines) if summary_lines else "No major issues detected"
    
    async def chat_about_cleaning(self, user_message: str) -> Dict[str, Any]:
        """Handle conversational data cleaning requests"""
        if not self.ai_assistant:
            return {"error": "AI assistant not available"}
        
        # Prepare context about current data state
        context = self._prepare_cleaning_context()
        
        # Create specialized prompt for data cleaning
        system_prompt = f"""You are a data cleaning assistant helping users clean their dataset through conversation.

CURRENT DATA STATE:
{context}

Your role:
1. Understand cleaning requests in natural language
2. Suggest specific cleaning actions
3. Explain the impact of proposed changes
4. Guide users through the cleaning process
5. Ask clarifying questions when needed

Be helpful, clear, and specific about what cleaning actions you recommend."""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.ai_assistant._call_inference_api(messages)
            
            if response:
                # Parse response for actionable cleaning commands
                cleaning_actions = self._extract_cleaning_actions(response["content"])
                
                return {
                    "response": response["content"],
                    "suggested_actions": cleaning_actions,
                    "success": True
                }
            else:
                return {
                    "response": "I'm having trouble processing your request right now. Could you try rephrasing your cleaning request?",
                    "success": False
                }
                
        except Exception as e:
            return {
                "response": f"Error processing your request: {str(e)}",
                "success": False
            }
    
    def _prepare_cleaning_context(self) -> str:
        """Prepare context about current data state for AI"""
        if self.data is None:
            return "No data loaded"
        
        context_lines = [
            f"Dataset: {len(self.data)} rows × {len(self.data.columns)} columns",
            f"Columns: {', '.join(self.data.columns[:5])}{'...' if len(self.data.columns) > 5 else ''}",
        ]
        
        # Add issue summary if available
        if self.data_issues:
            missing = self.data_issues.get("missing_values", {})
            if missing:
                context_lines.append(f"Missing values in {len(missing)} columns")
            
            duplicates = self.data_issues.get("duplicates", {}).get("exact_duplicates", {}).get("count", 0)
            if duplicates > 0:
                context_lines.append(f"{duplicates} duplicate rows found")
        
        return "\n".join(context_lines)
    
    def _extract_cleaning_actions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract actionable cleaning commands from AI response"""
        actions = []
        
        # Look for common cleaning action patterns
        action_patterns = {
            "remove_duplicates": r"remove.*duplicate",
            "fill_missing": r"fill.*missing|impute.*values",
            "fix_types": r"convert.*type|change.*datatype",
            "standardize": r"standardize|normalize",
            "remove_outliers": r"remove.*outlier"
        }
        
        response_lower = ai_response.lower()
        
        for action_type, pattern in action_patterns.items():
            if re.search(pattern, response_lower):
                actions.append({
                    "type": action_type,
                    "confidence": 0.8,
                    "suggested": True
                })
        
        return actions
    
    def apply_cleaning_action(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific cleaning action to the data"""
        if self.data is None:
            return {"error": "No data loaded"}
        
        try:
            original_shape = self.data.shape
            
            if action_type == "remove_duplicates":
                result = self._remove_duplicates(parameters)
            elif action_type == "fill_missing":
                result = self._fill_missing_values(parameters)
            elif action_type == "fix_types":
                result = self._fix_data_types(parameters)
            elif action_type == "remove_outliers":
                result = self._remove_outliers(parameters)
            elif action_type == "standardize_text":
                result = self._standardize_text(parameters)
            elif action_type == "merge_duplicates":
                result = self._merge_duplicate_records(parameters)
            else:
                return {"error": f"Unknown action type: {action_type}"}
            
            # Record the change
            self.cleaning_history.append({
                "action": action_type,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat(),
                "before_shape": original_shape,
                "after_shape": self.data.shape,
                "result": result
            })
            
            return result
            
        except Exception as e:
            return {"error": f"Error applying {action_type}: {str(e)}"}
    
    def _remove_duplicates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove duplicate rows"""
        subset = params.get("columns", None)
        keep = params.get("keep", "first")
        
        before_count = len(self.data)
        self.data = self.data.drop_duplicates(subset=subset, keep=keep)
        after_count = len(self.data)
        
        removed = before_count - after_count
        
        return {
            "success": True,
            "message": f"Removed {removed} duplicate rows",
            "details": {
                "rows_before": before_count,
                "rows_after": after_count,
                "rows_removed": removed
            }
        }
    
    def _fill_missing_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing values"""
        column = params.get("column")
        method = params.get("method", "mean")  # mean, median, mode, forward_fill, backward_fill, constant
        value = params.get("value", None)
        
        if column not in self.data.columns:
            return {"error": f"Column '{column}' not found"}
        
        before_missing = self.data[column].isnull().sum()
        
        if method == "constant" and value is not None:
            self.data[column] = self.data[column].fillna(value)
        elif method == "mean" and self.data[column].dtype in ['int64', 'float64']:
            self.data[column] = self.data[column].fillna(self.data[column].mean())
        elif method == "median" and self.data[column].dtype in ['int64', 'float64']:
            self.data[column] = self.data[column].fillna(self.data[column].median())
        elif method == "mode":
            mode_val = self.data[column].mode().iloc[0] if not self.data[column].mode().empty else None
            if mode_val is not None:
                self.data[column] = self.data[column].fillna(mode_val)
        elif method == "forward_fill":
            self.data[column] = self.data[column].fillna(method='ffill')
        elif method == "backward_fill":
            self.data[column] = self.data[column].fillna(method='bfill')
        else:
            return {"error": f"Invalid fill method: {method}"}
        
        after_missing = self.data[column].isnull().sum()
        filled = before_missing - after_missing
        
        return {
            "success": True,
            "message": f"Filled {filled} missing values in column '{column}' using {method}",
            "details": {
                "missing_before": int(before_missing),
                "missing_after": int(after_missing),
                "values_filled": int(filled)
            }
        }
    
    def _fix_data_types(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix data types"""
        column = params.get("column")
        target_type = params.get("target_type")
        
        if column not in self.data.columns:
            return {"error": f"Column '{column}' not found"}
        
        original_type = str(self.data[column].dtype)
        
        try:
            if target_type == "datetime":
                self.data[column] = pd.to_datetime(self.data[column], errors='coerce')
            elif target_type == "numeric":
                self.data[column] = pd.to_numeric(self.data[column], errors='coerce')
            elif target_type == "category":
                self.data[column] = self.data[column].astype('category')
            elif target_type == "string":
                self.data[column] = self.data[column].astype('string')
            else:
                self.data[column] = self.data[column].astype(target_type)
            
            return {
                "success": True,
                "message": f"Converted column '{column}' from {original_type} to {target_type}",
                "details": {
                    "original_type": original_type,
                    "new_type": str(self.data[column].dtype)
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to convert column '{column}' to {target_type}: {str(e)}"}
    
    def _remove_outliers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove outliers from numeric columns"""
        column = params.get("column")
        method = params.get("method", "iqr")  # iqr, zscore, isolation_forest
        threshold = params.get("threshold", 1.5)
        
        if column not in self.data.columns:
            return {"error": f"Column '{column}' not found"}
        
        if self.data[column].dtype not in ['int64', 'float64']:
            return {"error": f"Column '{column}' is not numeric"}
        
        before_count = len(self.data)
        
        if method == "iqr":
            Q1 = self.data[column].quantile(0.25)
            Q3 = self.data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            self.data = self.data[
                (self.data[column] >= lower_bound) & 
                (self.data[column] <= upper_bound)
            ]
        
        after_count = len(self.data)
        removed = before_count - after_count
        
        return {
            "success": True,
            "message": f"Removed {removed} outliers from column '{column}' using {method} method",
            "details": {
                "rows_before": before_count,
                "rows_after": after_count,
                "outliers_removed": removed
            }
        }
    
    def _standardize_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize text in specified columns"""
        column = params.get("column")
        operations = params.get("operations", ["strip", "lower"])
        
        if column not in self.data.columns:
            return {"error": f"Column '{column}' not found"}
        
        changes = 0
        original_values = self.data[column].copy()
        
        for operation in operations:
            if operation == "strip":
                self.data[column] = self.data[column].astype(str).str.strip()
            elif operation == "lower":
                self.data[column] = self.data[column].astype(str).str.lower()
            elif operation == "upper":
                self.data[column] = self.data[column].astype(str).str.upper()
            elif operation == "title":
                self.data[column] = self.data[column].astype(str).str.title()
        
        changes = (original_values != self.data[column]).sum()
        
        return {
            "success": True,
            "message": f"Standardized {changes} values in column '{column}'",
            "details": {
                "operations": operations,
                "values_changed": int(changes)
            }
        }
    
    def _merge_duplicate_records(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge duplicate records by combining their information"""
        key_columns = params.get("key_columns", [])
        merge_strategy = params.get("strategy", "first")  # first, last, combine, most_complete
        
        if not key_columns:
            return {"error": "No key columns specified for merging"}
        
        before_count = len(self.data)
        
        # Group by key columns and merge duplicates
        if merge_strategy == "most_complete":
            # Choose record with most non-null values
            def most_complete_record(group):
                return group.loc[group.isnull().sum(axis=1).idxmin()]
            
            self.data = self.data.groupby(key_columns).apply(most_complete_record).reset_index(drop=True)
        elif merge_strategy == "combine":
            # Combine non-null values from all records
            def combine_records(group):
                combined = {}
                for col in group.columns:
                    non_null_values = group[col].dropna().unique()
                    if len(non_null_values) == 1:
                        combined[col] = non_null_values[0]
                    elif len(non_null_values) > 1:
                        # For text columns, join values
                        if group[col].dtype == 'object':
                            combined[col] = ' | '.join(str(v) for v in non_null_values)
                        else:
                            # For numeric columns, take the first non-null value
                            combined[col] = non_null_values[0]
                    else:
                        combined[col] = None
                return pd.Series(combined)
            
            self.data = self.data.groupby(key_columns).apply(combine_records).reset_index()
        else:
            # Simple deduplication
            self.data = self.data.drop_duplicates(subset=key_columns, keep=merge_strategy)
        
        after_count = len(self.data)
        merged = before_count - after_count
        
        return {
            "success": True,
            "message": f"Merged {merged} duplicate records using {merge_strategy} strategy",
            "details": {
                "records_before": before_count,
                "records_after": after_count,
                "records_merged": merged,
                "key_columns": key_columns
            }
        }
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Get summary of all cleaning operations performed"""
        return {
            "original_shape": self.original_data.shape if self.original_data is not None else None,
            "current_shape": self.data.shape if self.data is not None else None,
            "cleaning_history": self.cleaning_history,
            "total_operations": len(self.cleaning_history)
        }
    
    def export_cleaned_data(self, file_path: str, include_history: bool = True) -> bool:
        """Export cleaned data to file"""
        if self.data is None:
            return False
        
        try:
            if file_path.endswith('.csv'):
                self.data.to_csv(file_path, index=False)
            elif file_path.endswith(('.xlsx', '.xls')):
                with pd.ExcelWriter(file_path) as writer:
                    self.data.to_excel(writer, sheet_name='Cleaned_Data', index=False)
                    
                    if include_history:
                        history_df = pd.DataFrame(self.cleaning_history)
                        history_df.to_excel(writer, sheet_name='Cleaning_History', index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False


# Example usage
async def demo_conversational_cleaning():
    """Demonstrate conversational data cleaning"""
    # Create sample data with issues
    sample_data = pd.DataFrame({
        'Name': ['John Doe', 'jane smith', 'JOHN DOE', 'Jane Smith', None],
        'Email': ['john@email.com', 'jane@email.com', 'john@email.com', None, 'invalid'],
        'Age': [25, 30, 25, 30, 150],  # 150 is an outlier
        'Salary': ['50000', '60,000', '$70000', '80000', None]
    })
    
    # Initialize cleaner
    cleaner = ConversationalDataCleaner()
    cleaner.load_data(sample_data)
    
    # Analyze data quality
    issues = await cleaner.analyze_data_quality()
    print("Data Quality Issues:", json.dumps(issues, indent=2, default=str))
    
    # Simulate conversational cleaning
    responses = [
        "I want to remove duplicate names",
        "Fill missing emails with 'unknown@email.com'",
        "Fix the salary column to be numeric",
        "Standardize the name column to title case"
    ]
    
    for request in responses:
        response = await cleaner.chat_about_cleaning(request)
        print(f"\nUser: {request}")
        print(f"Assistant: {response.get('response', 'No response')}")


if __name__ == "__main__":
    asyncio.run(demo_conversational_cleaning())