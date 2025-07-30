import os
import json
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service"""
        try:
            # Get service account credentials from environment variable
            creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not creds_json:
                logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables")
                return
            
            # Parse the JSON credentials
            service_account_info = json.loads(creds_json)
            
            # Create credentials
            creds = Credentials.from_service_account_info(
                service_account_info, 
                scopes=self.scopes
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets service initialized successfully")
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Google Sheets service is available"""
        return self.service is not None
    
    def get_spreadsheet_data(self, spreadsheet_id: str, range_name: str = 'Sheet1') -> Optional[List[List]]:
        """
        Read data from Google Sheets
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to read (e.g., 'Sheet1' or 'Sheet1!A1:Z1000')
        
        Returns:
            List of rows, where each row is a list of cell values
        """
        if not self.service:
            logger.error("Google Sheets service not initialized")
            return None
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Successfully read {len(values)} rows from spreadsheet")
            return values
            
        except HttpError as error:
            logger.error(f"HTTP error reading spreadsheet: {error}")
            return None
        except Exception as error:
            logger.error(f"Error reading spreadsheet: {error}")
            return None
    
    def write_to_spreadsheet(self, spreadsheet_id: str, range_name: str, values: List[List], 
                           value_input_option: str = 'RAW') -> bool:
        """
        Write data to Google Sheets
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to write to
            values: 2D array of values to write
            value_input_option: How to interpret input ('RAW' or 'USER_ENTERED')
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Google Sheets service not initialized")
            return False
        
        try:
            sheet = self.service.spreadsheets()
            body = {
                'values': values
            }
            
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"Successfully updated {updated_cells} cells")
            return True
            
        except HttpError as error:
            logger.error(f"HTTP error writing to spreadsheet: {error}")
            return False
        except Exception as error:
            logger.error(f"Error writing to spreadsheet: {error}")
            return False
    
    def append_to_spreadsheet(self, spreadsheet_id: str, range_name: str, values: List[List],
                            value_input_option: str = 'RAW') -> bool:
        """
        Append data to Google Sheets
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to append to
            values: 2D array of values to append
            value_input_option: How to interpret input ('RAW' or 'USER_ENTERED')
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Google Sheets service not initialized")
            return False
        
        try:
            sheet = self.service.spreadsheets()
            body = {
                'values': values
            }
            
            result = sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"Successfully appended {updated_cells} cells")
            return True
            
        except HttpError as error:
            logger.error(f"HTTP error appending to spreadsheet: {error}")
            return False
        except Exception as error:
            logger.error(f"Error appending to spreadsheet: {error}")
            return False
    
    def clear_spreadsheet_range(self, spreadsheet_id: str, range_name: str) -> bool:
        """
        Clear a range in Google Sheets
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to clear
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Google Sheets service not initialized")
            return False
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            logger.info(f"Successfully cleared range {range_name}")
            return True
            
        except HttpError as error:
            logger.error(f"HTTP error clearing spreadsheet: {error}")
            return False
        except Exception as error:
            logger.error(f"Error clearing spreadsheet: {error}")
            return False

# Global instance
sheets_service = GoogleSheetsService()