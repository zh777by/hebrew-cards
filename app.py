import streamlit as st
import json
import os
from PIL import Image
import uuid

DATA_FILE = "cards.json"
IMAGE_FOLDER = "images"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------- load cards ----------
def load_cards():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cards(cards):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

cards = load_cards()

# ---------- UI ----------
st.title("📚 Hebrew Flashcards")

menu = st.sidebar.selectbox(
    "Menu",
    ["Study", "Add Card", "All Cards"]
)

# ---------- ADD CARD ----------
if menu == "Add Card":
    st.header("Add new card")

    translation = st.text_input("Russian translation")
    image = st.file_uploader("Upload screenshot", type=["png","jpg","jpeg"])

    if st.button("Save card"):
        if translation and image:
            file_id = str(uuid.uuid4()) + ".png"
            path = os.path.join(IMAGE_FOLDER, file_id)

            with open(path, "wb") as f:
                f.write(image.read())

            cards.append({
                "id": file_id,
                "translation": translation,
                "learned": False
            })

            save_cards(cards)
            st.success("Card added!")

# ---------- STUDY ----------
elif menu == "Study":
    st.header("Study")

    unlearned = [c for c in cards if not c["learned"]]

    if not unlearned:
        st.info("All cards learned!")
    else:
        card = unlearned[0]

        if "show_back" not in st.session_state:
            st.session_state.show_back = False

        if not st.session_state.show_back:
            if st.button(card["translation"]):
                st.session_state.show_back = True
        else:
            img = Image.open(os.path.join(IMAGE_FOLDER, card["id"]))
            st.image(img)

            col1, col2 = st.columns(2)

            if col1.button("✅ Learned"):
                card["learned"] = True
                save_cards(cards)
                st.session_state.show_back = False
                st.rerun()

            if col2.button("↩️ Back"):
                st.session_state.show_back = False
                st.rerun()

# ---------- ALL CARDS ----------
elif menu == "All Cards":
    st.header("All cards")

    for c in cards:
        col1, col2 = st.columns([4,1])

        col1.write(c["translation"])

        if col2.button("Delete", key=c["id"]):
            cards.remove(c)
            save_cards(cards)
            st.rerun()