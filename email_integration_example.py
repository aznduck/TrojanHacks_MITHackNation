#!/usr/bin/env python3
"""
Example integration of Gmail service with the existing project
This shows how to send email notifications for deployments
"""

from gmail_service import GmailService
from datetime import datetime

class DeploymentNotifier:
    def __init__(self, gmail_service=None):
        """Initialize with optional Gmail service instance"""
        self.gmail_service = gmail_service or GmailService()
    
    def send_deployment_start_notification(self, deployment_id, repo_url, commit_sha, recipients):
        """Send notification when deployment starts"""
        subject = f"🚀 Deployment Started - {deployment_id[:8]}"
        
        body = f"""
Deployment Notification

Deployment ID: {deployment_id}
Repository: {repo_url}
Commit: {commit_sha[:8]}
Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Status: In Progress
The deployment pipeline is now running. You will receive updates as the process continues.

Best regards,
Deployment System
"""
        
        return self._send_to_recipients(recipients, subject, body)
    
    def send_deployment_complete_notification(self, deployment_id, status, results, recipients):
        """Send notification when deployment completes"""
        subject = f"✅ Deployment Complete - {deployment_id[:8]} - {status.title()}"
        
        # Format results nicely
        results_summary = self._format_results_summary(results)
        
        body = f"""
Deployment Complete

Deployment ID: {deployment_id}
Status: {status.title()}
Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Results Summary:
{results_summary}

View deployment details at: /deployment/{deployment_id}

Best regards,
Deployment System
"""
        
        return self._send_to_recipients(recipients, subject, body)
    
    def send_deployment_failure_notification(self, deployment_id, error, recipients):
        """Send notification when deployment fails"""
        subject = f"❌ Deployment Failed - {deployment_id[:8]}"
        
        body = f"""
Deployment Failure Alert

Deployment ID: {deployment_id}
Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error Details:
{error}

Please check the deployment logs and take appropriate action.

Best regards,
Deployment System
"""
        
        return self._send_to_recipients(recipients, subject, body)
    
    def send_incident_alert(self, deployment_id, incident_details, recipients):
        """Send incident alert notification"""
        subject = f"🚨 Incident Alert - {deployment_id[:8]}"
        
        body = f"""
Incident Alert

Deployment ID: {deployment_id}
Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Incident Details:
{incident_details}

Please investigate and respond to this incident.

Best regards,
Monitoring System
"""
        
        return self._send_to_recipients(recipients, subject, body)
    
    def _format_results_summary(self, results):
        """Format deployment results into a readable summary"""
        if not results:
            return "No results available"
        
        summary_lines = []
        
        # Infrastructure
        if results.get('infrastructure_files'):
            summary_lines.append("🏗️  Infrastructure files identified")
        if results.get('dockerfile'):
            summary_lines.append("🐳 Dockerfile generated")
        if results.get('ci_cd_config'):
            summary_lines.append("⚙️  CI/CD configuration created")
        
        # Dependencies
        if results.get('dependencies'):
            summary_lines.append(f"📦 {len(results.get('dependencies', []))} dependencies analyzed")
        if results.get('risks'):
            summary_lines.append(f"⚠️  {len(results.get('risks', []))} security risks identified")
        
        # Tests
        if results.get('test_passed'):
            summary_lines.append("🧪 Tests passed successfully")
        if results.get('ai_tests'):
            summary_lines.append("🤖 AI-generated tests created")
        
        # Deployment
        if results.get('deployment_url'):
            summary_lines.append(f"🌐 Deployed to: {results.get('deployment_url')}")
        
        # Monitoring
        if results.get('healthy'):
            summary_lines.append("💚 System health: Good")
        else:
            summary_lines.append("🔴 System health: Issues detected")
        
        return "\n".join(summary_lines) if summary_lines else "Results processing completed"
    
    def _send_to_recipients(self, recipients, subject, body):
        """Send email to multiple recipients"""
        if isinstance(recipients, str):
            recipients = [recipients]
        
        results = []
        for recipient in recipients:
            try:
                result = self.gmail_service.send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body
                )
                results.append({
                    'recipient': recipient,
                    'success': bool(result),
                    'message_id': result.get('id') if result else None
                })
            except Exception as e:
                results.append({
                    'recipient': recipient,
                    'success': False,
                    'error': str(e)
                })
        
        return results


# Example usage in your existing project
def integrate_with_deployment_system():
    """Example of how to integrate with your existing deployment system"""
    
    # Initialize the notifier
    notifier = DeploymentNotifier()
    
    # Example: Send deployment start notification
    recipients = ["team@example.com", "dev@example.com"]
    
    start_result = notifier.send_deployment_start_notification(
        deployment_id="abc12345-def6-7890-ghij-klmnopqrstuv",
        repo_url="https://github.com/example/repo",
        commit_sha="a1b2c3d4e5f6",
        recipients=recipients
    )
    
    print("Deployment start notifications sent:")
    for result in start_result:
        if result['success']:
            print(f"✅ {result['recipient']}: {result['message_id']}")
        else:
            print(f"❌ {result['recipient']}: {result.get('error', 'Unknown error')}")


# Example: Integration with your existing API
def add_email_notifications_to_api():
    """Example of how to add email notifications to your existing API endpoints"""
    
    # In your api.py, you could add:
    """
    from email_integration_example import DeploymentNotifier
    
    # Initialize once
    deployment_notifier = DeploymentNotifier()
    
    @app.post("/webhook/github")
    async def github_webhook(request: Request, background: BackgroundTasks):
        # ... existing code ...
        
        # Send start notification
        background.add_task(
            deployment_notifier.send_deployment_start_notification,
            deployment_id=deployment_id,
            repo_url=repo_url,
            commit_sha=commit_sha,
            recipients=["your-team@example.com"]
        )
        
        # ... rest of existing code ...
    """


if __name__ == "__main__":
    print("📧 Gmail Integration Examples")
    print("=" * 50)
    
    # Test the integration
    integrate_with_deployment_system()
    
    print("\n💡 To use in your project:")
    print("1. Import DeploymentNotifier from this file")
    print("2. Initialize it with your Gmail service")
    print("3. Call notification methods when events occur")
    print("4. Add to background tasks for non-blocking operation")
