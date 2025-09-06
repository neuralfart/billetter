#!/usr/bin/env python3
"""
Bodø/Glimt Ticket Monitor
Monitors the Bodø/Glimt website for ticket availability and sends notifications.
"""

import os
import time
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TicketMonitor:
    def __init__(self):
        self.bodo_glimt_url = "https://www.glimt.no"
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('FROM_EMAIL'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'to_email': os.getenv('TO_EMAIL')
        }
        
    def fetch_website_content(self):
        """Fetch the Bodø/Glimt website content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.bodo_glimt_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            text_content = '\n'.join(line for line in lines if line)
            
            logger.info(f"Successfully fetched website content ({len(text_content)} characters)")
            return text_content[:10000]  # Limit content for API efficiency
            
        except requests.RequestException as e:
            logger.error(f"Error fetching website: {e}")
            return None
    
    def analyze_content_with_claude(self, content):
        """Use Claude to analyze if tickets are available for Tottenham match."""
        try:
            prompt = f"""
            Please analyze this content from the Bodø/Glimt website and determine if there are tickets available for ordinary people (not season ticket holders or members) for the Tottenham match.

            Look for:
            1. Any mentions of "Tottenham" or "Spurs" matches
            2. Ticket availability information
            3. General sale information (not just for members/season ticket holders)
            4. Any indication that tickets are on sale to the public

            Website content:
            {content}

            Respond with either:
            - "TICKETS_AVAILABLE" if there are tickets available for ordinary people for the Tottenham match
            - "NO_TICKETS" if no tickets are available or only for members/season ticket holders
            - "NO_INFO" if there's no clear information about Tottenham match tickets

            Also provide a brief explanation of what you found.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            logger.info(f"Claude analysis: {response_text}")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error analyzing content with Claude: {e}")
            return "ERROR"
    
    def send_email_notification(self, subject, body):
        """Send email notification."""
        try:
            msg = EmailMessage()
            msg['From'] = self.email_config['email']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = subject
            msg.set_content(body)
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {self.email_config['to_email']}")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def check_tickets(self, is_first_run=False):
        """Main function to check for ticket availability."""
        logger.info("Starting ticket availability check...")
        
        # Fetch website content
        content = self.fetch_website_content()
        if not content:
            logger.error("Failed to fetch website content")
            if is_first_run:
                self.send_email_notification(
                    "❌ BODØ/GLIMT MONITOR STARTED - ERROR",
                    f"The ticket monitor has started but failed to fetch website content.\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            return
        
        # Analyze with Claude
        analysis = self.analyze_content_with_claude(content)
        
        if "TICKETS_AVAILABLE" in analysis:
            subject = "🎫 BODØ/GLIMT vs TOTTENHAM TICKETS AVAILABLE!"
            body = f"""
            Great news! Tickets appear to be available for the Bodø/Glimt vs Tottenham match!
            
            Analysis from Claude:
            {analysis}
            
            Check the website immediately: {self.bodo_glimt_url}
            
            Time checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_email_notification(subject, body)
            logger.info("Tickets available! Notification sent.")
            
        elif "NO_TICKETS" in analysis:
            logger.info("No tickets available for ordinary people yet.")
            if is_first_run:
                subject = "✅ BODØ/GLIMT MONITOR STARTED - NO TICKETS YET"
                body = f"""
                The Bodø/Glimt ticket monitor has started successfully!
                
                Current status: No tickets available for ordinary people yet.
                
                Analysis from Claude:
                {analysis}
                
                The monitor will check every hour and notify you when tickets become available.
                
                Time started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                self.send_email_notification(subject, body)
                
        elif "NO_INFO" in analysis:
            logger.info("No clear information about Tottenham match found.")
            if is_first_run:
                subject = "⚠️ BODØ/GLIMT MONITOR STARTED - NO TOTTENHAM INFO"
                body = f"""
                The Bodø/Glimt ticket monitor has started successfully!
                
                Current status: No clear information about the Tottenham match found on the website.
                
                Analysis from Claude:
                {analysis}
                
                The monitor will check every hour and notify you when information becomes available.
                
                Time started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                self.send_email_notification(subject, body)
                
        else:
            logger.warning("Unclear response from Claude analysis.")
            if is_first_run:
                subject = "⚠️ BODØ/GLIMT MONITOR STARTED - UNCLEAR RESPONSE"
                body = f"""
                The Bodø/Glimt ticket monitor has started but received an unclear response from Claude.
                
                Analysis response:
                {analysis}
                
                The monitor will continue checking every hour.
                
                Time started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                self.send_email_notification(subject, body)


def main():
    """Main function to run the ticket monitor."""
    monitor = TicketMonitor()
    
    # Validate required environment variables
    required_vars = ['ANTHROPIC_API_KEY', 'FROM_EMAIL', 'EMAIL_PASSWORD', 'TO_EMAIL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Run initial check with first-run flag
    logger.info("Running initial ticket check...")
    monitor.check_tickets(is_first_run=True)
    
    # Set up scheduler to run every hour
    scheduler = BlockingScheduler()
    scheduler.add_job(
        func=monitor.check_tickets,
        trigger="interval", 
        hours=1,
        id='ticket_check'
    )
    
    logger.info("Starting scheduler. Checking every hour...")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        scheduler.shutdown()


if __name__ == "__main__":
    main()