"""Başka bir profesyonel Instagram hesabının HERKESE AÇIK verilerini okur (Business Discovery). Hiçbir şey paylaşmaz."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import publisher as P  # noqa: E402

ad = sys.argv[1].strip().lstrip("@")
t = os.environ["IG_ACCESS_TOKEN"]
m = P.detect_mode(t)
uid = P.resolve_user_id(t, m)
alanlar = ("username,name,biography,website,followers_count,follows_count,media_count,"
           "media.limit(60){caption,like_count,comments_count,timestamp,media_type,media_product_type,permalink}")
r = P._request("GET", f"https://{P._host(m)}/{P.API_VERSION}/{uid}",
               {"fields": f"business_discovery.username({ad}){{{alanlar}}}", "access_token": t})
print("=====RAKIP_BASLA=====")
print(json.dumps(r.get("business_discovery", r), ensure_ascii=False))
print("=====RAKIP_BITTI=====")
