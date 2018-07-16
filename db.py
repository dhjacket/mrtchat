import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table('users', metadata,
    sa.Column('user_id', sa.Integer, primary_key=True,  autoincrement=True),
    sa.Column('login', sa.String(150), nullable=False, unique=True),
    sa.Column('password', sa.String(64), nullable=False)
)

chats = sa.Table('chats', metadata,
    sa.Column('chat_id', sa.Integer, primary_key=True,  autoincrement=True),
)

chat_users = sa.Table('chat_users', metadata,
    sa.Column('chat_user_id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('chat_id', sa.Integer, sa.ForeignKey("chats.chat_id"), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
)

messages = sa.Table('messages', metadata,
    sa.Column('message_id', sa.Integer, primary_key=True,  autoincrement=True),
    sa.Column('text', sa.Text),
    sa.Column('user_id', sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
    sa.Column('chat_id', sa.Integer, sa.ForeignKey("chats.chat_id"), nullable=True),
)


