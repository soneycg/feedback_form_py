from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

FEEDBACK_FILE = 'feedback_data.json'

# Email Configuration - Update these with your SMTP settings
EMAIL_CONFIG = {
    'smtp_server': 'smtp.example.com',  # e.g., 'smtp.gmail.com', 'smtp.office365.com'
    'smtp_port': 587,                    # Usually 587 for TLS, 465 for SSL
    'smtp_username': 'your-email@example.com',
    'smtp_password': 'your-app-password',
    'sender_email': 'your-email@example.com',
    'recipient_email': 'recipient@example.com',  # Where to send feedback reports
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
    """Format all feedback for email report"""
    if not feedback_list:
        return "<p>No feedback submissions yet.</p>"

    # Calculate statistics
    total = len(feedback_list)
    avg_rating = sum(int(f.get('overall_rating', 0)) for f in feedback_list) / total
    recommend_pct = sum(1 for f in feedback_list if f.get('would_recommend') == 'yes') / total * 100
    attend_pct = sum(1 for f in feedback_list if f.get('attend_again') == 'yes') / total * 100

    feedback_rows = ""
    for f in reversed(feedback_list):
        feedback_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{f.get('timestamp', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{f.get('name', 'Anonymous') or 'Anonymous'}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;"><strong>{f.get('overall_rating', 'N/A')}/5</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{f.get('performance_quality', 'N/A')}/5</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{f.get('sound_quality', 'N/A')}/5</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{f.get('venue_atmosphere', 'N/A')}/5</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{f.get('value_for_money', 'N/A')}/5</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{'Yes' if f.get('would_recommend') == 'yes' else 'No'}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .stats {{ display: flex; background: #f8fafc; border: 1px solid #e2e8f0; }}
            .stat {{ flex: 1; padding: 20px; text-align: center; border-right: 1px solid #e2e8f0; }}
            .stat:last-child {{ border-right: none; }}
            .stat-value {{ font-size: 28px; font-weight: bold; color: #1e40af; }}
            .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #1e40af; color: white; padding: 12px 10px; text-align: left; font-size: 12px; text-transform: uppercase; }}
            .footer {{ background: #e2e8f0; padding: 15px; text-align: center; font-size: 12px; color: #64748b; border-radius: 0 0 8px 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">Feedback Report</h2>
                <p style="margin: 5px 0 0 0;">Shalom Beats Musical Concert Middleton</p>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total Responses</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{avg_rating:.1f}</div>
                    <div class="stat-label">Avg Rating</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{recommend_pct:.0f}%</div>
                    <div class="stat-label">Would Recommend</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{attend_pct:.0f}%</div>
                    <div class="stat-label">Would Attend Again</div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Name</th>
                        <th>Overall</th>
                        <th>Performance</th>
                        <th>Sound</th>
                        <th>Venue</th>
                        <th>Food</th>
                        <th>Recommend</th>
                    </tr>
                </thead>
                <tbody>
                    {feedback_rows}
                </tbody>
            </table>

            <div class="footer">
                Shalom Beats Musical Concert Feedback System
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
def results():
    """Display all feedback results (admin view)"""
    feedback_list = load_feedback()
    return render_template('results.html', feedback_list=feedback_list)

@app.route('/send-report', methods=['POST'])
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
