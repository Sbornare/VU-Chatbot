import pandas as pd
import json
import logging
from typing import List, Dict, Any, Optional
from backend.database import mongo_db, get_next_sequence
from datetime import datetime

logger = logging.getLogger(__name__)


class PlacementDataIngestion:
    """Handle Excel file ingestion for placement data - adapts to any format"""
    
    def __init__(self):
        self.db = mongo_db
        
        # Flexible column mappings - will detect automatically
        self.column_mappings = {
            'student_name': ['student_name', 'name', 'student name', 'full name', 'student', 'candidate name', 'candidate'],
            'email': ['email', 'student_email', 'student email', 'mail', 'e-mail', 'email id'],
            'student_id': ['student_id', 'id', 'student id', 'roll no', 'roll number', 'registration no'],
            'program': ['program', 'course', 'degree', 'branch', 'stream', 'specialization', 'department'],
            'graduation_year': ['graduation_year', 'year', 'passing year', 'batch', 'graduation', 'pass year'],
            'cgpa': ['cgpa', 'gpa', 'percentage', 'marks', 'score', 'grade'],
            'company_name': ['company_name', 'company', 'organization', 'employer', 'firm', 'corp'],
            'job_title': ['job_title', 'position', 'role', 'designation', 'post', 'job role', 'title'],
            'package': ['package', 'salary', 'ctc', 'compensation', 'pay', 'income', 'lpa'],
            'job_location': ['job_location', 'location', 'place', 'city', 'work location'],
            'selection_date': ['selection_date', 'date', 'joining date', 'offer date', 'selected on'],
            'selection_process': ['selection_process', 'process', 'rounds', 'interview process'],
            'industry': ['industry', 'sector', 'domain', 'field'],
            'website': ['website', 'url', 'site', 'web'],
            'hr_contact': ['hr_contact', 'hr', 'contact person', 'recruiter'],
            'hr_email': ['hr_email', 'hr email', 'contact email', 'recruiter email']
        }
    
    def detect_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """Automatically detect column mappings based on column names"""
        columns = [col.lower().strip() for col in df.columns]
        detected = {}
        
        for field, possible_names in self.column_mappings.items():
            for col in columns:
                for possible in possible_names:
                    if possible.lower() in col or col in possible.lower():
                        # Get original column name (not lowercase)
                        original_col = df.columns[columns.index(col)]
                        detected[field] = original_col
                        break
                if field in detected:
                    break
        
        return detected
    
    def process_placement_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Process Excel file containing placement data - adapts to any format
        """
        try:
            # Read Excel file - detect all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            results = {
                'companies_added': 0,
                'placements_added': 0,
                'jobs_added': 0,
                'errors': [],
                'detected_format': {}
            }
            
            # Process each sheet and detect its purpose
            for sheet_name, df in excel_data.items():
                logger.info(f"Processing sheet: {sheet_name}")
                
                # Clean column names
                df.columns = df.columns.astype(str).str.strip()
                
                # Detect column mapping
                mapping = self.detect_column_mapping(df)
                results['detected_format'][sheet_name] = {
                    'columns': list(df.columns),
                    'detected_fields': mapping,
                    'rows': len(df)
                }
                
                # Determine sheet type and process accordingly
                if self._is_student_sheet(mapping, df):
                    results['placements_added'] += self._process_flexible_placements(df, mapping)
                elif self._is_company_sheet(mapping, df):
                    results['companies_added'] += self._process_flexible_companies(df, mapping)
                else:
                    # Try to process as general data
                    placements_added = self._process_flexible_placements(df, mapping)
                    if placements_added > 0:
                        results['placements_added'] += placements_added
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing placement Excel: {e}")
            return {'error': str(e)}
    
    def _is_student_sheet(self, mapping: Dict[str, str], df: pd.DataFrame) -> bool:
        """Determine if sheet contains student placement data"""
        student_indicators = ['student_name', 'company_name', 'package', 'job_title']
        return sum(1 for indicator in student_indicators if indicator in mapping) >= 2
    
    def _is_company_sheet(self, mapping: Dict[str, str], df: pd.DataFrame) -> bool:
        """Determine if sheet contains company data"""
        company_indicators = ['company_name', 'industry', 'website']
        return sum(1 for indicator in company_indicators if indicator in mapping) >= 2 and 'student_name' not in mapping
    
    def _process_flexible_companies(self, df: pd.DataFrame, mapping: Dict[str, str]) -> int:
        """Process companies with flexible column mapping"""
        count = 0
        
        for _, row in df.iterrows():
            try:
                company_name = self._get_value(row, mapping, 'company_name')
                if not company_name:
                    continue
                
                # Check if company already exists
                existing = self.db.companies.find_one({"name": company_name})
                if existing:
                    continue
                
                company = {
                    "id": get_next_sequence("companies"),
                    "name": company_name,
                    "industry": self._get_value(row, mapping, 'industry') or '',
                    "location": self._get_value(row, mapping, 'job_location') or '',
                    "website": self._get_value(row, mapping, 'website'),
                    "hr_contact": self._get_value(row, mapping, 'hr_contact'),
                    "hr_email": self._get_value(row, mapping, 'hr_email'),
                    "created_at": datetime.utcnow(),
                }

                self.db.companies.insert_one(company)
                count += 1
                
            except Exception as e:
                logger.error(f"Error processing company row: {e}")

        return count
    
    def _process_flexible_placements(self, df: pd.DataFrame, mapping: Dict[str, str]) -> int:
        """Process student placements with flexible column mapping"""
        count = 0
        
        for _, row in df.iterrows():
            try:
                student_name = self._get_value(row, mapping, 'student_name')
                company_name = self._get_value(row, mapping, 'company_name')
                
                if not student_name and not company_name:
                    continue
                
                # Get or create company
                company = None
                if company_name:
                    company = self.db.companies.find_one({"name": company_name})
                    if not company:
                        company = {
                            "id": get_next_sequence("companies"),
                            "name": company_name,
                            "created_at": datetime.utcnow(),
                        }
                        self.db.companies.insert_one(company)
                
                # Create placement record
                placement = {
                    "id": get_next_sequence("placements"),
                    "student_name": student_name or 'Unknown',
                    "student_email": self._get_value(row, mapping, 'email'),
                    "student_id": str(self._get_value(row, mapping, 'student_id') or ''),
                    "program": self._get_value(row, mapping, 'program') or '',
                    "graduation_year": self._safe_int(self._get_value(row, mapping, 'graduation_year')),
                    "cgpa": self._safe_float(self._get_value(row, mapping, 'cgpa')),
                    "company_id": company.get("id") if company else None,
                    "job_title": self._get_value(row, mapping, 'job_title') or '',
                    "package": self._safe_float(self._get_value(row, mapping, 'package')),
                    "job_location": self._get_value(row, mapping, 'job_location') or '',
                    "selection_rounds": self._get_value(row, mapping, 'selection_process'),
                    "selection_date": self._safe_date(self._get_value(row, mapping, 'selection_date')),
                    "created_at": datetime.utcnow(),
                }

                self.db.placements.insert_one(placement)
                count += 1
                
            except Exception as e:
                logger.error(f"Error processing placement row: {e}")

        return count
    
    def _get_value(self, row, mapping: Dict[str, str], field: str):
        """Get value from row using flexible mapping"""
        if field in mapping and mapping[field] in row.index:
            value = row[mapping[field]]
            if pd.isna(value) or value == '':
                return None
            return str(value).strip()
        return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if not value or pd.isna(value) or value == '':
            return None
        try:
            # Handle cases like "12.5 LPA", "₹12,50,000", etc.
            value_str = str(value).replace(',', '').replace('₹', '').replace('LPA', '').replace('lpa', '').strip()
            return float(value_str)
        except:
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if not value or pd.isna(value) or value == '':
            return None
        try:
            return int(float(str(value)))
        except:
            return None
    
    def _safe_date(self, value) -> Optional[datetime]:
        """Safely convert value to datetime"""
        if not value or pd.isna(value) or value == '':
            return None
        try:
            if isinstance(value, str):
                # Try multiple date formats
                formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except:
                        continue
            return value if isinstance(value, datetime) else None
        except:
            return None


# Convenience function
def ingest_placement_data(file_path: str) -> Dict[str, Any]:
    """Ingest placement data from Excel file with any format"""
    ingestion = PlacementDataIngestion()
    return ingestion.process_placement_excel(file_path)