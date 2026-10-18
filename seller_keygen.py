# Seller tool: customer er HWID নিয়ে lifetime key বানান
# use: python seller_keygen.py <HWID>
import sys
from license_manager import make_key

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Use: python seller_keygen.py <HWID>")
    else:
        hwid = sys.argv[1].strip().upper()
        print(make_key(hwid))
