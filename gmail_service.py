import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        self.service = None

    def authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    def send_email(self, to_email, subject, body, from_email=None):
        if not self.service:
            self.authenticate()
        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        except HttpError:
            return None

    def send_html_email(self, to_email, subject, html_body, from_email=None):
        if not self.service:
            self.authenticate()
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        except HttpError:
            return None

    def get_user_info(self):
        if not self.service:
            self.authenticate()
        try:
            return self.service.users().getProfile(userId='me').execute()
        except HttpError:
            return None


def send_email(to_email, subject, body, from_email=None):
    gmail = GmailService()
    return gmail.send_email(to_email, subject, body, from_email)


def send_html_email(to_email, subject, html_body, from_email=None):
    gmail = GmailService()
    return gmail.send_html_email(to_email, subject, html_body, from_email)
