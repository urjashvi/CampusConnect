import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="CampusConnect", page_icon="🎪", layout="wide")

DB = "campusconnect.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    event_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    description TEXT,
    organizer TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    email TEXT NOT NULL,
    registered_at TEXT NOT NULL,
    UNIQUE(event_id, email)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    meeting_day TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    submitted_at TEXT NOT NULL
)""")

# Add sample content only when the database is empty.
if cur.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
    sample_events = [
        ("CodeSprint 2026", "Technology", "2026-11-18", "Innovation Lab",
         "A friendly 6-hour coding challenge. Bring an idea and build a prototype.", "Tech Society"),
        ("Open Mic Evening", "Arts & Culture", "2026-11-21", "Central Lawn",
         "Music, poetry, comedy and performances by students.", "Cultural Council"),
        ("Green Campus Drive", "Community", "2026-11-24", "Main Gate",
         "Join volunteers for a campus clean-up and tree-planting activity.", "Eco Club"),
        ("Career Launch Workshop", "Career", "2026-11-28", "Seminar Hall 2",
         "Resume basics, interview practice and career Q&A with alumni.", "Placement Cell"),
    ]
    cur.executemany("""INSERT INTO events
        (title, category, event_date, venue, description, organizer)
        VALUES (?, ?, ?, ?, ?, ?)""", sample_events)

if cur.execute("SELECT COUNT(*) FROM clubs").fetchone()[0] == 0:
    sample_clubs = [
        ("Tech Society", "Technology", "Build projects, explore new tools and take part in hackathons.", "Wednesday"),
        ("Frame by Frame", "Arts & Culture", "A creative space for photography, film and visual storytelling.", "Friday"),
        ("Eco Club", "Community", "Campus sustainability, recycling and environmental volunteering.", "Saturday"),
        ("Entrepreneurship Cell", "Career", "Turn ideas into ventures through talks, mentoring and pitch events.", "Tuesday"),
    ]
    cur.executemany("INSERT INTO clubs (name, category, description, meeting_day) VALUES (?, ?, ?, ?)", sample_clubs)

conn.commit()

st.markdown("""
<style>
.stApp {background: #F6F7FB;}
[data-testid="stSidebar"] {background: #18243B;}
[data-testid="stSidebar"] * {color: #FFFFFF;}
.hero {padding: 25px 28px; border-radius: 18px; color: white;
       background: linear-gradient(115deg,#263F73,#6B55A5);}
.hero h1 {color:white; margin-bottom:5px;}
.small-muted {color:#68738A; font-size:0.9rem;}
div[data-testid="stMetric"] {background:white; padding:15px; border-radius:14px;
border:1px solid #E6EAF2;}
</style>
""", unsafe_allow_html=True)

def read_df(query, params=()):
    return pd.read_sql_query(query, conn, params=params)

st.sidebar.title("🎪 CampusConnect")
st.sidebar.caption("Find your people. Join your campus.")
page = st.sidebar.radio("Explore", [
    "🏠 Discover",
    "🗓️ Events",
    "🎟️ Register",
    "🤝 Clubs & Societies",
    "💬 Feedback",
    "➕ Add an Event"
])
st.sidebar.markdown("---")
st.sidebar.caption("A student community hub")

if page == "🏠 Discover":
    events = read_df("SELECT * FROM events ORDER BY event_date")
    clubs = read_df("SELECT * FROM clubs")
    regs = read_df("SELECT * FROM registrations")
    st.markdown("""
    <div class="hero">
      <h1>Campus life starts here.</h1>
      <div>Discover events, meet communities and make the most of your campus.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    a, b, c = st.columns(3)
    a.metric("Upcoming events", len(events[events["event_date"] >= str(date.today())]) if not events.empty else 0)
    b.metric("Student clubs", len(clubs))
    c.metric("Registrations", len(regs))
    st.subheader("✨ Coming up")
    upcoming = events[events["event_date"] >= str(date.today())].head(3)
    if upcoming.empty:
        st.info("No upcoming events listed yet. Check back soon.")
    for _, e in upcoming.iterrows():
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(e["title"])
            left.write(e["description"])
            left.caption(f'{e["category"]}  •  {e["event_date"]}  •  {e["venue"]}')
            right.write("**Organised by**")
            right.write(e["organizer"])
    st.subheader("🌱 Find a community")
    if not clubs.empty:
        cols = st.columns(2)
        for i, (_, club) in enumerate(clubs.head(4).iterrows()):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{club['name']}**")
                    st.caption(f"{club['category']} • Meets {club['meeting_day']}")
                    st.write(club["description"])

elif page == "🗓️ Events":
    st.title("🗓️ Event Explorer")
    events = read_df("SELECT * FROM events ORDER BY event_date")
    if events.empty:
        st.info("There are no events yet.")
    else:
        categories = ["All"] + sorted(events["category"].dropna().unique().tolist())
        chosen = st.selectbox("Filter by category", categories)
        if chosen != "All":
            events = events[events["category"] == chosen]
        for _, e in events.iterrows():
            with st.container(border=True):
                st.subheader(e["title"])
                st.write(e["description"])
                st.write(f"**Date:** {e['event_date']}  |  **Venue:** {e['venue']}")
                st.caption(f"{e['category']} • Organiser: {e['organizer']}")

elif page == "🎟️ Register":
    st.title("🎟️ Event Registration")
    events = read_df("SELECT id, title, event_date, venue FROM events ORDER BY event_date")
    if events.empty:
        st.info("No events available for registration.")
    else:
        labels = {f"{r['title']} — {r['event_date']}": int(r['id']) for _, r in events.iterrows()}
        with st.form("registration_form"):
            selected = st.selectbox("Choose an event", list(labels.keys()))
            student = st.text_input("Your name")
            email = st.text_input("Email address")
            submitted = st.form_submit_button("Register for event")
        if submitted:
            if not student.strip() or "@" not in email or "." not in email:
                st.error("Enter your name and a valid email address.")
            else:
                try:
                    cur.execute("""INSERT INTO registrations
                        (event_id, student_name, email, registered_at)
                        VALUES (?, ?, ?, ?)""",
                        (labels[selected], student.strip(), email.strip().lower(), datetime.now().isoformat(timespec="seconds")))
                    conn.commit()
                    st.success("You're registered! See you there 🎉")
                except sqlite3.IntegrityError:
                    st.warning("This email is already registered for that event.")

elif page == "🤝 Clubs & Societies":
    st.title("🤝 Clubs & Societies")
    clubs = read_df("SELECT * FROM clubs ORDER BY name")
    for _, club in clubs.iterrows():
        with st.container(border=True):
            st.subheader(club["name"])
            st.caption(f"{club['category']} • Regular meet-up: {club['meeting_day']}")
            st.write(club["description"])
    st.markdown("---")
    st.subheader("Suggest a new club")
    with st.form("club_form"):
        name = st.text_input("Club name")
        category = st.selectbox("Category", ["Technology", "Arts & Culture", "Sports", "Community", "Career", "Other"])
        desc = st.text_area("What is this club about?")
        day = st.selectbox("Preferred meeting day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        send = st.form_submit_button("Submit club suggestion")
    if send:
        if name.strip() and desc.strip():
            try:
                cur.execute("INSERT INTO clubs (name, category, description, meeting_day) VALUES (?, ?, ?, ?)",
                            (name.strip(), category, desc.strip(), day))
                conn.commit()
                st.success("Club suggestion added!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("A club with that name already exists.")
        else:
            st.error("Please enter a club name and description.")

elif page == "💬 Feedback":
    st.title("💬 Event Feedback")
    with st.form("feedback_form"):
        event_name = st.text_input("Event name")
        rating = st.slider("How was the event?", 1, 5, 4)
        comment = st.text_area("Your feedback")
        send = st.form_submit_button("Send feedback")
    if send:
        if event_name.strip():
            cur.execute("INSERT INTO feedback (event_name, rating, comment, submitted_at) VALUES (?, ?, ?, ?)",
                        (event_name.strip(), rating, comment.strip(), datetime.now().isoformat(timespec="seconds")))
            conn.commit()
            st.success("Thanks for helping improve campus events!")
        else:
            st.error("Please enter the event name.")
    feedback = read_df("SELECT event_name, rating, comment, submitted_at FROM feedback ORDER BY id DESC")
    if not feedback.empty:
        st.subheader("Recent feedback")
        st.dataframe(feedback, use_container_width=True, hide_index=True)

elif page == "➕ Add an Event":
    st.title("➕ Add a Campus Event")
    st.write("Are you organising something? Add it to the campus calendar.")
    with st.form("event_form"):
        title = st.text_input("Event title")
        category = st.selectbox("Category", ["Technology", "Arts & Culture", "Sports", "Community", "Career", "Other"])
        event_date = st.date_input("Event date", min_value=date.today())
        venue = st.text_input("Venue")
        organizer = st.text_input("Organiser / club")
        description = st.text_area("Event description")
        submit = st.form_submit_button("Publish event")
    if submit:
        if title.strip() and venue.strip() and organizer.strip() and description.strip():
            cur.execute("""INSERT INTO events
                (title, category, event_date, venue, description, organizer)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (title.strip(), category, str(event_date), venue.strip(), description.strip(), organizer.strip()))
            conn.commit()
            st.success("Your event has been added to CampusConnect!")
        else:
            st.error("Please complete all fields.")

conn.close()
