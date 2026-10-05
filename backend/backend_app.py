import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

SWAGGER_URL = "/api/docs"  # Swagger endpoint, e.g. http://localhost:5002/api/docs
API_URL = "/static/masterblog.json"  # Served from backend/static/

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

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
        sort = request.args.get('sort', default='', type=str).strip().lower()
        direction = request.args.get('direction', default='asc', type=str).strip().lower()

        if not sort:
            return jsonify(POSTS)

        if sort not in ('title', 'content'):
            return jsonify({"error": f"Invalid sort field: {sort}. Allowed values are title or content."}), 400

        if direction not in ('asc', 'desc'):
            return jsonify({"error": f"Invalid direction: {direction}. Allowed values are asc or desc."}), 400

        sorted_posts = sorted(POSTS, key=lambda post: post[sort].lower(), reverse=(direction == 'desc'))
        return jsonify(sorted_posts)


@app.route('/api/posts/search', methods=['GET'])
def get_posts_search():
    title = request.args.get('title', default='', type=str).strip().lower()
    content = request.args.get('content', default='', type=str).strip().lower()

    results = []

    for post in POSTS:
        if title:
            if title in post.get('title').lower():
                results.append(post)
        if content:
            if content in post.get('content').lower():
                if post not in results:
                    results.append(post)

    return jsonify(results)


@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    # Find the post with the given ID
    post = next((post for post in POSTS if post['id'] == id), None)
    if post is None:
        app.logger.warning(f'Post with id {id} not found')
        return jsonify({"error": f"Post with id {id} not found."}), 404

    # Remove the post from our list
    POSTS.remove(post)
    app.logger.info(f'Post with id {id} deleted')

    return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:id>', methods=['PUT'])
def update_post(id):
    # Find the post with the given ID
    post = next((post for post in POSTS if post['id'] == id), None)
    if post is None:
        app.logger.warning(f'Post with id {id} not found')
        return jsonify({"error": f"Post with id {id} not found."}), 404

    # Update only the fields provided by the client
    new_data = request.get_json()
    post['title'] = new_data.get('title', post['title'])
    post['content'] = new_data.get('content', post['content'])
    app.logger.info(f'Post with id {id} updated')

    return jsonify(post), 200


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
