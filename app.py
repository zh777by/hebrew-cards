import streamlit as st
import json
import os
import time
import random
from PIL import Image

# ===============================
# PAGE CONFIG + PWA SUPPORT
# ===============================

st.set_page_config(
    page_title="Hebrew Cards",
    page_icon="🇮🇱",
    layout="centered"
)

# PWA connection
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#ffffff">

<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js');
}
</script>
""", unsafe_allow_html=True)


# ===============================
# FILE PATHS
# ===============================

DATA_FILE = "cards.json"
IMAGE_DIR = "images"

# auto-create folders/files
os.makedirs(IMAGE_DIR, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


# ===============================
# DATA FUNCTIONS
# ===============================

def load_cards():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


import requests
import base64

def save_cards(cards):

    # --- save locally ---
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

    # --- backup to GitHub ---
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]

        url = f"https://api.github.com/repos/{repo}/contents/cards.json"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        # get current file sha
        r = requests.get(url, headers=headers)

        sha = None
        if r.status_code == 200:
            sha = r.json()["sha"]

        content = base64.b64encode(
            json.dumps(cards, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("utf-8")

        data = {
            "message": "Auto backup cards",
            "content": content,
            "sha": sha
        }

        requests.put(url, headers=headers, json=data)

    except Exception as e:
        print("GitHub backup failed:", e)


cards = load_cards()


# ===============================
# SIDEBAR — ADD CARD
# ===============================

st.sidebar.header("➕ Add New Card")

front = st.sidebar.text_input("Russian translation")
image_file = st.sidebar.file_uploader(
    "Upload screenshot",
    type=["png", "jpg", "jpeg"]
)

if st.sidebar.button("Add Card"):

    if front and image_file:

        try:
            filename = f"{int(time.time())}_{image_file.name}"
            img_path = os.path.join(IMAGE_DIR, filename)

            with open(img_path, "wb") as f:
                f.write(image_file.getbuffer())

            new_card = {
                "id": int(time.time()),
                "front": front,
                "image": img_path,
                "learned": False,
                "favorite": False,
                "score": 0,
                "last_seen": 0
            }

            cards.append(new_card)
            save_cards(cards)

            st.sidebar.success("✅ Card added!")
            st.rerun()

        except Exception as e:
            st.sidebar.error(e)

    else:
        st.sidebar.warning("Fill text and image")


# ===============================
# MAIN TITLE
# ===============================

st.title("🇮🇱 Hebrew Flashcards")


if not cards:
    st.info("No cards yet. Add your first one 👈")
    st.stop()


# ===============================
# RANDOM CARD ENGINE
# ===============================

if "current_card" not in st.session_state:
    st.session_state.current_card = random.choice(cards)

card = st.session_state.current_card


# ===============================
# CARD DISPLAY
# ===============================

st.subheader("Tap to reveal")

if "show_image" not in st.session_state:
    st.session_state.show_image = False


if st.button(card.get("front", "No text")):
    st.session_state.show_image = True


if st.session_state.show_image:

    try:
        img = Image.open(card["image"])
        st.image(img, use_container_width=True)
    except:
        st.error("Image not found")

    col1, col2, col3 = st.columns(3)

    # learned
    if col1.button("✅ Learned"):
        for c in cards:
            if c["id"] == card["id"]:
                c["learned"] = True
        save_cards(cards)
        st.session_state.show_image = False
        st.session_state.current_card = random.choice(cards)
        st.rerun()

    # favorite
    if col2.button("⭐ Favorite"):
        for c in cards:
            if c["id"] == card["id"]:
                c["favorite"] = not c.get("favorite", False)
        save_cards(cards)
        st.rerun()

    # next
    if col3.button("➡ Next"):
        st.session_state.show_image = False
        st.session_state.current_card = random.choice(cards)
        st.rerun()


# ===============================
# CARD LIST
# ===============================

st.divider()
st.subheader("📚 All Cards")

for c in cards:

    cols = st.columns([4,1])

    status = "✅" if c.get("learned") else ""
    fav = "⭐" if c.get("favorite") else ""

    cols[0].write(f"{c.get('front','')} {status} {fav}")

    if cols[1].button("Delete", key=c["id"]):
        cards = [x for x in cards if x["id"] != c["id"]]
        save_cards(cards)
        st.rerun()