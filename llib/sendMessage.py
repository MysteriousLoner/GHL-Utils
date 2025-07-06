import smtplib
import logging
import re
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger('email_sender')

# Email configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SENDER_NAME = os.getenv('SENDER_NAME', 'GHL Utils')

def validate_email_format(email):
    """
    Validate email format using regex
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_email_domain_exists(email):
    """
    Check if the email domain has valid MX records
    
    Args:
        email (str): Email address to check
        
    Returns:
        bool: True if domain exists, False otherwise
    """
    try:
        domain = email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
        return False

def validate_email_exists(email):
    """
    Validate that email address exists (format + domain check)
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email appears to exist, False otherwise
        
    Raises:
        ValueError: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email address is required and must be a string")
    
    # Check format
    if not validate_email_format(email):
        raise ValueError(f"Invalid email format: {email}")
    
    # Check domain exists
    if not check_email_domain_exists(email):
        raise ValueError(f"Email domain does not exist: {email}")
    
    return True

def send_email(target_email, message, subject="Message from GHL Utils"):
    """
    Send an email to the target email address
    
    Args:
        target_email (str): The recipient's email address
        message (str): The message content to send
        subject (str, optional): Email subject line
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Raises:
        ValueError: If parameters are invalid or email doesn't exist
        RuntimeError: If email sending fails
    """
    # Input validation
    if not target_email:
        error_msg = "Missing required parameter: target_email"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not message:
        error_msg = "Missing required parameter: message"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check email configuration
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        error_msg = "Email configuration missing. Please set SENDER_EMAIL and SENDER_PASSWORD in environment variables"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Validate email exists
    try:
        validate_email_exists(target_email)
    except ValueError as e:
        logger.error(f"Email validation failed: {str(e)}")
        raise
    
    try:
        logger.info(f"Preparing to send email to: {target_email}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = target_email
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        logger.debug(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable TLS encryption
        
        # Login to sender account
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, target_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully to: {target_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Recipient email rejected: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error occurred: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def send_html_email(target_email, html_message, subject="Message from GHL Utils"):
    """
    Send an HTML email to the target email address
    
    Args:
        target_email (str): The recipient's email address
        html_message (str): The HTML message content to send
        subject (str, optional): Email subject line
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Raises:
        ValueError: If parameters are invalid or email doesn't exist
        RuntimeError: If email sending fails
    """
    # Input validation
    if not target_email:
        error_msg = "Missing required parameter: target_email"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not html_message:
        error_msg = "Missing required parameter: html_message"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check email configuration
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        error_msg = "Email configuration missing. Please set SENDER_EMAIL and SENDER_PASSWORD in environment variables"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Validate email exists
    try:
        validate_email_exists(target_email)
    except ValueError as e:
        logger.error(f"Email validation failed: {str(e)}")
        raise
    
    try:
        logger.info(f"Preparing to send HTML email to: {target_email}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = target_email
        msg['Subject'] = subject
        
        # Add HTML message body
        html_part = MIMEText(html_message, 'html')
        msg.attach(html_part)
        
        # Create SMTP session
        logger.debug(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable TLS encryption
        
        # Login to sender account
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, target_email, text)
        server.quit()
        
        logger.info(f"HTML email sent successfully to: {target_email}")
        return True
        
    except Exception as e:
        error_msg = f"Error sending HTML email: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

# Test function
def test_email_sending():
    """Test function to verify email sending functionality"""
    try:
        test_email = "test@example.com"
        test_message = "This is a test message from GHL Utils"
        
        result = send_email(test_email, test_message, "Test Email")
        print(f"Test email result: {result}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_email_sending()