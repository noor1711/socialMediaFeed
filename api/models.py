from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy import event, CheckConstraint

db = SQLAlchemy()
bcrypt = Bcrypt()


friendships = db.Table(
    'friendships',
    db.Column('user_id', db.Integer, primary_key=True, ),
    db.Column('friend_id', db.Integer, primary_key=True, ),
    db.Column('created_at', db.DateTime, default=datetime.now)
)
class User(db.Model):
    """ User account model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # username, email, passwordhash
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)

    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    friends = db.relationship('User', secondary=friendships, primaryjoin=friendships.c.user_id==id, secondaryjoin=friendships.c.friend_id==id, backref=db.backref("friended_by", lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        """we need to encrypt our password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    
    def check_password(self, password):
        """generate alt for given password and then compare the salt of stored password"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=False):
        """ details to show to other users in response """
        data = {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat()
        }

        if include_email:
            data["email"] = self.email

        return data
    
    def __repr__(self):
        return f"Username: {self.username}"
    
class Post(db.Model):
    """Social Media post model"""
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.now, index=True) # we need to get the most recent dates
    updated_at = db.Column(db.DateTime, default=datetime.now, index=True) # we need to get the most recent dates

    # user id will be a foreign key from the user table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # relationships
    likes = db.relationship('Like', backref="post", lazy="dynamic", cascade="all, delete-orphan")
    likes = db.relationship('Comment', backref="post", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, current_user_id=None):
        data = {
            'id': self.id,
            'content': self.content,
            'image_url': self.image_url, 
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count(),
            'author': {
                'id': self.author.id,
                'username': self.author.username,
            }
        }

        if current_user_id == self.user_id:
            is_liked = self.likes.filter(user_id=current_user_id).first() is not None
            data['is_liked'] = is_liked
        
        return data
    
    def __repr__(self):
        return f'<Post {self.id} by {self.author.username}>'

class Like(db.Model):
    __tablename__ = "likes"
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )

    def __repr__(self):
        return f'<Like {self.id} by {self.user_id} on {self.post_id}>'
    
class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    author = db.relationship('User', backref='comments')

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'author': {
                'id': self.author.id,
                'username': self.author.username
            }
        }
    
    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'
    
class TokenBlockList(db.Model):
    """ Generally JWTs are cleared out from frontend or expiry time is set to really low"""
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)

    # jwt id
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<TokenBlocklist {self.jti}>'


# a relationship works as follows
# in user table we add relationship to post table, with a backref - this is creates a post.author in post model
# in post table we add user_id of user table

@event.listens_for(Post, 'before_update')
def update_post_timestamp(mapper, connection, target):
    target.updated_at = datetime.now

"""
TODO:
post.likes.count()  # Executes: SELECT COUNT(*) FROM likes WHERE post_id = 15

# For better performance with many posts:
from sqlalchemy import func

posts_with_counts = db.session.query(
    Post,
    func.count(Like.id).label('like_count')
).outerjoin(Like).group_by(Post.id).all()

# Single query instead of N queries (N = number of posts)

"""

class Friend(db.Model):
    __tablename__="friends"
    
    id = db.Column(db.Integer, primary_key=True)

    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("user1_id", "user2_id", name='unique_users_should_be_friends'),
        CheckConstraint(user1_id != user2_id, name='user can not befriend oneself')
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'created_at': self.created_at
        }

    def __repr__(self):
        return f"Friend: {self.user1_id} {self.user2_id}"
