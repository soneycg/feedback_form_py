from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from functools import wraps
import json
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

FEEDBACK_FILE = 'feedback_data.json'

# Admin credentials from environment
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

def check_auth(username, password):
    """Check if username/password combination is valid"""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    """Send 401 response to enable basic auth login"""
    return Response(
        'Access denied. Please login with valid credentials.',
        401,
        {'WWW-Authenticate': 'Basic realm="Admin Access Required"'}
    )

def requires_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Email Configuration from environment
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_username': os.getenv('SMTP_USERNAME'),
    'smtp_password': os.getenv('SMTP_PASSWORD'),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'recipient_email': os.getenv('RECIPIENT_EMAIL'),
    'use_tls': True
}

def load_feedback():
    """Load existing feedback from JSON file"""
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    return []

def save_feedback(feedback_list):
    """Save feedback to JSON file"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=2)

def send_email(subject, html_content):
    """Send email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        if EMAIL_CONFIG['use_tls']:
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])

        server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['recipient_email'], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def format_single_feedback_email(feedback):
    """Format a single feedback submission for email"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
            .rating {{ display: inline-block; background: #1e40af; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; }}
            .section {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e2e8f0; }}
            .label {{ font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase; }}
            .value {{ margin-top: 5px; }}
            .footer {{ background: #e2e8f0; padding: 15px; text-align: center; font-size: 12px; color: #64748b; border-radius: 0 0 8px 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">New Feedback Received</h2>
                <p style="margin: 5px 0 0 0;">Shalom Beats Musical Concert Middleton</p>
            </div>
            <div class="content">
                <div class="section">
                    <div class="label">Submitted</div>
                    <div class="value">{feedback.get('timestamp', 'N/A')}</div>
                </div>

                <div class="section">
                    <div class="label">Respondent</div>
                    <div class="value">{feedback.get('name', 'Anonymous') or 'Anonymous'}</div>
                    {f"<div class='value' style='color: #64748b;'>{feedback.get('email')}</div>" if feedback.get('email') else ''}
                </div>

                <div class="section">
                    <div class="label">Overall Rating</div>
                    <div class="value"><span class="rating">{feedback.get('overall_rating', 'N/A')}/5</span></div>
                </div>

                <div class="section">
                    <div class="label">Detailed Ratings</div>
                    <div class="value">
                        <p>Performance Quality: <strong>{feedback.get('performance_quality', 'N/A')}/5</strong></p>
                        <p>Sound Quality: <strong>{feedback.get('sound_quality', 'N/A')}/5</strong></p>
                        <p>Venue & Atmosphere: <strong>{feedback.get('venue_atmosphere', 'N/A')}/5</strong></p>
                        <p>Food: <strong>{feedback.get('value_for_money', 'N/A')}/5</strong></p>
                    </div>
                </div>

                {f'''<div class="section">
                    <div class="label">Favorite Moment</div>
                    <div class="value">{feedback.get('favorite_moment')}</div>
                </div>''' if feedback.get('favorite_moment') else ''}

                {f'''<div class="section">
                    <div class="label">Suggested Improvements</div>
                    <div class="value">{feedback.get('improvements')}</div>
                </div>''' if feedback.get('improvements') else ''}

                {f'''<div class="section">
                    <div class="label">Additional Comments</div>
                    <div class="value">{feedback.get('additional_comments')}</div>
                </div>''' if feedback.get('additional_comments') else ''}

                <div class="section" style="border-bottom: none;">
                    <p>Would Recommend: <strong>{'Yes' if feedback.get('would_recommend') == 'yes' else 'No'}</strong></p>
                    <p>Would Attend Again: <strong>{'Yes' if feedback.get('attend_again') == 'yes' else 'No'}</strong></p>
                </div>
            </div>
            <div class="footer">
                Shalom Beats Musical Concert Feedback System
            </div>
        </div>
    </body>
    </html>
    """
    return html

def format_all_feedback_email(feedback_list):
    """Format all feedback for email report with complete details"""
    if not feedback_list:
        return "<p>No feedback submissions yet.</p>"

    # Calculate statistics
    total = len(feedback_list)
    avg_rating = sum(int(f.get('overall_rating', 0)) for f in feedback_list) / total
    avg_performance = sum(int(f.get('performance_quality', 0)) for f in feedback_list) / total
    avg_sound = sum(int(f.get('sound_quality', 0)) for f in feedback_list) / total
    avg_venue = sum(int(f.get('venue_atmosphere', 0)) for f in feedback_list) / total
    avg_food = sum(int(f.get('value_for_money', 0)) for f in feedback_list) / total
    recommend_pct = sum(1 for f in feedback_list if f.get('would_recommend') == 'yes') / total * 100
    attend_pct = sum(1 for f in feedback_list if f.get('attend_again') == 'yes') / total * 100

    # Build detailed feedback cards
    feedback_cards = ""
    for i, f in enumerate(reversed(feedback_list), 1):
        name = f.get('name', 'Anonymous') or 'Anonymous'
        email = f.get('email', '')

        # Comments sections
        comments_html = ""
        if f.get('favorite_moment'):
            comments_html += f'''
            <div style="background: #f0f9ff; padding: 12px 15px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #1e3a5f;">
                <div style="font-size: 11px; font-weight: bold; color: #1e3a5f; text-transform: uppercase; margin-bottom: 5px;">Favorite Moment</div>
                <div style="color: #334155;">{f.get('favorite_moment')}</div>
            </div>
            '''
        if f.get('improvements'):
            comments_html += f'''
            <div style="background: #fef3c7; padding: 12px 15px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #d97706;">
                <div style="font-size: 11px; font-weight: bold; color: #d97706; text-transform: uppercase; margin-bottom: 5px;">Suggested Improvements</div>
                <div style="color: #334155;">{f.get('improvements')}</div>
            </div>
            '''
        if f.get('additional_comments'):
            comments_html += f'''
            <div style="background: #f1f5f9; padding: 12px 15px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #64748b;">
                <div style="font-size: 11px; font-weight: bold; color: #64748b; text-transform: uppercase; margin-bottom: 5px;">Additional Comments</div>
                <div style="color: #334155;">{f.get('additional_comments')}</div>
            </div>
            '''

        feedback_cards += f'''
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 20px; overflow: hidden;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1e3a5f, #2c5282); padding: 15px 20px; color: white;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td>
                            <div style="font-weight: bold; font-size: 16px;">{name}</div>
                            {f'<div style="font-size: 13px; opacity: 0.9;">{email}</div>' if email else ''}
                        </td>
                        <td style="text-align: right;">
                            <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold;">
                                ★ {f.get('overall_rating', 'N/A')}/5
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Body -->
            <div style="padding: 20px;">
                <div style="font-size: 12px; color: #64748b; margin-bottom: 15px;">Submitted: {f.get('timestamp', 'N/A')}</div>

                <!-- Ratings Grid -->
                <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 15px;">
                    <tr>
                        <td style="background: #f8fafc; border-radius: 6px; text-align: center; width: 25%;">
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Performance</div>
                            <div style="font-size: 18px; font-weight: bold; color: #1e3a5f;">{f.get('performance_quality', 'N/A')}/5</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 6px; text-align: center; width: 25%;">
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Sound</div>
                            <div style="font-size: 18px; font-weight: bold; color: #1e3a5f;">{f.get('sound_quality', 'N/A')}/5</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 6px; text-align: center; width: 25%;">
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Venue</div>
                            <div style="font-size: 18px; font-weight: bold; color: #1e3a5f;">{f.get('venue_atmosphere', 'N/A')}/5</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 6px; text-align: center; width: 25%;">
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Food</div>
                            <div style="font-size: 18px; font-weight: bold; color: #1e3a5f;">{f.get('value_for_money', 'N/A')}/5</div>
                        </td>
                    </tr>
                </table>

                <!-- Comments -->
                {comments_html}

                <!-- Footer Tags -->
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                    <span style="display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; margin-right: 8px; {'background: #dcfce7; color: #166534;' if f.get('would_recommend') == 'yes' else 'background: #fee2e2; color: #991b1b;'}">
                        {'✓' if f.get('would_recommend') == 'yes' else '✗'} Would Recommend
                    </span>
                    <span style="display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; {'background: #dcfce7; color: #166534;' if f.get('attend_again') == 'yes' else 'background: #fee2e2; color: #991b1b;'}">
                        {'✓' if f.get('attend_again') == 'yes' else '✗'} Would Attend Again
                    </span>
                </div>
            </div>
        </div>
        '''

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f1f5f9; margin: 0; padding: 0; }}
        </style>
    </head>
    <body style="background: #f1f5f9; padding: 20px;">
        <div style="max-width: 700px; margin: 0 auto;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1e3a5f, #0d2137); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Feedback Report</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">Shalom Beats Musical Concert Middleton</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.7;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <!-- Stats Summary -->
            <div style="background: white; padding: 25px; border-bottom: 1px solid #e2e8f0;">
                <h2 style="margin: 0 0 20px 0; font-size: 16px; color: #1e3a5f; text-transform: uppercase; letter-spacing: 1px;">Summary Statistics</h2>
                <table width="100%" cellpadding="10" cellspacing="0">
                    <tr>
                        <td style="background: #f8fafc; border-radius: 8px; text-align: center; width: 25%;">
                            <div style="font-size: 32px; font-weight: bold; color: #1e3a5f;">{total}</div>
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Responses</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 8px; text-align: center; width: 25%;">
                            <div style="font-size: 32px; font-weight: bold; color: #f59e0b;">{avg_rating:.1f}</div>
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Avg Rating</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 8px; text-align: center; width: 25%;">
                            <div style="font-size: 32px; font-weight: bold; color: #10b981;">{recommend_pct:.0f}%</div>
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Recommend</div>
                        </td>
                        <td style="background: #f8fafc; border-radius: 8px; text-align: center; width: 25%;">
                            <div style="font-size: 32px; font-weight: bold; color: #ec4899;">{attend_pct:.0f}%</div>
                            <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Attend Again</div>
                        </td>
                    </tr>
                </table>

                <!-- Category Averages -->
                <h3 style="margin: 25px 0 15px 0; font-size: 14px; color: #475569;">Average Ratings by Category</h3>
                <table width="100%" cellpadding="8" cellspacing="0">
                    <tr>
                        <td style="background: #f8fafc; border-radius: 6px; padding: 12px;">
                            <span style="color: #64748b;">Performance:</span>
                            <strong style="color: #1e3a5f; float: right;">{avg_performance:.1f}/5</strong>
                        </td>
                        <td style="background: #f8fafc; border-radius: 6px; padding: 12px;">
                            <span style="color: #64748b;">Sound Quality:</span>
                            <strong style="color: #1e3a5f; float: right;">{avg_sound:.1f}/5</strong>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: #f8fafc; border-radius: 6px; padding: 12px;">
                            <span style="color: #64748b;">Venue & Atmosphere:</span>
                            <strong style="color: #1e3a5f; float: right;">{avg_venue:.1f}/5</strong>
                        </td>
                        <td style="background: #f8fafc; border-radius: 6px; padding: 12px;">
                            <span style="color: #64748b;">Food:</span>
                            <strong style="color: #1e3a5f; float: right;">{avg_food:.1f}/5</strong>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Individual Feedback -->
            <div style="background: #f1f5f9; padding: 25px;">
                <h2 style="margin: 0 0 20px 0; font-size: 16px; color: #1e3a5f; text-transform: uppercase; letter-spacing: 1px;">All Feedback ({total} responses)</h2>
                {feedback_cards}
            </div>

            <!-- Footer -->
            <div style="background: #1e3a5f; color: white; padding: 20px; text-align: center; border-radius: 0 0 12px 12px;">
                <p style="margin: 0; font-size: 13px; opacity: 0.9;">Shalom Beats Musical Concert Feedback System</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.7;">This report contains all feedback submissions</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/')
def index():
    """Display the feedback form"""
    return render_template('feedback_form.html')

@app.route('/submit', methods=['POST'])
def submit_feedback():
    """Handle form submission"""
    feedback = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'name': request.form.get('name', '').strip(),
        'email': request.form.get('email', '').strip(),
        'overall_rating': request.form.get('overall_rating'),
        'performance_quality': request.form.get('performance_quality'),
        'sound_quality': request.form.get('sound_quality'),
        'venue_atmosphere': request.form.get('venue_atmosphere'),
        'value_for_money': request.form.get('value_for_money'),
        'favorite_moment': request.form.get('favorite_moment', '').strip(),
        'improvements': request.form.get('improvements', '').strip(),
        'would_recommend': request.form.get('would_recommend'),
        'attend_again': request.form.get('attend_again'),
        'additional_comments': request.form.get('additional_comments', '').strip()
    }

    # Load existing feedback and append new entry
    feedback_list = load_feedback()
    feedback_list.append(feedback)
    save_feedback(feedback_list)

    # Send email notification for new submission
    email_html = format_single_feedback_email(feedback)
    send_email("New Feedback - Shalom Beats Concert", email_html)

    flash('Thank you for your feedback! Your response has been recorded.', 'success')
    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    """Display thank you page"""
    return render_template('thank_you.html')

@app.route('/results')
@requires_auth
def results():
    """Display all feedback results (admin view)"""
    feedback_list = load_feedback()
    return render_template('results.html', feedback_list=feedback_list)

@app.route('/send-report', methods=['POST'])
@requires_auth
def send_report():
    """Send all feedback as email report"""
    feedback_list = load_feedback()
    email_html = format_all_feedback_email(feedback_list)

    if send_email("Feedback Report - Shalom Beats Concert", email_html):
        return jsonify({'success': True, 'message': 'Report sent successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send report. Check email configuration.'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
