from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from config import Config
from models import db, User, Message

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('chat.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': '已登录'})
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'})
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '注册成功'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'success': True})
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db.session.commit()
            
            socketio.emit('user_status_changed', {'user_id': user.id, 'is_online': True})
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.is_online = False
    user.last_seen = datetime.utcnow()
    db.session.commit()
    
    socketio.emit('user_status_changed', {'user_id': user.id, 'is_online': False})
    
    logout_user()
    return jsonify({'success': True})

@app.route('/api/users')
@login_required
def get_users():
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/messages/<int:user_id>')
@login_required
def get_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    for message in messages:
        if message.sender_id == user_id and not message.is_read:
            message.is_read = True
    db.session.commit()
    
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/current_user')
@login_required
def get_current_user():
    return jsonify(current_user.to_dict())

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        current_user.is_online = True
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        emit('user_status_changed', {'user_id': current_user.id, 'is_online': True}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        current_user.is_online = False
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        emit('user_status_changed', {'user_id': current_user.id, 'is_online': False}, broadcast=True)

@socketio.on('private_message')
def handle_private_message(data):
    recipient_id = data['recipient_id']
    content = data['content']
    
    message = Message(
        content=content,
        sender_id=current_user.id,
        recipient_id=recipient_id
    )
    db.session.add(message)
    db.session.commit()
    
    emit('new_message', message.to_dict(), room=str(recipient_id))
    emit('new_message', message.to_dict(), room=str(current_user.id))

@socketio.on('join_user_room')
def handle_join_user_room(data):
    user_id = data['user_id']
    join_room(str(user_id))

@socketio.on('leave_user_room')
def handle_leave_user_room(data):
    user_id = data['user_id']
    leave_room(str(user_id))

@socketio.on('typing')
def handle_typing(data):
    recipient_id = data['recipient_id']
    emit('user_typing', {'user_id': current_user.id}, room=str(recipient_id))

@socketio.on('stop_typing')
def handle_stop_typing(data):
    recipient_id = data['recipient_id']
    emit('user_stop_typing', {'user_id': current_user.id}, room=str(recipient_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
