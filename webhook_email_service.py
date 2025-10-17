#!/usr/bin/env python3
"""
Simple webhook test server for email sending
This demonstrates how to create a webhook service that receives email requests
"""

from flask import Flask, request, jsonify
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

@app.route('/send-email', methods=['POST'])
def send_email_webhook():
    """
    Webhook endpoint that receives email requests and sends them
    Expects JSON payload with: to, subject, html_body, token
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['to', 'subject', 'html_body']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify webhook token (optional security)
        expected_token = os.environ.get('WEBHOOK_TOKEN', 'test-token')
        provided_token = data.get('token', '')
        
        if expected_token and provided_token != expected_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Extract email data
        to_email = data['to']
        subject = data['subject']
        html_body = data['html_body']
        employee_name = data.get('employee_name', 'Unknown')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        
        # Log the email request
        print(f"=== WEBHOOK EMAIL REQUEST ===")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Employee: {employee_name}")
        print(f"Date Range: {date_from} to {date_to}")
        print(f"Content Length: {len(html_body)} characters")
        
        # Here you would implement your actual email sending logic
        # Options:
        # 1. Use SMTP directly
        # 2. Call another email service API (SendGrid, Mailgun, etc.)
        # 3. Queue the email for batch processing
        # 4. Store in database for later processing
        
        # For this demo, we'll simulate email sending
        simulate_email_sending = True
        
        if simulate_email_sending:
            print("=== WEBHOOK EMAIL SIMULATION ===")
            print("Email would be sent here via your preferred method")
            print("=== SIMULATION COMPLETE ===")
            
            return jsonify({
                'success': True,
                'message': 'Email sent successfully (simulated)',
                'recipient': to_email,
                'method': 'webhook'
            })
        else:
            # Example of real email sending via SMTP
            return send_real_email_via_smtp(to_email, subject, html_body)
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500

def send_real_email_via_smtp(to_email, subject, html_body):
    """Example of sending real email via SMTP from webhook"""
    try:
        # Configure SMTP (these would come from environment variables)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            return jsonify({'error': 'SMTP credentials not configured'}), 500
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"Real email sent via webhook to: {to_email}")
        
        return jsonify({
            'success': True,
            'message': 'Email sent successfully',
            'recipient': to_email,
            'method': 'webhook+smtp'
        })
        
    except Exception as e:
        print(f"SMTP error in webhook: {e}")
        return jsonify({'error': f'SMTP error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Email Webhook Service',
        'version': '1.0.0'
    })

@app.route('/', methods=['GET'])
def info():
    """Service information"""
    return jsonify({
        'service': 'Email Webhook Service',
        'version': '1.0.0',
        'endpoints': {
            'POST /send-email': 'Send email via webhook',
            'GET /health': 'Health check',
            'GET /': 'Service info'
        },
        'payload_format': {
            'to': 'recipient@example.com',
            'subject': 'Email subject',
            'html_body': '<html>Email content</html>',
            'employee_name': 'Employee Name (optional)',
            'date_from': '2025-09-01 (optional)',
            'date_to': '2025-09-03 (optional)',
            'token': 'webhook-token (optional)'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Email Webhook Service on port {port}")
    print("Set WEBHOOK_TOKEN environment variable for security")
    app.run(host='0.0.0.0', port=port, debug=True)