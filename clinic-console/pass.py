import bcrypt

password = b"123"
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password, salt)
print(hashed.decode())
