import sys
sys.path.insert(0, '/mnt/d/code/chat')

from app import app
from models import db, User, Message

with app.app_context():
    print("=== 用户列表 ===")
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, 用户名: {user.username}, 在线: {user.is_online}")
    
    print("\n=== 所有消息 ===")
    messages = Message.query.order_by(Message.id).all()
    
    if not messages:
        print("没有消息")
    else:
        for msg in messages:
            sender = User.query.get(msg.sender_id)
            recipient = User.query.get(msg.recipient_id)
            sender_name = sender.username if sender else f"未知({msg.sender_id})"
            recipient_name = recipient.username if recipient else f"未知({msg.recipient_id})"
            
            print(f"\n消息ID: {msg.id}")
            print(f"  发送者: {sender_name} (ID: {msg.sender_id})")
            print(f"  接收者: {recipient_name} (ID: {msg.recipient_id})")
            print(f"  内容: {msg.content}")
            print(f"  时间: {msg.timestamp}")
            print(f"  已读: {msg.is_read}")
