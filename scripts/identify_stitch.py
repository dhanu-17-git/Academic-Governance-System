"""Identify page types from Stitch downloads - UTF-8 safe"""
import os, re

folder = 'stitch_downloads'
for fname in sorted(os.listdir(folder)):
    path = os.path.join(folder, fname)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    title_match = re.search(r'<title>(.*?)</title>', html)
    title = title_match.group(1) if title_match else 'No title'
    
    markers = []
    for keyword in ['Dashboard', 'Complaint', 'Feedback', 'Placement', 'Timetable', 'Lab', 'Attendance', 'sidebar', 'Track Complaint']:
        if keyword.lower() in html.lower():
            markers.append(keyword)
    
    has_sidebar = 'aside' in html.lower()
    
    with open('stitch_map.txt', 'a', encoding='utf-8') as out:
        out.write(f'File: {fname}\n')
        out.write(f'  Title: {title}\n')
        out.write(f'  Size: {len(html)} bytes\n')
        out.write(f'  Has aside: {has_sidebar}\n')
        out.write(f'  Markers: {", ".join(markers)}\n\n')

print('Done - see stitch_map.txt')
