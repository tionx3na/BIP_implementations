import os
import binascii
import hashlib
import unicodedata
import hmac
import struct
import ecdsa
from base58 import b58encode
from ecdsa.curves import SECP256k1
from ecdsa.ecdsa import int_to_string, string_to_int

bits = 256
print("Bytes = " + str(bits//8))
ent = os.urandom(bits//8)
ent_hex = binascii.hexlify(ent)
decoded = ent_hex.decode("utf-8")
ent_bin = binascii.unhexlify(str(decoded)) #random in bin
ent_hex = binascii.hexlify(ent_bin) #random in hex
bytes = len(ent_bin)


hashed_sha256 = hashlib.sha256(ent_bin).hexdigest()

result = (
    bin(int(ent_hex, 16))[2:].zfill(bytes * 8)
    + bin(int(hashed_sha256, 16))[2:].zfill(256)[: bytes * 8 // 32]
)


index_list = []
with open("wordlist.txt", "r", encoding="utf-8") as f:
    for w in f.readlines():
        index_list.append(w.strip())

wordlist = []
for i in range(len(result) // 11):
    #print(result[i*11 : (i+1)*11])
    index = int(result[i*11 : (i+1)*11], 2)
    #print(str(index))
    wordlist.append(index_list[index])

phrase = " ".join(wordlist)
print(phrase)

#TO SEED
normalized_mnemonic = unicodedata.normalize("NFKD", phrase)
password = ""
normalized_passphrase = unicodedata.normalize("NFKD", password)

passphrase = "mnemonic" + normalized_passphrase
mnemonic = normalized_mnemonic.encode("utf-8")
passphrase = passphrase.encode("utf-8")

bin_seed = hashlib.pbkdf2_hmac("sha512", mnemonic, passphrase, 2048)


# BIP-39 seed to BIP-32 Master Root Key

seed = binascii.hexlify(bin_seed[:64])
# seed = binascii.unhexlify("000102030405060708090a0b0c0d0e0f")
decoded_seed = seed.decode("utf-8")
final_seed = binascii.unhexlify(decoded_seed)
print(decoded_seed)
I = hmac.new(b"Bitcoin seed", final_seed, hashlib.sha512).digest()
Il, Ir = I[:32], I[32:]

secret = Il
chain = Ir

xprv = binascii.unhexlify("0488ade4")
xpub = binascii.unhexlify("0488b21e")
depth = b"\x00"
fpr = b'\0\0\0\0'
index = 0
child = struct.pack('>L', index) 

k_priv = ecdsa.SigningKey.from_string(secret, curve=SECP256k1)
K_priv = k_priv.get_verifying_key()

data_priv = b'\x00' + (k_priv.to_string())  # ser256(p): serializes integer p as a 32-byte sequence

# serialization the coordinate pair P = (x,y) as a byte sequence using SEC1's compressed form
if K_priv.pubkey.point.y() & 1:
    data_pub= b'\3'+int_to_string(K_priv.pubkey.point.x())
else:
    data_pub = b'\2'+int_to_string(K_priv.pubkey.point.x())

raw_priv = xprv + depth + fpr + child + chain + data_priv
raw_pub = xpub + depth + fpr + child + chain + data_pub

# Double hash using SHA256
hashed_xprv = hashlib.sha256(raw_priv).digest()
hashed_xprv = hashlib.sha256(hashed_xprv).digest()
hashed_xpub = hashlib.sha256(raw_pub).digest()
hashed_xpub = hashlib.sha256(hashed_xpub).digest()

# Append 4 bytes of checksum
raw_priv += hashed_xprv[:4]
raw_pub += hashed_xpub[:4]

# Return base58
print(b58encode(raw_priv))
print(b58encode(raw_pub))