import streamlit as st
import json
import time
import os
import requests
import base64
import pandas as pd
from github import Github

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Hebrew V3", page_icon="🇮🇱", layout="centered")

# PWA Support & Swipe JS
st.markdown("""
    <link rel="manifest" href="/static/manifest.json">
    <script>
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.register('/static/service-worker.js');
        }
        
        // Перехват жестов для Streamlit
        var startX;
        document.addEventListener('touchstart', e => { startX = e.changedTouches[0].screenX; });
        document.addEventListener('touchend', e => {
            let diffX = e.changedTouches[0].screenX - startX;
            if (Math.abs(diffX) > 100) {
                let direction = diffX > 0 ? 'right' : 'left';
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: direction}, '*');
            }
        });
    </script>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ДАННЫХ ---

def load_data():
    if not os.path.exists("cards.json"):
        return []
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_all(cards):
    # 1. Локальное сохранение
    with open("cards.json", "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    
    # 2. GitHub Backup
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["GITHUB_REPO"]
        g = Github(token)
        repo = g.get_user().get_repo(repo_name.split('/')[-1])
        file = repo.get_contents("cards.json")
        content = json.dumps(cards, ensure_ascii=False, indent=2)
        repo.update_file("cards.json", "Auto-update SM2", content, file.sha, branch="main")
        st.toast("☁️ Синхронизировано с GitHub")
    except Exception as e:
        st.error(f"Ошибка бэкапа: {e}")

# --- АЛГОРИТМ SM-2 (ANKI) ---

def update_sm2(card, quality):
    # quality: 0-2 (не помню), 3-5 (помню)
    if quality >= 3:
        if card.get("repetitions", 0) == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card.get("ease", 2.5))
        card["repetitions"] = card.get("repetitions", 0) + 1
    else:
        card["repetitions"] = 0
        card["interval"] = 1

    card["ease"] = card.get("ease", 2.5) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card["ease"] = max(1.3, card["ease"])
    card["due_date"] = time.time() + (card["interval"] * 86400)
    return card

# --- ИНТЕРФЕЙС ---

def main():
    st.title("Hebrew Learning V3 🧠")
    
    if 'cards' not in st.session_state:
        st.session_state.cards = load_data()
    
    tab1, tab2, tab3 = st.tabs(["Учить", "Добавить", "Аналитика"])

    with tab1:
        now = time.time()
        # Фильтруем те, что пора учить
        due_cards = [c for c in st.session_state.cards if c.get("due_date", 0) <= now]
        
        if not due_cards:
            st.success("🎉 Все карточки выучены на сегодня!")
            if st.button("Повторить всё вне очереди"):
                due_cards = st.session_state.cards
        
        if due_cards:
            card = due_cards[0]
            
            with st.container(border=True):
                st.subheader(card["front"])
                if card.get("image"):
                    st.image(card["image"], use_container_width=True)
                
                show = st.button("Показать перевод", use_container_width=True)
                
                if show:
                    st.divider()
                    st.markdown(f"### {card.get('back', 'Перевод не задан')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("❌ Снова (1д)", use_container_width=True):
                            card = update_sm2(card, 2)
                            save_all(st.session_state.cards)
                            st.rerun()
                    with col2:
                        if st.button("✅ Знаю", use_container_width=True):
                            card = update_sm2(card, 5)
                            save_all(st.session_state.cards)
                            st.rerun()
            
            st.info("💡 На телефоне можно свайпать: Влево — Снова, Вправо — Знаю")

    with tab2:
        st.subheader("Новая карточка")
        new_front = st.text_input("Слово (Иврит)")
        new_back = st.text_input("Перевод")
        uploaded_file = st.file_uploader("Картинка", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Сохранить"):
            img_path = ""
            if uploaded_file:
                img_path = f"images/{int(time.time())}.png"
                with open(img_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            new_card = {
                "id": int(time.time()),
                "front": new_front,
                "back": new_back,
                "image": img_path,
                "ease": 2.5,
                "interval": 0,
                "repetitions": 0,
                "due_date": 0
            }
            st.session_state.cards.append(new_card)
            save_all(st.session_state.cards)
            st.success("Добавлено!")

    with tab3:
        if st.session_state.cards:
            df = pd.DataFrame(st.session_state.cards)
            st.metric("Всего карточек", len(df))
            
            # График интервалов (насколько глубоко слова в памяти)
            st.write("Уровни памяти (интервал в днях):")
            st.bar_chart(df['interval'].value_counts())
            
            if st.button("Очистить все данные"):
                if st.checkbox("Я уверен"):
                    st.session_state.cards = []
                    save_all([])
                    st.rerun()

if __name__ == "__main__":
    # Создаем папку для картинок если нет
    if not os.path.exists("images"):
        os.makedirs("images")
    main()