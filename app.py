import streamlit as st
import json
import os
import time
import random
import requests
import base64
import pandas as pd
import plotly.express as px
from PIL import Image

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Hebrew Cards",
    page_icon="🇮🇱",
    layout="centered"
)

# session safety
if "show_image" not in st.session_state:
    st.session_state.show_image = False

if "current_card" not in st.session_state:
    st.session_state.current_card = None

# =====================================================
# PWA SUPPORT
# =====================================================
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/service-worker.js');
}
</script>
""", unsafe_allow_html=True)

# =====================================================
# PATHS
# =====================================================
DATA_FILE = "cards.json"
IMAGE_DIR = "images"

os.makedirs(IMAGE_DIR, exist_ok=True)

# =====================================================
# SM-2 ALGORITHM (ANKI)
# =====================================================
def update_sm2(card, quality):

    card.setdefault("repetitions", 0)
    card.setdefault("interval", 0)
    card.setdefault("ease", 2.5)

    if quality >= 3:
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card["ease"])

        card["repetitions"] += 1
    else:
        card["repetitions"] = 0
        card["interval"] = 1

    card["ease"] += (0.1 - (5-quality)*(0.08+(5-quality)*0.02))
    card["ease"] = max(1.3, card["ease"])

    card["due_date"] = time.time() + card["interval"] * 86400
    return card


# =====================================================
# DATA LOAD/SAVE
# =====================================================
def load_cards():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def github_backup(cards):

    if "GITHUB_TOKEN" not in st.secrets:
        return

    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]

        url = f"https://api.github.com/repos/{repo}/contents/cards.json"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        # get SHA
        r = requests.get(url, headers=headers)
        sha = r.json()["sha"] if r.status_code == 200 else None

        content = base64.b64encode(
            json.dumps(cards, ensure_ascii=False, indent=2).encode()
        ).decode()

        payload = {
            "message": "Auto backup from Streamlit",
            "content": content,
            "sha": sha
        }

        res = requests.put(url, headers=headers, json=payload)

        if res.status_code in (200, 201):
            st.toast("☁️ Backup saved to GitHub")
        else:
            st.error(f"Backup failed ({res.status_code})")
            st.write(res.text)

    except Exception as e:
        st.error(f"GitHub error: {e}")


def save_cards(cards):

    # local save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    # cloud backup
    github_backup(cards)


# =====================================================
# ANALYTICS
# =====================================================
def show_analytics(cards):

    if not cards:
        return

    st.divider()
    st.subheader("📈 Learning Analytics")

    df = pd.DataFrame(cards)

    if "repetitions" in df.columns:
        fig = px.pie(df, names="repetitions",
                     title="Learning Levels")
        st.plotly_chart(fig, use_container_width=True)

    now = time.time()
    due_today = sum(1 for c in cards if c.get("due_date", 0) <= now)

    st.metric("Cards due today", due_today)


# =====================================================
# LOAD DATA
# =====================================================
cards = load_cards()

# =====================================================
# SIDEBAR — ADD CARD
# =====================================================
st.sidebar.header("➕ Add Card")

front = st.sidebar.text_input("Russian translation")
image_file = st.sidebar.file_uploader(
    "Upload screenshot",
    type=["png", "jpg", "jpeg"]
)

if st.sidebar.button("Add Card"):

    if front and image_file:

        filename = f"{int(time.time())}_{image_file.name}"
        img_path = os.path.join(IMAGE_DIR, filename)

        with open(img_path, "wb") as f:
            f.write(image_file.getbuffer())

        new_card = {
            "id": int(time.time()),
            "front": front,
            "image": img_path,
            "repetitions": 0,
            "interval": 0,
            "ease": 2.5,
            "due_date": 0,
            "favorite": False
        }

        cards.append(new_card)
        save_cards(cards)

        st.sidebar.success("✅ Card added!")
        st.rerun()

# =====================================================
# MAIN ENGINE
# =====================================================
st.title("🇮🇱 Hebrew Flashcards")

if not cards:
    st.info("Add your first card in the sidebar 👈")
    st.stop()

now = time.time()
due_cards = [c for c in cards if c.get("due_date", 0) <= now]

if st.session_state.current_card is None:
    if due_cards:
        st.session_state.current_card = random.choice(due_cards)
    else:
        st.success("🎉 Nothing to review today!")
        show_analytics(cards)
        st.stop()

card = st.session_state.current_card

# =====================================================
# CARD DISPLAY
# =====================================================
st.subheader("Tap to reveal")

if st.button(card.get("front", "No text"), use_container_width=True):
    st.session_state.show_image = True

if st.session_state.show_image:

    try:
        st.image(Image.open(card["image"]), use_container_width=True)
    except:
        st.error("Image not found")

    col1, col2, col3 = st.columns(3)

    if col1.button("❌ Again"):
        update_sm2(card, 2)
        save_cards(cards)
        st.session_state.show_image = False
        st.session_state.current_card = None
        st.rerun()

    if col2.button("⭐ Favorite"):
        card["favorite"] = not card.get("favorite", False)
        save_cards(cards)
        st.rerun()

    if col3.button("✅ Good"):
        update_sm2(card, 5)
        save_cards(cards)
        st.session_state.show_image = False
        st.session_state.current_card = None
        st.rerun()

# =====================================================
# CARD LIST
# =====================================================
with st.expander("📚 All cards"):

    for c in cards:

        cols = st.columns([4, 1])

        status = "🔴" if c.get("due_date", 0) <= now else "⏱️"
        cols[0].write(f"{c.get('front','')} {status}")

        if cols[1].button("🗑️", key=f"del_{c['id']}"):
            cards = [x for x in cards if x["id"] != c["id"]]
            save_cards(cards)
            st.rerun()

# =====================================================
# ANALYTICS FOOTER
# =====================================================
show_analytics(cards)