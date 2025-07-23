import json
import base64
import email
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.services.memory_service import UniversalMemoryService
import logging

logger = logging.getLogger(__name__)

class GoogleWorkspaceService:
    """
    Comprehensive Google Workspace integration for Gmail, Calendar, Drive, and Meet.
    Provides deep automation and intelligent processing of Google services.
    """
    
    def __init__(self, credentials: Credentials = None, memory_service: UniversalMemoryService = None):
        self.credentials = credentials
        self.memory_service = memory_service
        self._services = {}
        
        if credentials:
            self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google API services with error handling"""
        try:
            self._services['gmail'] = build('gmail', 'v1', credentials=self.credentials)
            self._services['calendar'] = build('calendar', 'v3', credentials=self.credentials)
            self._services['drive'] = build('drive', 'v3', credentials=self.credentials)
            logger.info("Google Workspace services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Google services: {e}")
    
    def refresh_credentials_if_needed(self):
        """Refresh credentials if they're expired"""
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self._initialize_services()
                logger.info("Google credentials refreshed successfully")
                return True
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                return False
        return True
    
    # Gmail Integration Methods
    
    def get_recent_emails(self, max_results: int = 50, query: str = None, user_id: int = 1) -> List[Dict]:
        """Retrieve recent emails with intelligent filtering and analysis"""
        
        if not self._services.get('gmail'):
            return []
        
        try:
            # Build query for relevant emails
            search_query = query or 'is:unread OR newer_than:7d'
            
            results = self._services['gmail'].users().messages().list(
                userId='me', 
                maxResults=max_results,
                q=search_query
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages[:20]:  # Limit to prevent API quota issues
                try:
                    email_data = self._services['gmail'].users().messages().get(
                        userId='me', 
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    parsed_email = self._parse_email(email_data)
                    if parsed_email:
                        emails.append(parsed_email)
                        
                        # Store email content in memory for context
                        if self.memory_service:
                            self.memory_service.add_memory(
                                content=f"Email from {parsed_email.get('from', '')}: {parsed_email.get('subject', '')}",
                                memory_type='user',
                                category='email',
                                tags=['email', 'gmail', parsed_email.get('from', '').split('@')[1] if '@' in parsed_email.get('from', '') else 'unknown'],
                                source_platform='gmail',
                                user_id=user_id
                            )
                        
                except Exception as e:
                    logger.warning(f"Error processing email {message['id']}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(emails)} emails from Gmail")
            return emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return []
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = None, bcc: str = None, html_body: str = None,
                   user_id: int = 1) -> Dict:
        """Send email through Gmail API with tracking"""
        
        if not self._services.get('gmail'):
            return {'success': False, 'error': 'Gmail service not available'}
        
        try:
            message = self._create_message(to, subject, body, cc, bcc, html_body)
            
            sent_message = self._services['gmail'].users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            # Store sent email in memory
            if self.memory_service:
                self.memory_service.add_memory(
                    content=f"Sent email to {to}: {subject}",
                    memory_type='user',
                    category='email_sent',
                    tags=['email', 'sent', to.split('@')[1] if '@' in to else 'unknown'],
                    source_platform='gmail',
                    user_id=user_id
                )
            
            logger.info(f"Email sent successfully to {to}")
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId')
            }
            
        except HttpError as e:
            logger.error(f"Error sending email: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_email_thread(self, thread_id: str) -> List[Dict]:
        """Get complete email thread for context analysis"""
        
        if not self._services.get('gmail'):
            return []
        
        try:
            thread = self._services['gmail'].users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            emails = []
            for message in thread.get('messages', []):
                parsed_email = self._parse_email(message)
                if parsed_email:
                    emails.append(parsed_email)
            
            return emails
            
        except HttpError as e:
            logger.error(f"Error getting email thread: {e}")
            return []
    
    # Calendar Integration Methods
    
    def create_calendar_event(self, title: str, start_time: str, end_time: str,
                             attendees: List[str] = None, description: str = None,
                             location: str = None, user_id: int = 1) -> Dict:
        """Create calendar event with automatic Google Meet integration"""
        
        if not self._services.get('calendar'):
            return {'success': False, 'error': 'Calendar service not available'}
        
        event = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{int(time.time())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 30},       # 30 minutes before
                ],
            }
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        try:
            created_event = self._services['calendar'].events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            # Store event in memory
            if self.memory_service:
                self.memory_service.add_memory(
                    content=f"Created calendar event: {title} with {len(attendees or [])} attendees",
                    memory_type='user',
                    category='calendar',
                    tags=['calendar', 'meeting', 'created'],
                    source_platform='google_calendar',
                    user_id=user_id
                )
            
            logger.info(f"Calendar event created: {title}")
            return {
                'success': True,
                'event_id': created_event['id'],
                'meeting_link': self._extract_meet_link(created_event),
                'event_link': created_event.get('htmlLink'),
                'calendar_link': created_event.get('htmlLink')
            }
            
        except HttpError as e:
            logger.error(f"Error creating calendar event: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_upcoming_events(self, max_results: int = 20, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming calendar events for scheduling intelligence"""
        
        if not self._services.get('calendar'):
            return []
        
        try:
            now = datetime.utcnow()
            time_max = now + timedelta(days=days_ahead)
            
            events_result = self._services['calendar'].events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            parsed_events = []
            
            for event in events:
                parsed_event = self._parse_calendar_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)
            
            logger.info(f"Retrieved {len(parsed_events)} upcoming events")
            return parsed_events
            
        except HttpError as e:
            logger.error(f"Error getting calendar events: {e}")
            return []
    
    def find_available_slots(self, duration_minutes: int = 60, days_ahead: int = 14,
                           working_hours: tuple = (9, 17)) -> List[Dict]:
        """Find available time slots for intelligent scheduling"""
        
        events = self.get_upcoming_events(days_ahead=days_ahead)
        
        # Create availability analysis
        available_slots = []
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_offset in range(days_ahead):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends (optional - can be configured)
            if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            # Find busy periods for this day
            busy_periods = []
            for event in events:
                event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
                
                if event_start.date() == current_date.date():
                    busy_periods.append((event_start.hour, event_end.hour))
            
            # Find available slots
            for hour in range(working_hours[0], working_hours[1]):
                slot_start = current_date.replace(hour=hour)
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Check if slot conflicts with busy periods
                is_available = True
                for busy_start, busy_end in busy_periods:
                    if (hour >= busy_start and hour < busy_end) or \
                       (slot_end.hour > busy_start and slot_end.hour <= busy_end):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start_time': slot_start.isoformat(),
                        'end_time': slot_end.isoformat(),
                        'duration_minutes': duration_minutes,
                        'date': current_date.date().isoformat(),
                        'day_of_week': current_date.strftime('%A')
                    })
        
        return available_slots[:20]  # Return top 20 slots
    
    # Drive Integration Methods
    
    def create_shared_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict:
        """Create shared folder for deal/project documents"""
        
        if not self._services.get('drive'):
            return {'success': False, 'error': 'Drive service not available'}
        
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            folder = self._services['drive'].files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Make folder shareable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self._services['drive'].permissions().create(
                fileId=folder['id'],
                body=permission
            ).execute()
            
            logger.info(f"Created shared folder: {folder_name}")
            return {
                'success': True,
                'folder_id': folder['id'],
                'folder_name': folder['name'],
                'web_link': folder['webViewLink']
            }
            
        except HttpError as e:
            logger.error(f"Error creating Drive folder: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_document(self, file_path: str, folder_id: str = None, 
                       share_with: List[str] = None) -> Dict:
        """Upload document to Drive with sharing"""
        
        if not self._services.get('drive'):
            return {'success': False, 'error': 'Drive service not available'}
        
        try:
            import os
            from googleapiclient.http import MediaFileUpload
            
            file_name = os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self._services['drive'].files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            # Share with specific users if provided
            if share_with:
                for email in share_with:
                    permission = {
                        'type': 'user',
                        'role': 'reader',
                        'emailAddress': email
                    }
                    
                    self._services['drive'].permissions().create(
                        fileId=file['id'],
                        body=permission,
                        sendNotificationEmail=True
                    ).execute()
            
            logger.info(f"Uploaded document: {file_name}")
            return {
                'success': True,
                'file_id': file['id'],
                'file_name': file['name'],
                'web_link': file['webViewLink']
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {'success': False, 'error': str(e)}
    
    # Utility Methods
    
    def _parse_email(self, email_data: Dict) -> Optional[Dict]:
        """Parse Gmail API email data into structured format"""
        
        try:
            headers = email_data['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Extract body with better handling
            body = self._extract_email_body(email_data['payload'])
            
            return {
                'id': email_data['id'],
                'thread_id': email_data['threadId'],
                'subject': header_dict.get('Subject', ''),
                'from': header_dict.get('From', ''),
                'to': header_dict.get('To', ''),
                'cc': header_dict.get('Cc', ''),
                'date': header_dict.get('Date', ''),
                'body': body,
                'labels': email_data.get('labelIds', []),
                'snippet': email_data.get('snippet', ''),
                'is_unread': 'UNREAD' in email_data.get('labelIds', []),
                'importance': self._assess_email_importance(header_dict, body)
            }
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from Gmail API payload with better handling"""
        
        body = ""
        
        def extract_text_from_part(part):
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Simple HTML to text conversion
                    import re
                    text = re.sub('<[^<]+?>', '', html_content)
                    return text
            return ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') in ['text/plain', 'text/html']:
                    text = extract_text_from_part(part)
                    if text:
                        body = text
                        break
                elif 'parts' in part:  # Nested parts
                    for nested_part in part['parts']:
                        text = extract_text_from_part(nested_part)
                        if text:
                            body = text
                            break
        else:
            body = extract_text_from_part(payload)
        
        return body.strip()
    
    def _create_message(self, to: str, subject: str, body: str, 
                       cc: str = None, bcc: str = None, html_body: str = None) -> Dict:
        """Create email message for Gmail API"""
        
        import email.mime.text
        import email.mime.multipart
        
        if html_body:
            message = email.mime.multipart.MIMEMultipart('alternative')
            text_part = email.mime.text.MIMEText(body, 'plain')
            html_part = email.mime.text.MIMEText(html_body, 'html')
            message.attach(text_part)
            message.attach(html_part)
        else:
            message = email.mime.text.MIMEText(body)
        
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}
    
    def _parse_calendar_event(self, event: Dict) -> Optional[Dict]:
        """Parse Google Calendar event data"""
        
        try:
            start = event.get('start', {})
            end = event.get('end', {})
            
            return {
                'id': event['id'],
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start_time': start.get('dateTime', start.get('date', '')),
                'end_time': end.get('dateTime', end.get('date', '')),
                'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                'meeting_link': self._extract_meet_link(event),
                'event_link': event.get('htmlLink', ''),
                'status': event.get('status', 'confirmed')
            }
            
        except Exception as e:
            logger.error(f"Error parsing calendar event: {e}")
            return None
    
    def _extract_meet_link(self, event: Dict) -> str:
        """Extract Google Meet link from calendar event"""
        
        conference_data = event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        
        for entry_point in entry_points:
            if entry_point.get('entryPointType') == 'video':
                return entry_point.get('uri', '')
        
        return ''
    
    def _assess_email_importance(self, headers: Dict, body: str) -> str:
        """Assess email importance based on content and headers"""
        
        # Check for high importance markers
        importance = headers.get('X-Priority', '3')
        if importance in ['1', '2']:
            return 'high'
        
        # Check for urgent keywords
        urgent_keywords = ['urgent', 'asap', 'emergency', 'critical', 'immediate']
        content = (headers.get('Subject', '') + ' ' + body).lower()
        
        if any(keyword in content for keyword in urgent_keywords):
            return 'high'
        
        # Check for meeting requests
        meeting_keywords = ['meeting', 'call', 'schedule', 'appointment']
        if any(keyword in content for keyword in meeting_keywords):
            return 'medium'
        
        return 'normal'
    
    @staticmethod
    def create_oauth_flow(client_config: Dict, scopes: List[str], redirect_uri: str) -> Flow:
        """Create OAuth flow for Google authentication"""
        
        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        return flow
    
    @staticmethod
    def get_required_scopes() -> List[str]:
        """Get required OAuth scopes for full functionality"""
        
        return [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
