"""Download all Stitch screens and list them"""

import json
import urllib.request
import os

with open(
    r"C:\Users\User\.gemini\antigravity\brain\f6052717-2faa-4b29-ba85-9da55bad376e\.system_generated\steps\1215\output.txt",
    "r",
    encoding="utf-8",
) as f:
    data = json.loads(f.read())

screens = data.get("screens", [])
print(f"Total screens: {len(screens)}\n")

os.makedirs("stitch_downloads", exist_ok=True)

for i, s in enumerate(screens):
    title = s.get("title", "Untitled")
    sid = s["name"].split("/")[-1]
    has_html = bool(s.get("htmlCode", {}).get("downloadUrl"))
    device = s.get("deviceType", "UNKNOWN")
    w = s.get("width", "?")
    h = s.get("height", "?")
    print(f'{i + 1}. [{device}] "{title}" ({w}x{h}) HTML={has_html}')
    print(f"   ID: {sid}")

    if has_html:
        url = s["htmlCode"]["downloadUrl"]
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                html = resp.read().decode("utf-8")
                safe_title = title.replace(" ", "_").replace("/", "_")[:40]
                filename = f"stitch_downloads/{i + 1}_{safe_title}.html"
                with open(filename, "w", encoding="utf-8") as out:
                    out.write(html)
                print(f"   Downloaded: {len(html)} bytes -> {filename}")
                # Show the <title> tag
                if "<title>" in html:
                    t_start = html.index("<title>") + 7
                    t_end = html.index("</title>")
                    print(f"   Page Title: {html[t_start:t_end]}")
        except Exception as e:
            print(f"   ERROR: {e}")
    print()
