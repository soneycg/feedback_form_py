# Musical Concert Feedback Form

A professional Flask-based web application for collecting and analyzing feedback from musical concert attendees.

## Features

- **Beautiful, Responsive Design**: Modern gradient-themed interface that works on all devices
- **Comprehensive Feedback Collection**:
  - Overall rating (1-5 stars)
  - Detailed ratings for performance quality, sound, venue, and value
  - Open-ended questions for favorite moments and improvements
  - Yes/No questions for recommendations and future attendance
  - Optional contact information
- **Data Storage**: All feedback is saved to a JSON file for easy access and analysis
- **Admin Dashboard**: View all responses with statistics and visualizations at `/results`
- **Real-time Statistics**: Average ratings, recommendation rates, and more

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to:
   - Main feedback form: `http://localhost:5000/`
   - View results: `http://localhost:5000/results`

3. Fill out the feedback form and submit

4. All responses are automatically saved to `feedback_data.json`

## File Structure

```
feedback-form/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── feedback_data.json          # Stored feedback (created automatically)
├── templates/
│   ├── feedback_form.html      # Main feedback form
│   ├── thank_you.html          # Submission confirmation page
│   └── results.html            # Admin dashboard to view results
└── README.md                   # This file
```

## Customization

### Changing the Secret Key
In production, update the secret key in `app.py`:
```python
app.secret_key = 'your-secure-random-key-here'
```

### Modifying Questions
Edit the HTML templates in the `templates/` directory to add, remove, or modify questions.

### Changing the Port
Modify the last line in `app.py`:
```python
app.run(debug=True, port=5000)  # Change port number here
```

## Security Notes

- Change the secret key before deploying to production
- Consider adding authentication for the `/results` endpoint
- Use HTTPS in production environments
- Implement rate limiting for form submissions

## Data Privacy

- Email addresses are optional and only collected if provided
- All data is stored locally in `feedback_data.json`
- No data is sent to external services

## License

Free to use and modify for your concert feedback needs!
