import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


def validate_post_data(data):
    missing_fields = [field for field in ("title", "content") if field not in data]
    if missing_fields:
        app.logger.warning(f'Post data is missing: {", ".join(missing_fields)}')
    else:
        app.logger.info('Post data is valid')
    return missing_fields


@app.route('/api/posts', methods=['GET', 'POST'])
def get_posts():
    if request.method == 'POST':

        # Get the new post data from the client
        new_post = request.get_json()
        missing_fields = validate_post_data(new_post)
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        # Generate a new ID for the post
        new_id = max((post['id'] for post in POSTS), default=0) + 1
        new_post['id'] = new_id

        # Add the new post to our list
        POSTS.append(new_post)
        app.logger.info(f'Post with id {new_id} added')

        # Return the new post data to the client
        return jsonify(new_post), 201
    else:
        return jsonify(POSTS)


@app.errorhandler(429)
def rate_limit_error(error):
    app.logger.warning(f'Rate limit exceeded for {request.path}')
    return jsonify({"error": "Too Many Requests"}), 429


@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f'Not found: {request.path}')
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    app.logger.warning(f'Method {request.method} not allowed for {request.path}')
    return jsonify({"error": "Method Not Allowed"}), 405


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
