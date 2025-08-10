#!/usr/bin/env python3
"""
Test script for Gmail service
Make sure you have credentials.json in the same directory
"""

from gmail_service import GmailService, send_email, send_html_email

def test_gmail_service():
    """Test the Gmail service functionality"""
    
    print("🚀 Testing Gmail Service with OAuth2...")
    
    # Initialize the service
    gmail = GmailService()
    
    # Get user info (this will trigger authentication if needed)
    print("\n📧 Getting user info...")
    user_info = gmail.get_user_info()
    if user_info:
        print(f"✅ Authenticated as: {user_info['emailAddress']}")
    else:
        print("❌ Failed to get user info")
        return
    
    # Test sending a plain text email
    print("\n📤 Testing plain text email...")
    test_email = "your-test-email@example.com"  # Change this to your test email
    
    text_result = gmail.send_email(
        to_email=test_email,
        subject="🧪 Test Email from Gmail API",
        body="""Hello!

This is a test email sent using the Gmail API with OAuth2 authentication.

Features:
- OAuth2 authentication flow
- Automatic token refresh
- Token persistence
- Error handling

Best regards,
Your Gmail Service
"""
    )
    
    if text_result:
        print("✅ Plain text email sent successfully!")
        print(f"   Message ID: {text_result['id']}")
    else:
        print("❌ Failed to send plain text email")
    
    # Test sending an HTML email
    print("\n📤 Testing HTML email...")
    html_body = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #4285f4; color: white; padding: 20px; border-radius: 5px; }
            .content { margin: 20px 0; }
            .footer { color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 HTML Test Email</h1>
        </div>
        <div class="content">
            <p>This is a <strong>beautiful HTML email</strong> sent using the Gmail API!</p>
            <ul>
                <li>✅ OAuth2 authentication</li>
                <li>✅ HTML formatting</li>
                <li>✅ Professional styling</li>
                <li>✅ Easy to use</li>
            </ul>
        </div>
        <div class="footer">
            Sent via Gmail API with Python
        </div>
    </body>
    </html>
    """
    
    html_result = gmail.send_html_email(
        to_email=test_email,
        subject="🎨 HTML Test Email from Gmail API",
        html_body=html_body
    )
    
    if html_result:
        print("✅ HTML email sent successfully!")
        print(f"   Message ID: {html_result['id']}")
    else:
        print("❌ Failed to send HTML email")
    
    print("\n🎯 Gmail service test completed!")

if __name__ == "__main__":
    # Make sure to change the test email address above before running
    test_gmail_service()
