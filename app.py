from flask import Flask, jsonify, request
import requests
from textblob import TextBlob
from datetime import datetime

app = Flask(__name__)

FEDDIT_API_URL = "http://localhost:8080/api/v1" 
DEFAULT_LIMIT = 20000

def get_comment_polarity(text):
    
    blob = TextBlob(text)
    polarity_score = blob.sentiment.polarity
    if polarity_score > 0:
        classification = 'positive'
    elif polarity_score < 0:
        classification = 'negative'
    else:
        classification = 'neutral'    
    
    return polarity_score, classification

@app.route('/comments', methods=['GET'])
def get_recent_comments():
    subfeddit_id = request.args.get('subfeddit_id')  # Get subfeddit ID from query parameter
    if not subfeddit_id:
        return jsonify({'error': 'Subfeddit ID is required'}), 400

    limit = int(request.args.get('limit', DEFAULT_LIMIT))  # Get limit from query parameter or set default

    start_time_str = request.args.get('start_time')  # Get start_time from query parameter as string
    end_time_str = request.args.get('end_time')  # Get end_time from query parameter as string

    params = {'subfeddit_id': subfeddit_id, 'limit': limit}

    # Add start_time and end_time to the params if provided
    if start_time_str:
        start_timestamp = int(datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S').timestamp())
        # params['start_time'] = start_timestamp
    if end_time_str:
        end_timestamp = int(datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S').timestamp())
        # params['end_time'] = end_timestamp

    # Call the Feddit API to get the comments based on specified parameters
    comments_url = f"{FEDDIT_API_URL}/comments/"
    response = requests.get(comments_url, params=params)

    if response.status_code == 200:
        comments = response.json().get('comments', [])
        # Perform sentiment analysis and classification for each comment
        analyzed_comments = []

        for comment in comments:
            text = comment.get('text', '')
            created_timestamp = comment.get('created_at', '')
            if created_timestamp > start_timestamp and created_timestamp < end_timestamp:         
                created_time = datetime.utcfromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                polarity_score, classification = get_comment_polarity(text)
                analyzed_comment = {
                    'id': comment.get('id', ''),
                    'text': text,
                    'polarity': polarity_score,
                    'classification': classification,
                    'created_time': created_time
                }
                analyzed_comments.append(analyzed_comment)

        # Sort the comments based on polarity score
        sort_by_polarity = request.args.get('sort_by_polarity')
        if sort_by_polarity and sort_by_polarity.lower() == 'true':
            analyzed_comments.sort(key=lambda x: x.get('polarity', 0), reverse=True)

        return jsonify(analyzed_comments)
    else:
        return jsonify({'error': 'Failed to fetch comments'}), 500

if __name__ == '__main__':
    app.run(debug=True)
