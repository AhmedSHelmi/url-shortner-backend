import hashlib

def generate_url(url):
    return str(hashlib.md5(str(url).encode('utf-8')).hexdigest())
    