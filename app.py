import streamlit as st
import json
import time
from pathlib import Path
import random

# --- НАСТРОЙКИ ПУТЕЙ ---
DATA_FILE = "cards.json"
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True) # Создаем папку, если её нет

# --- ФУНКЦИИ ЗАГРУЗКИ И СОХРАНЕНИЯ ---
def load_cards():
    if not Path(DATA_FILE).exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_cards(cards_list):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards_list, f, ensure_ascii=False, indent=2)

# Загружаем базу данных
cards = load_cards()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ (SESSION STATE) ---
if "show_back" not in st.session_state:
    st.session_state.show_back = False
if "mode" not in st.session_state:
    st.session_state.mode = "study"
if "current_card_id" not in st.session_state:
    st.session_state.current_card_id = None

# --- ФИЛЬТРАЦИЯ ---
def get_active_cards():
    if st.session_state.mode == "study":
        return [c for c in cards if not c.get("learned", False)]
    if st.session_state.mode == "favorites":
        return [c for c in cards if c.get("favorite", False)]
    return cards

active_cards = get_active_cards()

# --- ИНТЕРФЕЙС: ЗАГОЛОВОК И МЕНЮ ---
st.title("🇮🇱 Hebrew Cards V2")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📚 Учить", use_container_width=True):
        st.session_state.mode = "study"
        st.session_state.show_back = False
        st.session_state.current_card_id = None
        st.rerun()
with col2:
    if st.button("⭐ Избранное", use_container_width=True):
        st.session_state.mode = "favorites"
        st.session_state.show_back = False
        st.session_state.current_card_id = None
        st.rerun()
with col3:
    if st.button("📋 Все", use_container_width=True):
        st.session_state.mode = "all"
        st.session_state.show_back = False
        st.session_state.current_card_id = None
        st.rerun()

st.divider()

# --- ФОРМА ДОБАВЛЕНИЯ (ВСЕГДА СВЕРХУ) ---
with st.expander("➕ Добавить новую карточку", expanded=not active_cards):
    front_input = st.text_input("Перевод (на русском)")
    image_file = st.file_uploader("Загрузить скриншот", type=["png", "jpg", "jpeg"])

    if st.button("Сохранить карточку"):
        if front_input and image_file:
            img_path = IMAGE_DIR / image_file.name
            with open(img_path, "wb") as f:
                f.write(image_file.getbuffer())

            new_card = {
                "id": int(time.time() * 1000),
                "front": front_input,
                "image": str(img_path),
                "learned": False,
                "favorite": False,
                "score": 0,
                "last_seen": 0
            }
            cards.append(new_card)
            save_cards(cards)
            st.success(f"Карточка '{front_input}' добавлена!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Заполните текст и выберите картинку")

st.divider()

# --- ПРОВЕРКА НА ПУСТОТУ ---
if not active_cards:
    st.info(f"В режиме '{st.session_state.mode}' пока нет карточек. Используйте форму выше 👆")
    st.stop()

# --- ЛОГИКА ВЫБОРА КАРТОЧКИ (УМНОЕ ПОВТОРЕНИЕ) ---
def pick_card(cards_list):
    now = time.time()
    weights = []
    for c in cards_list:
        score = c.get("score", 0)
        last = c.get("last_seen", 0)
        # Вес: чем ниже score и чем дольше не видели, тем выше вероятность
        weight = max(1, 10 - score + (now - last) / 3600)
        weights.append(weight)
    return random.choices(cards_list, weights=weights, k=1)[0]

# Фиксируем карточку в сессии, чтобы она не менялась при каждом клике
if st.session_state.current_card_id is None or not any(c['id'] == st.session_state.current_card_id for c in active_cards):
    chosen = pick_card(active_cards)
    st.session_state.current_card_id = chosen['id']

# Находим объект текущей карточки
current_card = next((c for c in cards if c['id'] == st.session_state.current_card_id), None)

if not current_card:
    st.session_state.current_card_id = None
    st.rerun()

# --- ОТОБРАЖЕНИЕ КАРТОЧКИ ---
st.subheader(f"Режим: {st.session_state.mode}")

if not st.session_state.show_back:
    # Сторона с текстом
    if st.button(f"👁 {current_card['front']}\n\n(Нажми, чтобы увидеть ответ)", use_container_width=True):
        st.session_state.show_back = True
        st.rerun()
else:
    # Сторона с картинкой
    st.image(current_card["image"], use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("❌ Снова", use_container_width=True):
            current_card["score"] = max(0, current_card.get("score", 0) - 1)
            current_card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            st.session_state.current_card_id = None
            st.rerun()
    with col_b:
        if st.button("👍 Хорошо", use_container_width=True):
            current_card["score"] = current_card.get("score", 0) + 1
            current_card["last_seen"] = time.time()
            save_cards(cards)
            st.session_state.show_back = False
            st.session_state.current_card_id = None
            st.rerun()
    with col_c:
        if st.button("✅ Знаю", use_container_width=True):
            current_card["learned"] = True
            save_cards(cards)
            st.session_state.show_back = False
            st.session_state.current_card_id = None
            st.rerun()

    # Доп. функции
    c_fav, c_del = st.columns(2)
    with c_fav:
        fav_text = "🌟 В избранном" if current_card.get("favorite") else "⭐ В избранное"
        if st.button(fav_text, use_container_width=True):
            current_card["favorite"] = not current_card.get("favorite", False)
            save_cards(cards)
            st.rerun()
    with c_del:
        if st.button("🗑 Удалить", use_container_width=True):
            cards.remove(current_card)
            save_cards(cards)
            st.session_state.current_card_id = None
            st.session_state.show_back = False
            st.rerun()