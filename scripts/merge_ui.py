import re

# Read the finalizing design from Stitch
with open('dashboard_ui_snapshot/dashboard_finalized.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Jinja extends or make it standalone? 
# We'll make it standalone since it introduces Tailwind which breaks the existing Bootstrap base.html
# We need to add session checks and flash messages.

head_additions = """
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
"""
html = html.replace('</head>', head_additions + '</head>')

# Ensure user is checked
body_start = """<body class="flex min-h-screen">
{% if not session.user_email %}
    <script>window.location.href = "{{ url_for('auth.login') }}";</script>
{% endif %}
"""
html = html.replace('<body class="flex min-h-screen">', body_start)


# 2. Fix Sidebar Links and Modules
# Allowed: Dashboard, Raise Complaint, Track Complaint, Feedback, Placement, Timetable, Lab Status. 
sidebar_html = """
<nav class="space-y-1">
    <a class="sidebar-item sidebar-item-active" href="{{ url_for('student.dashboard') }}">
        <span class="material-symbols-outlined text-[20px]">dashboard</span> Dashboard
    </a>
    <a class="sidebar-item" href="{{ url_for('student.raise_complaint') }}">
        <span class="material-symbols-outlined text-[20px]">report_problem</span> Raise Complaint
    </a>
    <a class="sidebar-item" href="{{ url_for('student.track_complaint') }}">
        <span class="material-symbols-outlined text-[20px]">my_location</span> Track Complaint
    </a>
    <a class="sidebar-item" href="{{ url_for('student.academic_feedback') }}">
        <span class="material-symbols-outlined text-[20px]">rate_review</span> Feedback
    </a>
    <a class="sidebar-item" href="{{ url_for('student.placement_index') }}">
        <span class="material-symbols-outlined text-[20px]">rocket</span> Placement
    </a>
    {% if session.get('role') == 'student' %}
    <a class="sidebar-item" href="{{ url_for('student.student_timetable') }}">
        <span class="material-symbols-outlined text-[20px]">calendar_month</span> Timetable
    </a>
    <a class="sidebar-item" href="{{ url_for('student.lab_index') }}">
        <span class="material-symbols-outlined text-[20px]">science</span> Lab Status
    </a>
    {% endif %}
</nav>
"""

# Replace the two nav areas in the original HTML with this one, removing the Support one.
html = re.sub(r'<div class="px-4 mb-4">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-widest mb-2 px-2">Main Menu</p>\s*<nav class="space-y-1">.*?</nav>\s*</div>', 
              f'<div class="px-4 mb-4"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-2">Main Menu</p>{sidebar_html}</div>', html, flags=re.DOTALL)

html = re.sub(r'<div class="px-4 mb-4">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-widest mb-2 px-2">Support</p>\s*<nav class="space-y-1">.*?</nav>\s*</div>', '', html, flags=re.DOTALL)

# User Profile Area in Sidebar
html = html.replace('Demo User', "{{ session.user_email.split('@')[0] }}")
html = html.replace('S-82910-24', 'Student ID Hidden')
html = re.sub(r'<button class="text-slate-400 hover:text-slate-600">\s*<span class="material-symbols-outlined text-sm">logout</span>\s*</button>',
              '<a href="{{ url_for(\'auth.logout\') }}" class="text-rose-400 hover:text-rose-600 ml-auto"><span class="material-symbols-outlined text-sm">logout</span></a>', html)

# Top Navbar fixes
html = html.replace('<div class="absolute top-2 right-2 h-2 w-2 bg-indigo-600 rounded-full"></div>',
                    '{% if notifications and notifications|length > 0 %}<div class="absolute top-2 right-2 h-2 w-2 bg-indigo-600 rounded-full"></div>{% endif %}')

# Flash messages block
flash_messages = """
    <div class="px-8 pt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="p-4 mb-4 text-sm rounded-lg {% if category == 'error' %}bg-rose-50 text-rose-800{% else %}bg-emerald-50 text-emerald-800{% endif %}" role="alert">
                    <span class="font-medium">{{ message }}</span>
                </div>
            {% endfor %}
        {% endif %}
        {% endwith %}
    </div>
"""
html = html.replace('<main class="p-8 max-w-7xl mx-auto w-full">', f'<main class="p-8 max-w-7xl mx-auto w-full">{flash_messages}')


# Cards Replacements
html = html.replace('<h3 class="text-xl font-bold">85%</h3>', '<h3 class="text-xl font-bold">{{ overall_attendance_pct|default("0") }}%</h3>')
html = html.replace('style="width: 85%"', 'style="width: {{ overall_attendance_pct|default("0") }}%"') 

html = html.replace('<h3 class="text-xl font-bold">76%</h3>', '<h3 class="text-xl font-bold">{{ avg_marks_pct|default("0") }}%</h3>')
html = html.replace('style="width: 76%"', 'style="width: {{ avg_marks_pct|default("0") }}%"') 

html = html.replace('<h3 class="text-xl font-bold">4</h3>', '<h3 class="text-xl font-bold">{{ attendance_records|length|default("0") }}</h3>')

# Link wrapping for cards by making the entire div clickable
# Note: Do not use raw strings with escaped quotes in re.sub replacement, it leaves literal backslashes
html = re.sub(
    r'<div class="info-card">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-wider">Attendance</p>',
    "<div class=\"info-card\" onclick=\"window.location.href='{{ url_for('student.attendance_overview') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-slate-400 uppercase tracking-wider\">Attendance</p>", html
)
html = re.sub(
    r'<div class="info-card">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-wider">Avg Marks</p>',
    "<div class=\"info-card\" onclick=\"window.location.href='{{ url_for('student.marks_overview') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-slate-400 uppercase tracking-wider\">Avg Marks</p>", html
)
html = re.sub(
    r'<div class="info-card">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-wider">Modules</p>',
    "<div class=\"info-card\" onclick=\"window.location.href='{{ url_for('student.course_plan_overview') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-slate-400 uppercase tracking-wider\">Course Plan</p>", html
)
html = re.sub(
    r'<div class="info-card">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-wider">Placement</p>',
    "<div class=\"info-card\" onclick=\"window.location.href='{{ url_for('student.placement_index') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-slate-400 uppercase tracking-wider\">Placement</p>", html
)
html = re.sub(
    r'<div class="info-card border-indigo-200 bg-indigo-50/30">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-indigo-600 uppercase tracking-wider">Analytics</p>',
    "<div class=\"info-card border-indigo-200 bg-indigo-50/30\" onclick=\"window.location.href='{{ url_for('student.student_progress') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-indigo-600 uppercase tracking-wider\">My Progress</p>", html
)
html = re.sub(
    r'<div class="info-card">\s*<div class="flex items-center justify-between mb-2">\s*<p class="text-\[10px\] font-bold text-slate-400 uppercase tracking-wider">Lab Status</p>',
    "<div class=\"info-card\" onclick=\"window.location.href='{{ url_for('student.lab_index') }}'\">\n<div class=\"flex items-center justify-between mb-2\">\n<p class=\"text-[10px] font-bold text-slate-400 uppercase tracking-wider\">Lab Status</p>", html
)


# Today's Classes Injection (Adding IDs for the JS to bind to)
old_ongoing = """<div class="relative group cursor-pointer">
<div class="absolute -left-1 top-4 bottom-4 w-1 bg-indigo-600 rounded-full"></div>
<div class="p-4 rounded-md border border-slate-100 hover:border-indigo-100 bg-indigo-50/10 hover:bg-indigo-50/30 transition-all">
<div class="flex justify-between items-start mb-2">
<span class="text-[9px] font-black text-indigo-600 uppercase tracking-widest">Ongoing</span>
<span class="text-[10px] font-bold text-slate-400">9:00 - 10:30 AM</span>
</div>
<h4 class="text-sm font-bold text-slate-900 mb-1">Advanced Algorithms</h4>
<div class="flex items-center gap-2 text-xs text-slate-500">
<span class="material-symbols-outlined text-xs">location_on</span>
                                    Room 402 • Dr. A. Smith
                                </div>
</div>
</div>"""

new_ongoing = """
<div id="ongoing-class-content" class="relative group cursor-pointer" style="display:none;">
    <div class="absolute -left-1 top-4 bottom-4 w-1 bg-indigo-600 rounded-full"></div>
    <div class="p-4 rounded-md border border-slate-100 hover:border-indigo-100 bg-indigo-50/10 hover:bg-indigo-50/30 transition-all">
        <div class="flex justify-between items-start mb-2">
            <span class="text-[9px] font-black text-indigo-600 uppercase tracking-widest">Ongoing</span>
            <span id="ongoing-time" class="text-[10px] font-bold text-slate-400">Time</span>
        </div>
        <h4 id="ongoing-subject" class="text-sm font-bold text-slate-900 mb-1">Subject</h4>
        <div class="flex items-center gap-2 text-xs text-slate-500">
            <span class="material-symbols-outlined text-xs">person</span>
            <span id="ongoing-instructor">Instructor</span>
        </div>
    </div>
</div>
<div id="no-ongoing-class">
    <div class="p-4 text-center rounded-md border border-slate-100 bg-slate-50/50">
        <span class="text-xs text-slate-500 font-medium">No active class right now.</span>
    </div>
</div>
"""
html = html.replace(old_ongoing, new_ongoing)

old_next = """<div class="relative group cursor-pointer">
<div class="absolute -left-1 top-4 bottom-4 w-1 bg-slate-300 rounded-full"></div>
<div class="p-4 rounded-md border border-slate-100 hover:border-slate-200 transition-all">
<div class="flex justify-between items-start mb-2">
<span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Next Up</span>
<span class="text-[10px] font-bold text-slate-400">11:00 - 12:30 PM</span>
</div>
<h4 class="text-sm font-bold text-slate-900 mb-1">Computer Networks</h4>
<div class="flex items-center gap-2 text-xs text-slate-500">
<span class="material-symbols-outlined text-xs">science</span>
                                    Lab 02 • Prof. Jenkins
                                </div>
</div>
</div>"""

new_next = """
<div id="next-class-content" class="relative group cursor-pointer" style="display:none;">
    <div class="absolute -left-1 top-4 bottom-4 w-1 bg-emerald-500 rounded-full"></div>
    <div class="p-4 rounded-md border border-slate-100 hover:border-slate-200 transition-all">
        <div class="flex justify-between items-start mb-2">
            <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Next Up</span>
            <span id="next-time" class="text-[10px] font-bold text-slate-400">Time</span>
        </div>
        <h4 id="next-subject" class="text-sm font-bold text-slate-900 mb-1">Subject</h4>
        <div class="flex items-center gap-2 text-xs text-slate-500">
            <span class="material-symbols-outlined text-xs">person</span>
            <span id="next-instructor">Instructor</span>
        </div>
    </div>
</div>
<div id="no-next-class">
    <div class="p-4 text-center rounded-md border border-slate-100 bg-slate-50/50">
        <span class="text-xs text-slate-500 font-medium">Done for the day!</span>
    </div>
</div>
"""
html = html.replace(old_next, new_next)


# Quick Actions Links
html = html.replace('<button class="bg-white p-4', '<a href="#" class="block bg-white p-4')
html = html.replace('</button>', '</a>')

html = html.replace('<p class="font-bold text-[11px] text-slate-900">Raise Complaint</p>\n</a>', '<p class="font-bold text-[11px] text-slate-900">Raise Complaint</p>\n</a>').replace('href="#" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', f'href="{{{{ url_for(\'student.raise_complaint\') }}}}" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', 1)

html = html.replace('<p class="font-bold text-[11px] text-slate-900">Give Feedback</p>\n</a>', '<p class="font-bold text-[11px] text-slate-900">Give Feedback</p>\n</a>').replace('href="#" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', f'href="{{{{ url_for(\'student.academic_feedback\') }}}}" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', 1)

html = html.replace('<p class="font-bold text-[11px] text-slate-900">Track Complaint</p>\n</a>', '<p class="font-bold text-[11px] text-slate-900">Track Complaint</p>\n</a>').replace('href="#" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', f'href="{{{{ url_for(\'student.track_complaint\') }}}}" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', 1)

html = html.replace('<p class="font-bold text-[11px] text-slate-900">Campus Updates</p>\n</a>', '<p class="font-bold text-[11px] text-slate-900">Campus Updates</p>\n</a>').replace('href="#" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', 'href="#updates-section" class="block bg-white p-4 border border-slate-200 rounded-lg shadow-sm hover:border-indigo-500 transition-all group text-left"', 1)


# Tickets Summary
html = html.replace('<span class="block text-xl font-extrabold text-slate-900">18</span>', '<span class="block text-xl font-extrabold text-slate-900">{{ total_complaints }}</span>')
html = html.replace('<span class="text-xs font-bold text-slate-900">13</span>', '<span class="text-xs font-bold text-slate-900">{{ resolved_complaints }}</span>')
html = html.replace('<span class="text-xs font-bold text-slate-900">5</span>', '<span class="text-xs font-bold text-slate-900">{{ pending_complaints }}</span>')


# Latest Updates Section Mapping
updates_feed_wrapper = """<div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="updates-section">
<div class="bg-white p-3 border border-slate-200 rounded-lg shadow-sm flex gap-4 items-center hover:bg-slate-50 cursor-pointer">
<div class="h-10 w-10 rounded bg-indigo-100 flex-shrink-0 flex items-center justify-center text-indigo-600">
<span class="material-symbols-outlined">event</span>
</div>
<div class="min-w-0">
<h4 class="font-bold text-xs text-slate-900 truncate">Campus Tech Symposium</h4>
<p class="text-[10px] text-slate-500 truncate mt-0.5">Registration opens for annual tech meet...</p>
<span class="text-[9px] font-bold text-indigo-600 mt-1 block">REGISTER NOW</span>
</div>
</div>
<div class="bg-white p-3 border border-slate-200 rounded-lg shadow-sm flex gap-4 items-center hover:bg-slate-50 cursor-pointer">
<div class="h-10 w-10 rounded bg-amber-100 flex-shrink-0 flex items-center justify-center text-amber-600">
<span class="material-symbols-outlined">history_edu</span>
</div>
<div class="min-w-0">
<h4 class="font-bold text-xs text-slate-900 truncate">Mid-Term Schedules</h4>
<p class="text-[10px] text-slate-500 truncate mt-0.5">Full examination schedules are now live...</p>
<span class="text-[9px] font-bold text-amber-600 mt-1 block">VIEW PDF</span>
</div>
</div>
</div>"""

updates_feed_jinja = """<div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="updates-section">
{% for update in updates %}
<div class="bg-white p-3 border border-slate-200 rounded-lg shadow-sm flex gap-4 items-center hover:bg-slate-50 cursor-pointer">
    <div class="h-10 w-10 rounded {% if loop.index0 % 2 == 0 %}bg-indigo-100 text-indigo-600{% else %}bg-amber-100 text-amber-600{% endif %} flex-shrink-0 flex items-center justify-center">
        <span class="material-symbols-outlined">notifications</span>
    </div>
    <div class="min-w-0">
        <h4 class="font-bold text-xs text-slate-900 truncate">{{ update.title }}</h4>
        <p class="text-[10px] text-slate-500 truncate mt-0.5">{{ update.content }}</p>
        <span class="text-[9px] font-bold text-slate-400 mt-1 block">{{ update.created_at.split(' ')[0] if ' ' in update.created_at else update.created_at }} | {{ update.category }}</span>
    </div>
</div>
{% else %}
<div class="text-[11px] text-slate-500 p-4">No campus updates available at the moment.</div>
{% endfor %}
</div>"""

html = html.replace('<div class="grid grid-cols-1 md:grid-cols-2 gap-4">', '<div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="updates-section">')
html = html.replace(updates_feed_wrapper, updates_feed_jinja)

# --- RE-INTEGRATE ORIGINAL TIMETABLE ---
# Read the original snapshot to extract the colorful modern-timetable-grid
with open('dashboard_ui_snapshot/dashboard.html', 'r', encoding='utf-8') as f_snap:
    snap_html = f_snap.read()
    
# Extract the timetable section
start_marker = '<div class="table-responsive bg-light bg-opacity-50 rounded-4 p-4 border-0 shadow-sm" style="overflow-x: auto;">'
end_marker = '</table>\n        </div>'
start_idx = snap_html.find(start_marker)
end_idx = snap_html.find(end_marker, start_idx) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    colorful_timetable = snap_html[start_idx:end_idx]
    
    # We want to replace the newly generated bland timetable
    # The bland one starts right after <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50"> ... </div>
    # Actually let's just use regex to find the <div class="overflow-x-auto">...</table>\n</div> inside the Weekly Schedule card
    # It looks like:
    stitch_table_pattern = re.compile(r'<div class="overflow-x-auto">\s*<table class="w-full border-collapse">.*?</table>\s*</div>', re.DOTALL)
    
    colorful_timetable = colorful_timetable.replace('bg-light bg-opacity-50 border-0 shadow-sm', '')
    
    # --- Shrink the table sizing to fit into the sleek Stitch layout ---
    # Shrink padding and text in the CSS
    colorful_timetable = colorful_timetable.replace('border-spacing: 12px;', 'border-spacing: 6px;')
    colorful_timetable = colorful_timetable.replace('min-width: 1000px;', 'min-width: 700px;') # Make it scrollable sooner, takes up less space
    colorful_timetable = colorful_timetable.replace('padding: 14px;', 'padding: 8px;')
    colorful_timetable = colorful_timetable.replace('min-height: 90px;', 'min-height: 60px;')
    colorful_timetable = colorful_timetable.replace('font-size: 0.95rem;', 'font-size: 0.75rem;') # Card titles
    colorful_timetable = colorful_timetable.replace('font-size: 0.75rem;', 'font-size: 0.65rem;') # Card subtitles
    colorful_timetable = colorful_timetable.replace('width: 60px;', 'width: 40px;') # Day col width
    colorful_timetable = colorful_timetable.replace('padding-right: 1.5rem;', 'padding-right: 0.5rem;') # Day col padding
    
    # Shrink the th headers
    colorful_timetable = colorful_timetable.replace('font-size: 0.8rem;', 'font-size: 0.65rem;')
    
    # Wrap it in the expected Stitch padding
    colorful_timetable = f'<div class="p-4">{colorful_timetable}</div>'
    
    html = stitch_table_pattern.sub(colorful_timetable, html)



# Inject JS logic for Today's Classes
js_block = """
<!-- Original Timetable Logic Port -->
<script>
    const scheduleData = {
        1: [ // Monday
            { start: "09:00", end: "10:00", subject: "ADA", instructor: "Dr. Shabana Sultana" },
            { start: "10:00", end: "11:00", subject: "AI", instructor: "Balaji V" },
            { start: "11:00", end: "11:30", subject: "Short Break", instructor: "-" },
            { start: "11:30", end: "12:30", subject: "DBMS", instructor: "Usha K Patil" },
            { start: "12:30", end: "13:30", subject: "DMS/Algebra", instructor: "Dr. M R Rashmi / Dr. Shivaraj Kumar" },
            { start: "13:30", end: "14:30", subject: "Lunch Break", instructor: "-" },
            { start: "14:30", end: "16:30", subject: "Lab (E1: ADA, E2: DBMS, E3: AI)", instructor: "Respective Lab Faculty" },
            { start: "16:30", end: "17:30", subject: "NSS / PE / YOGA", instructor: "Padmini M S / Nanditha V" }
        ],
        2: [ // Tuesday
            { start: "09:00", end: "10:00", subject: "AI", instructor: "Balaji V" },
            { start: "10:00", end: "11:00", subject: "ADA", instructor: "Dr. Shabana Sultana" },
            { start: "11:00", end: "11:30", subject: "Short Break", instructor: "-" },
            { start: "11:30", end: "13:30", subject: "Lab (E2: ADA, E3: DBMS)", instructor: "Respective Lab Faculty" },
            { start: "13:30", end: "14:30", subject: "Lunch Break", instructor: "-" },
            { start: "14:30", end: "16:30", subject: "Lab (E1: AI)", instructor: "Balaji V + MA" }
        ],
        3: [ // Wednesday
            { start: "09:00", end: "10:00", subject: "UHV", instructor: "Sneha S" },
            { start: "10:00", end: "11:00", subject: "DBMS", instructor: "Usha K Patil" },
            { start: "11:00", end: "11:30", subject: "Short Break", instructor: "-" },
            { start: "11:30", end: "12:30", subject: "DMS/Algebra", instructor: "Dr. M R Rashmi / Dr. Shivaraj Kumar" },
            { start: "12:30", end: "13:30", subject: "ADA", instructor: "Dr. Shabana Sultana" },
            { start: "13:30", end: "14:30", subject: "Lunch Break", instructor: "-" },
            { start: "14:30", end: "16:30", subject: "Lab (E2: MERN)", instructor: "Divyashree R + ZF" },
            { start: "16:30", end: "17:30", subject: "NSS / PE / YOGA", instructor: "Padmini M S / Nanditha V" }
        ],
        4: [ // Thursday
            { start: "09:00", end: "11:00", subject: "Lab (E1: DBMS, E2: AI, E3: ADA)", instructor: "Respective Lab Faculty" },
            { start: "11:00", end: "11:30", subject: "Short Break", instructor: "-" },
            { start: "11:30", end: "13:30", subject: "Biology for Engineering", instructor: "-" },
            { start: "13:30", end: "14:30", subject: "Lunch Break", instructor: "-" }
        ],
        5: [ // Friday
            { start: "09:00", end: "10:00", subject: "DBMS", instructor: "Usha K Patil" },
            { start: "10:00", end: "11:00", subject: "AI", instructor: "Balaji V" },
            { start: "11:00", end: "11:30", subject: "Short Break", instructor: "-" },
            { start: "11:30", end: "13:30", subject: "DMS/Algebra", instructor: "Dr. M R Rashmi" },
            { start: "13:30", end: "14:30", subject: "Lunch Break", instructor: "-" },
            { start: "14:30", end: "16:30", subject: "Lab (E1: MERN)", instructor: "Divyashree R + ZF" }
        ]
    };

    function updateClasses() {
        const now = new Date();
        const day = now.getDay();
        const currentMins = now.getHours() * 60 + now.getMinutes();

        const todaysClasses = scheduleData[day] || [];
        let ongoingClass = null;
        let nextClass = null;

        for (let i = 0; i < todaysClasses.length; i++) {
            let c = todaysClasses[i];
            let [startH, startM] = c.start.split(":").map(Number);
            let [endH, endM] = c.end.split(":").map(Number);

            let startTotal = startH * 60 + startM;
            let endTotal = endH * 60 + endM;

            if (currentMins >= startTotal && currentMins < endTotal) {
                ongoingClass = c;
                if (i + 1 < todaysClasses.length) {
                    nextClass = todaysClasses[i + 1];
                }
                break;
            } else if (currentMins < startTotal) {
                if (!nextClass) {
                    nextClass = c;
                }
            }
        }

        function formatTime(timeStr) {
            let [h, m] = timeStr.split(':');
            let hour = parseInt(h);
            let ampm = hour >= 12 ? 'PM' : 'AM';
            hour = hour % 12;
            hour = hour ? hour : 12; 
            return `${hour}:${m} ${ampm}`;
        }

        if (ongoingClass && ongoingClass.instructor !== "-") {
            document.getElementById("ongoing-class-content").style.display = "block";
            document.getElementById("no-ongoing-class").style.display = "none";
            document.getElementById("ongoing-subject").textContent = ongoingClass.subject;
            document.getElementById("ongoing-instructor").textContent = ongoingClass.instructor;
            document.getElementById("ongoing-time").textContent = `${formatTime(ongoingClass.start)} - ${formatTime(ongoingClass.end)}`;
        } else {
            document.getElementById("ongoing-class-content").style.display = "none";
            document.getElementById("no-ongoing-class").style.display = "block";
        }

        if (nextClass && nextClass.instructor !== "-") {
            document.getElementById("next-class-content").style.display = "block";
            document.getElementById("no-next-class").style.display = "none";
            document.getElementById("next-subject").textContent = nextClass.subject;
            document.getElementById("next-instructor").textContent = nextClass.instructor;
            document.getElementById("next-time").textContent = `${formatTime(nextClass.start)} - ${formatTime(nextClass.end)}`;
        } else {
            document.getElementById("next-class-content").style.display = "none";
            document.getElementById("no-next-class").style.display = "block";
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        updateClasses();
        // Update every minute to keep it live
        setInterval(updateClasses, 60000);
    });
</script>
</body>
"""

html = html.replace('</body>', js_block)


# --- Interactive UI Enhancements ---
# Inject hover states, translation animations, and modern scale effects

html = re.sub(r'\.sidebar-item-active\s*\{[^\}]+\}', '.sidebar-item-active {\n            @apply bg-indigo-50 text-indigo-700 border-r-4 border-indigo-600;\n        }', html)
html = re.sub(r'\.sidebar-item\s*\{[^\}]+\}', '.sidebar-item {\n            @apply flex items-center gap-3 px-4 py-2.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 hover:translate-x-1 transition-all duration-300 text-sm font-medium rounded-lg mx-2;\n        }', html)
html = re.sub(r'\.info-card\s*\{[^\}]+\}', '.info-card {\n            @apply bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 hover:-translate-y-1 hover:border-indigo-200 transition-all duration-300 relative overflow-hidden cursor-pointer;\n        }', html)
html = re.sub(r'\.schedule-cell\s*\{[^\}]+\}', '.schedule-cell {\n            @apply border-r border-b border-slate-100 p-1 h-14 min-w-[120px] transition-colors hover:bg-slate-50;\n        }', html)
html = re.sub(r'\.compact-button\s*\{[^\}]+\}', '.compact-button {\n            @apply px-3 py-1.5 bg-indigo-600 text-white rounded-md text-xs font-semibold hover:bg-indigo-700 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 flex items-center gap-1.5;\n        }', html)

# 2. Add Animations to Quick Actions
html = html.replace('hover:border-indigo-500 transition-all group', 'hover:border-indigo-500 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group')
html = html.replace('group-hover:bg-indigo-600', 'group-hover:bg-indigo-600 group-hover:scale-110 group-hover:-rotate-3')

# 3. Add Animations to Updates
html = html.replace('hover:bg-slate-50 cursor-pointer', 'hover:bg-slate-50 hover:shadow-md hover:-translate-y-1 transition-all duration-300 cursor-pointer')

# 4. Add Animations to Timetable Classes
html = html.replace('rounded-sm"', 'rounded-sm hover:scale-105 hover:shadow-md transition-all duration-200 cursor-pointer"')

# 5. Make user profile interactive
html = html.replace('class="bg-slate-50 rounded-lg p-3 flex items-center gap-3"', 'class="bg-slate-50 hover:bg-indigo-50 rounded-lg p-3 flex items-center gap-3 cursor-pointer transition-colors duration-200"')

# Write it out to templates/dashboard.html
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Integration complete!")
