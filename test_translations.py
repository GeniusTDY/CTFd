import requests, re, json

s = requests.Session()

# Login as admin
r = s.get('http://localhost:4000/login')
nonce = re.search(r'[a-f0-9]{64}', re.search(r'csrfNonce.{0,80}', r.text).group()).group()
r = s.post('http://localhost:4000/login', data={'name':'admin','password':'Password123!','nonce':nonce}, allow_redirects=False)

passed = 0
failed = 0
def check(name, condition, msg=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name} - {msg}')

# === Chinese ===
s.cookies.set('language', 'zh_CN')
print('=== Chinese (zh_CN) ===')

# 1. Pydantic enum
r = s.get('http://localhost:4000/api/v1/users?field=invalid')
data = r.json()
msg = str(data.get('errors', {}).get('field', ''))
check('Pydantic enum (zh)', '\u4e0d\u662f\u6709\u6548\u7684\u679a\u4e3e\u6210\u5458' in msg, f'got: {msg[:80]}')

# 2. API 404 with help suffix
r = s.put('http://localhost:4000/api/v1/scoreboard/top/10')
msg = r.json().get('message','')
check('API 404+help (zh)', '\u670d\u52a1\u5668\u4e0a\u672a\u627e\u5230' in msg and '\u60a8\u7684\u610f\u601d\u662f' in msg, f'got: {msg[:80]}')

# 3. Non-API 404
r = s.get('http://localhost:4000/nonexistent')
m = re.search(r'<h1[^>]*>(.*?)</h1>', r.text, re.S)
check('Non-API 404 (zh)', m and '\u672a\u627e\u5230\u6587\u4ef6' in m.group(1), f'got: {m.group(1) if m else "?"}')

# 4. API 403 (permission denied)
r = s.post('http://localhost:4000/api/v1/teams', json={})
msg = r.json().get('message','')
check('API 403 (zh)', '\u6ca1\u6709\u6743\u9650' in msg, f'got: {msg[:80]}')

# 5. Marshmallow validation via admin endpoint
r = s.patch('http://localhost:4000/api/v1/challenges/1', json={'value': 'not_a_number'})
data = r.json()
errors = str(data.get('errors', {}))
check('Marshmallow type (zh)', '\u4e0d\u662f\u6709\u6548' in errors or '\u65e0\u6548' in errors or '\u5fc5\u987b' in errors, f'got: {errors[:120]}')

# === English ===
s.cookies.set('language', 'en')
print()
print('=== English (en) ===')

# 6. Pydantic enum
r = s.get('http://localhost:4000/api/v1/users?field=invalid')
data = r.json()
msg = str(data.get('errors', {}).get('field', ''))
check('Pydantic enum (en)', 'value is not a valid enumeration member' in msg, f'got: {msg[:80]}')

# 7. API 404 with help suffix
r = s.put('http://localhost:4000/api/v1/scoreboard/top/10')
msg = r.json().get('message','')
check('API 404+help (en)', 'not found' in msg.lower() and 'did you mean' in msg.lower(), f'got: {msg[:80]}')

# 8. Non-API 404
r = s.get('http://localhost:4000/nonexistent')
m = re.search(r'<h1[^>]*>(.*?)</h1>', r.text, re.S)
check('Non-API 404 (en)', m and 'File not found' in m.group(1), f'got: {m.group(1) if m else "?"}')

# 9. API 403
r = s.post('http://localhost:4000/api/v1/teams', json={})
msg = r.json().get('message','')
check('API 403 (en)', 'permission' in msg.lower() or "don't have" in msg.lower(), f'got: {msg[:80]}')

# 10. Marshmallow validation
r = s.patch('http://localhost:4000/api/v1/challenges/1', json={'value': 'not_a_number'})
data = r.json()
errors = str(data.get('errors', {}))
check('Marshmallow type (en)', 'Not a valid' in errors or 'Invalid' in errors or 'Must be' in errors, f'got: {errors[:120]}')

print()
print(f'=== Results: {passed} passed, {failed} failed ===')
if failed == 0:
    print('ALL TESTS PASSED!')
else:
    print(f'{failed} tests FAILED')
