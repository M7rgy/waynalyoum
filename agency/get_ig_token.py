"""One-time helper: turns a short-lived token from Meta's Graph API Explorer into the NEVER-expiring
Page token + Instagram account ID that GitHub needs. Run on your PC:   python get_ig_token.py
Nothing is saved to disk; copy the two values into GitHub secrets.
"""
import getpass
import json
import urllib.parse
import urllib.request

G = "https://graph.facebook.com/v27.0"


def get(path, **q):
    with urllib.request.urlopen(f"{G}/{path}?{urllib.parse.urlencode(q)}", timeout=30) as r:
        return json.loads(r.read())


app_id = input("App ID: ").strip()
secret = getpass.getpass("App Secret (hidden): ").strip()
short = getpass.getpass("Short-lived user token from Graph API Explorer (hidden): ").strip()

long_user = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app_id,
                client_secret=secret, fb_exchange_token=short)["access_token"]
pages = get("me/accounts", access_token=long_user, fields="id,name,access_token,instagram_business_account")["data"]
if not pages:
    raise SystemExit("No Facebook Pages found. Link @waynalyoum to a Facebook Page first (see guide step 1).")
for i, p in enumerate(pages):
    print(f"[{i}] {p['name']}  ig={p.get('instagram_business_account', {}).get('id', '—')}")
p = pages[int(input("Which page is linked to @waynalyoum? number: ") or 0)] if len(pages) > 1 else pages[0]
ig = p.get("instagram_business_account", {}).get("id")
if not ig:
    raise SystemExit("That Page has no Instagram professional account linked.")
me = get(ig, access_token=p["access_token"], fields="username")
dbg = get("debug_token", input_token=p["access_token"], access_token=f"{app_id}|{secret}")["data"]
print("\nInstagram account:", me.get("username"))
print("Token expires:", "NEVER ✅" if dbg.get("expires_at", 0) == 0 else dbg.get("expires_at"))
print("\nPut these in GitHub > Settings > Secrets and variables > Actions:\n")
print("IG_USER_ID      =", ig)
print("IG_ACCESS_TOKEN =", p["access_token"])
