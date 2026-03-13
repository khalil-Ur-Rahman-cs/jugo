# check_login.py - LOGIN DEBUGGING

import sqlite3
import hashlib

print("=" * 50)
print("🔍 LOGIN DEBUGGING TOOL")
print("=" * 50)

conn = sqlite3.connect('database/jugo_swat.db')
cursor = conn.cursor()

# 1. Check admin table
print("\n1. Checking admin table...")
cursor.execute("SELECT * FROM admin")
admin = cursor.fetchone()

if admin:
    print(f"   ID: {admin[0]}")
    print(f"   Username: {admin[1]}")
    print(f"   Password (hashed): {admin[2][:20]}...")
    print(f"   Created: {admin[3]}")
else:
    print("   ❌ NO ADMIN FOUND!")
    conn.close()
    exit()

# 2. Test password hashing
print("\n2. Testing password hash...")
test_password = "admin123"
expected_hash = hashlib.sha256(test_password.encode()).hexdigest()
print(f"   Input password: {test_password}")
print(f"   Generated hash: {expected_hash[:20]}...")

# 3. Compare with database
print("\n3. Comparing hashes...")
if admin[2] == expected_hash:
    print("   ✅ HASH MATCH!")
else:
    print("   ❌ HASH MISMATCH!")
    print(f"   DB hash:    {admin[2][:30]}...")
    print(f"   Gen hash:   {expected_hash[:30]}...")

# 4. Try login
print("\n4. Testing login query...")
cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", 
               ("admin", expected_hash))
result = cursor.fetchone()

if result:
    print("   ✅ LOGIN QUERY SUCCESS")
else:
    print("   ❌ LOGIN QUERY FAILED")

# 5. FIX: Recreate admin if needed
print("\n5. Fixing admin (if needed)...")
cursor.execute("DELETE FROM admin")
hashed = hashlib.sha256('admin123'.encode()).hexdigest()
cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
               ("admin", hashed))
conn.commit()
print("   ✅ Admin recreated with password: admin123")

conn.close()
print("\n" + "=" * 50)
print("🔧 DONE! Ab 'python main.py' try karein")
print("=" * 50)