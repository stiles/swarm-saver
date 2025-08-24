#!/usr/bin/env python3
import os, time, json, csv, math, sys
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError

load_dotenv()
token = os.getenv("FOURSQUARE_TOKEN")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX") or os.getenv("S3_PATH")
AWS_PROFILE = os.getenv("AWS_PROFILE") or os.getenv("MY_PERSONAL_PROFILE") or os.getenv("AWS_DEFAULT_PROFILE")

# tiny config
V = datetime.utcnow().strftime("%Y%m%d")   # version date
LIMIT = 250                                # API max page size
OUT_DIR = Path("data")
NDJSON = OUT_DIR / "checkins.ndjson"
CSV    = OUT_DIR / "checkins.csv"
GEOJSON= OUT_DIR / "checkins.geojson"

def flatten_row(c):
    v = (c.get("venue") or {})
    loc = (v.get("location") or {})
    def iso(ts): 
        return datetime.utcfromtimestamp(ts).isoformat() + "Z" if ts else ""
    return [
        c.get("id", ""),
        iso(c.get("createdAt")),
        v.get("name", ""),
        v.get("id", ""),
        loc.get("lat"), loc.get("lng"),
        loc.get("address", ""), loc.get("city", ""), loc.get("state",""),
        loc.get("country",""),
        c.get("shout",""),
        c.get("visibility",""),
        c.get("type",""),
        c.get("timeZoneOffset","")
    ]

def as_feature(c):
    v = (c.get("venue") or {})
    loc = (v.get("location") or {})
    lat, lng = loc.get("lat"), loc.get("lng")
    if lat is None or lng is None:
        return None
    props = {
        "id": c.get("id"),
        "createdAt": c.get("createdAt"),
        "created_at": datetime.utcfromtimestamp(c["createdAt"]).isoformat()+"Z" if c.get("createdAt") else None,
        "venue_id": v.get("id"),
        "venue_name": v.get("name"),
        "address": loc.get("address"),
        "city": loc.get("city"),
        "state": loc.get("state"),
        "country": loc.get("country"),
        "shout": c.get("shout"),
        "visibility": c.get("visibility"),
        "type": c.get("type"),
    }
    return {"type":"Feature","geometry":{"type":"Point","coordinates":[lng,lat]},"properties":props}

def upload_to_s3(paths):
    if not S3_BUCKET:
        return
    try:
        session = boto3.session.Session(profile_name=AWS_PROFILE) if AWS_PROFILE else boto3.session.Session()
        s3 = session.client("s3")
        for p in paths:
            name = p.name
            key = f"{S3_PREFIX.rstrip('/')}/{name}" if S3_PREFIX else name
            ct = (
                "application/x-ndjson" if name.endswith(".ndjson") else
                "application/geo+json" if name.endswith(".geojson") else
                "text/csv" if name.endswith(".csv") else
                "application/octet-stream"
            )
            s3.upload_file(str(p), S3_BUCKET, key, ExtraArgs={"ContentType": ct})
            print(f"Uploaded s3://{S3_BUCKET}/{key}")
    except (BotoCoreError, ClientError) as e:
        print(f"S3 upload failed: {e}")
        return

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    base = "https://api.foursquare.com/v2/users/self/checkins"

    # discover total
    r = s.get(base, params={"v": V, "limit": 1, "offset": 0}, timeout=30)
    r.raise_for_status()
    total = r.json().get("response", {}).get("checkins", {}).get("count", 0)
    if total == 0:
        print("No check-ins found")
        return
    pages = math.ceil(total / LIMIT)
    print(f"Found {total} check-ins across ~{pages} pages")

    # open outputs
    ndj = NDJSON.open("w", encoding="utf-8")
    csvf = CSV.open("w", newline="", encoding="utf-8")
    writer = csv.writer(csvf)
    writer.writerow([
        "id","created_at","venue_name","venue_id",
        "lat","lng","address","city","state","country",
        "shout","visibility","type","tz_offset"
    ])
    features = []

    fetched = 0
    offset = 0
    while fetched < total:
        params = {"v": V, "limit": LIMIT, "offset": offset}
        rr = s.get(base, params=params, timeout=30)
        rr.raise_for_status()
        data = rr.json()
        items = data.get("response", {}).get("checkins", {}).get("items", []) or []
        if not items:
            break

        for c in items:
            # raw
            ndj.write(json.dumps(c, ensure_ascii=False) + "\n")
            # csv
            writer.writerow(flatten_row(c))
            # geojson
            feat = as_feature(c)
            if feat: features.append(feat)

        fetched += len(items)
        offset += len(items)
        print(f"{fetched}/{total}")
        time.sleep(0.2)  # gentle on rate limits

    ndj.close(); csvf.close()

    # write geojson last
    with GEOJSON.open("w", encoding="utf-8") as gj:
        json.dump({"type":"FeatureCollection","features":features}, gj, ensure_ascii=False)

    print(f"Done → {NDJSON}, {CSV}, {GEOJSON}")
    upload_to_s3([NDJSON, CSV, GEOJSON])

if __name__ == "__main__":
    main()