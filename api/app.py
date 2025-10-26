from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import ( JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity )
from datetime import datetime, timedelta
from config import config
from models import db, bcrypt, User, Post, Like, Comment, TokenBlockList, Friend
import os

app = Flask(__name__)

app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

CORS(app, origins=["http://localhost:3000"])

db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    # study more on flask-migrate


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """
        This method is called whenever user tries to contact a protected route
        jwt_header:
            tokentype - bearer
            algo - hs256
        jwt_payload:
            user_id, expiration, jti
    """
    
    jti = jwt_payload['jti']

    token = TokenBlockList.query.filter(jti=jti).first()

    return token is not None

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
        Request format - 
            username
            email
            password
        
        Response format - (201) 
            username
            access_token
            refresh_token
            message
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": 'Username, email and password are required fields'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip().lower()
    password = data['password']

    if len(data.get('password')) < 6:
        return jsonify({'error': 'password need to be atleast 6 characters'}), 400
    
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email already in use'}), 409
    
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': 'Username already in use'}), 409

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # create JWT tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'message': 'Successfully created user!',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@app.route("/login", methods=["POST"])
def login():
    """
        Request and response structure almost like register
        Request - 
        email, username
        password
    """

    data = request.get_json()
    if not data or not (data.get('email') or data.get('username')) or not data.get('password'):
        return jsonify({"error": 'Email and password are required fields'}), 400
    
    username = data.get('username').strip()    
    email = data.get('email').strip().lower()
    password = data['password']

    user = User.query.filter((User.username==username) | (User.email==email)).first()
    
    if user is None:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'message': 'Successfully logged in!',
        'user': user.to_dict(include_email=True),
        'access_toke': access_token,
        'refresh_token': refresh_token
    }), 200

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
        Get the new access_token using refresh token, refresh=True, ensures that only refresh_token is accepted
    """

    current_user_id = get_jwt_identity()

    new_access_token = create_access_token(identity=current_user_id)

    return jsonify({
        'access_token': new_access_token
    }), 200

@app.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    """
        We need to invalidate the JWT token used in Authentication
    """

    token = get_jwt()
    jti = token['jti']

    token_blocklist = TokenBlockList(jti=jti)
    db.session.add(token_blocklist)
    db.session.commit()

    return jsonify({ 'message': 'Successfully logged out'}), 200

# TODO: to be ran as scheduled task 
def cleanup_blocklist():
    cutoff = datetime.now() - timedelta(days=30)
    TokenBlockList.query.filter(TokenBlockList.created_at < cutoff).delete();
    db.session.commit()

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
        Return the info for current user
    """

    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200


@app.route('/api/feed', methods=["GET"])
@jwt_required()
def get_feed():
    """
        Request - 
        query_params - page_size, page

        Response - 
        {
            "posts" : [
                {
                    id: 1,
                    content,
                    image_url,
                    likes_count,
                    comments_count,
                    is_liked,
                    author: {
                        id: 1, 
                        username: johndoe
                    }
                }
            ], 
            "pagination": {
                "page": 2, 
                "per_page": 10, 
                "total_pages": 5,
                "total_posts": 98,
                "has_next": true,
                "has_prev": true
            }
        }
    """

    current_user_id = get_jwt_identity()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    per_page = min(per_page, 100)

    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, 
        per_page=per_page,
        error_out=False # do not error out is num of pages is less than curr page 
    )

    posts = [post.to_dict(current_user_id=current_user_id) for post in pagination.items]

    return jsonify({
        'posts': posts,
        'pagination': {
            'page': page, 
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_posts': pagination.total,
            'has_next': pagination.hasNext,
            'has_next': pagination.hasPrev,
        }
    }), 200


@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    """
        Request - 
            content
            image_url

        Response - 
            message
    """

    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'error': 'Content is Required'}), 400

    content = data['content'].strip()

    if len(content) == 0:
        return jsonify({'error': 'Content should not be empty'}), 400

    if len(content) > 5000:  # Max 5000 characters
        return jsonify({'error': 'Content too long (max 5000 characters)'}), 400
        
    post = Post(content=content, image_url=data['image_url'], user_id=current_user_id)
    db.session.add(post)
    db.session.commit()

    return jsonify({'post': post.to_dict(current_user_id=current_user_id)}), 201
    
@app.route('/api/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    return jsonify({post.to_dict(current_user_id=current_user_id)}), 200

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    data = request.get_json()


    if post.user_id != current_user_id:
        return jsonify({'error': 'You are not authorized to edit this post'}), 401

    if 'content' in data:
        content = data['content'].strip()

        if not len(content):
            return jsonify({'error': 'Content can not be empty'}), 400

        post.content = content
    
    if 'image_url' in data:
        post.image_url = data['image_url']
    post.update_at = datetime.now
    db.session.commit()

    return jsonify({post.to_dict(current_user_id=current_user_id)}), 200

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user_id:
        return jsonify({'error': 'You are not authorized to delete this post'}), 401
    
    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post deleted successfully'}), 200

@app.route('/api/post/<int:post_id>/like', methods=['POST'])
@jwt_required()
def toggle_post_like(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    # lets see if we have already liked this photo
    like = Like.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    already_liked = like is not None
    if like:
        # we need to delete this like
        db.session.delete(like);
    else:
        like = Like(user_id=current_user_id, post_id=post_id)
        db.session.add(like)
    
    db.session.commit()

    return jsonify({'message': 'Post Unliked' if already_liked else 'Post Liked', 'likes_count': post.likes.count(), 'is_liked': not already_liked}), 200 if not already_liked else 201  

@app.route('/api/post/<int:post_id>/comments', methods=["GET"])
@jwt_required()
def get_comments(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id, user_id=current_user_id).order_by(Comment.created_at.desc()).all()

    return jsonify({'comments': [comment.to_dict() for comment in comments]}), 200

@app.route('/api/post/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)

    data = request.get_json()

    if not data or not data.get('comment'):
        return jsonify({'error': 'Comment can not be empty'}), 400

    content = data['content'].strip()

    if not len(content):
        return jsonify({'error': 'Comment can not be empty'}), 400

    comment = Comment(content=comment, user_id=current_user_id, post_id=post_id)

    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict), 201

@app.route('/api/curatedFeed', methods=['GET'])
@jwt_required
def get_friends_posts():
    user_id = get_jwt_identity()

    user_ids = Friend.query.filter((Friend.user1_id==user_id) | (Friend.user2_id==user_id)).all()

    # now we need to get the posts of all the friends
    allPosts = Post.query.filter(Post.user_id.in_(user_ids)).order_by(Post.created_at.desc()).all()

    return jsonify({'posts': [post.to_dict() for post in allPosts]}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
