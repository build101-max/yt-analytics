import requests
import json
import os
from datetime import datetime, timezone

API_KEY    = os.environ["YT_API_KEY"]
CHANNEL_ID = os.environ["YT_CHANNEL_ID"]

def fetch():
    # Channel stats
    url  = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={CHANNEL_ID}&key={API_KEY}"
    res  = requests.get(url).json()
    item = res["items"][0]
    stats   = item["statistics"]
    snippet = item["snippet"]

    subs   = int(stats.get("subscriberCount", 0))
    views  = int(stats.get("viewCount", 0))
    videos = int(stats.get("videoCount", 0))
    hours  = round(views * 0.065)

    # Top 10 videos
    vid_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&maxResults=10&order=viewCount&type=video&key={API_KEY}"
    vids    = requests.get(vid_url).json()
    top_videos = []
    for v in vids.get("items", []):
        vid_id = v["id"].get("videoId", "")
        # Get video stats
        vstats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id={vid_id}&key={API_KEY}"
        vstats     = requests.get(vstats_url).json()
        if vstats.get("items"):
            vs = vstats["items"][0]["statistics"]
            cd = vstats["items"][0]["contentDetails"]
            top_videos.append({
                "id":       vid_id,
                "title":    v["snippet"]["title"],
                "thumb":    v["snippet"]["thumbnails"]["medium"]["url"],
                "views":    int(vs.get("viewCount", 0)),
                "likes":    int(vs.get("likeCount", 0)),
                "comments": int(vs.get("commentCount", 0)),
                "duration": cd.get("duration", ""),
                "published": v["snippet"]["publishedAt"][:10],
                "url":      f"https://youtube.com/watch?v={vid_id}"
            })

    # Load existing data for history
    history = []
    if os.path.exists("data.json"):
        with open("data.json") as f:
            old = json.load(f)
            history = old.get("history", [])

    # Add today's snapshot
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not history or history[-1]["date"] != today:
        history.append({
            "date":   today,
            "views":  views,
            "subs":   subs,
            "videos": videos,
            "hours":  hours,
        })
    history = history[-90:]  # keep last 90 days

    data = {
        "updated":    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "channel":    snippet["title"],
        "subs":       subs,
        "views":      views,
        "videos":     videos,
        "hours":      hours,
        "history":    history,
        "top_videos": top_videos,
    }

    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved stats: {subs} subs, {views} views, {videos} videos")

fetch()
