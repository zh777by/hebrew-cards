import streamlit as st
import json
import time
from pathlib import Path
import random

# Файл базы данных
DATA_FILE = "cards.json"

# Создаем папку для картинок, если её нет
Path("images").mkdir(exist_ok=True)

# -----------------------
# ЗАГРУЗКА И СОХРАНЕНИЕ
# -----------------------
def load_cards():
    if not Path(DATA_FILE).exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_cards(cards):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

# Загружаем данные при старте
cards = load_cards()

# -----------------------
# СОСТОЯНИЕ СЕССИИ
# -----------------------
if "show_back" not in st.session_state:
    st.session_state.show_back = False
if "mode" not in st.session_state:
    st.session_state.mode = "study"

# -----------------------
# ФИЛЬТРАЦИЯ КАРТОЧЕК
# -----------------------
def get_active_cards():
    if st.session_state.mode == "study":
        return [c for c in cards if not c.get("learned", False)]
    if st.session_state.mode == "favorites":
        return [c for c in cards if c.get("favorite", False)]
    return cards

active_cards = get_active_cards()

# -----------------------
# ИНТЕРФЕЙС (ШАПКА)
# -----------------------
st.title("🇮🇱 Hebrew Cards V2")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📚 Учить", use_container_width=True):
        st.session_state.mode = "study"
        st.session_state.show_back = False
        st.rerun()
with col2:
    if st.button("⭐ Избранное", use_container_width=True):
        st.session_state.mode = "favorites"
        st.session_state.show_back = False
        st.rerun()
with col3:
    if st.button("📋 Все", use_container_width=True):
        st.session_state.mode = "all"
        st.session_state.show_back = False
        st.rerun()

st.divider()

# -----------------------
# ФОРМА ДОБАВЛЕНИЯ (ВСЕГДА ВИДНА)
# -----------------------
with st.expander("➕ Добавить новую карточку", expanded=not active_cards):
    front = st.text_input("Перевод (на русском)")
    image_file = st.file_uploader("Загрузить скриншот", type=["png", "jpg", "jpeg"])

    if st.button("Сохранить карточку"):
        if front and image_file:
            # Сохраняем картинку в папку images
            img_path = f"images/{image_file.name}"
            with open(img_path, "wb") as f:
                f.write(image_file.getbuffer())

            # Создаем структуру карточки
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
            st.success(f"Карточка '{front}' добавлена!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Введите текст и выберите картинку!")

st.divider()

# -----------------------
# ПРОВЕРКА НА ПУСТОТУ
# -----------------------
if not active_cards:
    st.info(f"В режиме '{st.session_state.mode}' пока нет карточек. Добавьте первую карточку выше 👆")
    st.stop()

# -----------------------
# ВЫБОР И ОТОБРАЖЕНИЕ КАРТОЧКИ
# -----------------------
def pick_card(cards_list):
    now = time.time()
    weights = []
    for c in cards_list:
        score = c.get("score", 0)
        last = c.get("last_seen", 0)
        # Чем меньше score и чем дольше не видели, тем выше шанс выпадения
        weight = max(1, 5 - score + (now - last) / 10000)
        weights.append(weight)
    return random.choices(cards_list, weights=weights, k=1)[0]

# Выбираем карточку (сохраняем в session_state, чтобы не прыгала при нажатии кнопок)
if "current_card_id" not in st.session_state or any(c['id'] == st.session_state.current_card_id for c in cards) == False:
    st.session_state.current_card_id = pick_card(active_cards)['id']

# Находим объект текущей карточки
card = next(c for c in cards if c['id'] == st.session_state.current_card_id)

st.subheader(f"Режим: {st.session_state.mode.capitalize()}")

if not st.session_state.show_back:
    # РУБАШКА КАРТОЧКИ
    if st.button(f"👁 Показать ответ для: {card['front']}", use_container_width=True, height=200):
        st.session_state.show_back = True
        st.rerun()
else:
    # ЛИЦЕВАЯ СТОРОНА (КАРТИНКА)
    st.image(card["image"], use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("❌ Плохо", use_container_width=True):
            card["score"] = max(0, card.get("score", 0) - 1)
            card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            del st.session_state.current_card_id
            st.rerun()
    with col_b:
        if st.button("👍 Норм", use_container_width=True):
            card["score"] = card.get("score", 0) + 1
            card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            del st.session_state.current_card_id
            st.rerun()
    with col_c:
        if st.button("✅ Знаю!", use_container_width=True):
            card["learned"] = True
            save_cards(cards)
            st.session_state.show_back = False
            del st.session_state.current_card_id
            st.rerun()

    # Избранное и Удаление
    c_fav, c_del = st.columns(2)
    with c_fav:
        label = "🌟 В избранном" if card.get("favorite") else "⭐ В избранное"
        if st.button(label, use_container_width=True):
            card["favorite"] = not card.get("favorite", False)
            save_cards(cards)
            st.rerun()
    with c_del:
        if st.button("🗑 Удалить", use_container_width=True):
            cards.remove(card)
            save_cards(cards)
            st.session_state.show_back = False
            del st.session_state.current_card_id
            st.rerun()