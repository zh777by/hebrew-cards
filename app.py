import streamlit as st
import json
import random
import time
from pathlib import Path

DATA_FILE = "cards.json"

# -----------------------
# LOAD / SAVE
# -----------------------

def load_cards():
    if not Path(DATA_FILE).exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cards(cards):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

cards = load_cards()

# -----------------------
# SESSION STATE
# -----------------------

if "index" not in st.session_state:
    st.session_state.index = 0

if "show_back" not in st.session_state:
    st.session_state.show_back = False

if "mode" not in st.session_state:
    st.session_state.mode = "study"

# -----------------------
# FILTER MODES
# -----------------------

def get_active_cards():
    if st.session_state.mode == "study":
        return [c for c in cards if not c["learned"]]

    if st.session_state.mode == "favorites":
        return [c for c in cards if c["favorite"]]

    if st.session_state.mode == "all":
        return cards

    return cards

active_cards = get_active_cards()

# -----------------------
# HEADER
# -----------------------

st.title("🇮🇱 Hebrew Cards")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📚 Study"):
        st.session_state.mode = "study"
        st.session_state.index = 0

with col2:
    if st.button("⭐ Favorites"):
        st.session_state.mode = "favorites"
        st.session_state.index = 0

with col3:
    if st.button("📋 All"):
        st.session_state.mode = "all"
        st.session_state.index = 0

st.divider()

# -----------------------
# NO CARDS
# -----------------------

if not active_cards:
    st.warning("Нет карточек в этом режиме")
    st.stop()

# -----------------------
# CARD SELECTION (SPACED REPETITION)
# -----------------------

def pick_card(cards):
    now = time.time()

    # вес = меньше score → чаще показывать
    weights = []
    for c in cards:
        score = c.get("score", 0)
        last = c.get("last_seen", 0)

        delay_bonus = (now - last) / 10000
        weight = max(1, 5 - score + delay_bonus)

        weights.append(weight)

    return random.choices(cards, weights=weights, k=1)[0]

card = pick_card(active_cards)

# -----------------------
# CARD UI
# -----------------------

st.subheader("Карточка")

if not st.session_state.show_back:
    if st.button(card["front"], use_container_width=True):
        st.session_state.show_back = True
        st.rerun()

else:
    st.image(card["image"], use_container_width=True)

    col1, col2, col3 = st.columns(3)

    # ❌ Не знаю
    with col1:
        if st.button("❌ Again"):
            card["score"] = max(0, card.get("score", 0) - 1)
            card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            st.rerun()

    # 👍 Нормально
    with col2:
        if st.button("👍 Good"):
            card["score"] = card.get("score", 0) + 1
            card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            st.rerun()

    # ✅ Выучено
    with col3:
        if st.button("✅ Learned"):
            card["learned"] = True
            card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            st.rerun()

# -----------------------
# FAVORITE + DELETE
# -----------------------

col1, col2 = st.columns(2)

with col1:
    if st.button("⭐ Toggle Favorite"):
        card["favorite"] = not card.get("favorite", False)
        save_cards(cards)
        st.rerun()

with col2:
    if st.button("🗑 Delete"):
        cards.remove(card)
        save_cards(cards)
        st.session_state.show_back = False
        st.rerun()

st.divider()

# -----------------------
# ADD NEW CARD
# -----------------------

st.subheader("Добавить карточку")

front = st.text_input("Русский перевод")
image_file = st.file_uploader("Скриншот", type=["png", "jpg", "jpeg"])

if st.button("➕ Add Card"):
    if front and image_file:

        img_path = f"images/{image_file.name}"

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

        st.success("Карточка добавлена!")
        st.rerun()