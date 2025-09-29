import streamlit as st
import pandas as pd
import time
import json
from faker import Faker
from functools import lru_cache
from typing import NamedTuple, Optional, List, Tuple, Callable
import os
import random

# ==============================================================================
# Пути
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
SEED_FILE = os.path.join(DATA_DIR, 'seed.json')


# ==============================================================================
# Стили
# ==============================================================================
def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700&display=swap');

            html, body, [class*="st-"] { 
                font-family: 'Titillium Web', sans-serif; 
            }
            .stApp { 
                background-color: #121212; 
                color: #E0E0E0; 
            }
            header[data-testid="stHeader"] { 
                display: none !important; 
            }
            h1, h2, h3 { 
                color: #FFFFFF; 
            }

            /* Кнопки */
            .stButton>button {
                background-color: #00D2BE;
                color: #121212;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                transition: background-color 0.3s ease;
                width: 100%;
            }
            .stButton>button:hover { 
                background-color: #00A693; 
            }

            /* --- НОВЫЕ СТИЛИ ДЛЯ АНИМИРОВАННОГО МЕНЮ --- */
            /* Стили для кнопок меню в боковой панели */
            div[data-testid="stSidebarNav"] div.stButton > button {
                background-color: transparent;
                color: #E0E0E0;
                border: 2px solid transparent;
                text-align: left;
                font-size: 1.1rem;
                font-weight: 600;
                padding: 12px 20px;
                margin-bottom: 8px;
                border-radius: 10px;
                transition: all 0.3s ease; /* Плавный переход для всех свойств */
            }

            /* Эффект при наведении на кнопку меню */
            div[data-testid="stSidebarNav"] div.stButton > button:hover {
                background-color: rgba(0, 210, 190, 0.1);
                border-left: 4px solid #00D2BE;
                color: #FFFFFF;
                transform: translateX(5px); /* Небольшой сдвиг вправо */
            }

            /* Стиль для активной кнопки меню */
            div[data-testid="stSidebarNav"] div.stButton > button.active-menu-button {
                background-color: rgba(0, 210, 190, 0.2);
                color: #FFFFFF;
                border-left: 4px solid #00D2BE;
                font-weight: 700;
            }

            /* Скрываем стандартную навигацию Streamlit, чтобы наше меню выглядело чище */
            div[data-testid="stSidebarNavItems"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# Модели данных
# ==============================================================================
class CarEra(NamedTuple): id: str; name: str; parent: Optional[str]


class Bolid(NamedTuple): id: str; name: str; team: str; year: int; price: int; era_id: str; tags: List[
    str]; quantity_available: int; image_url: str


class Collector(NamedTuple): id: str; name: str; tier: str


class GarageItem(NamedTuple): bolid_id: str; quantity: int


class Garage(NamedTuple): collector_id: str; items: List[GarageItem]


class PurchaseOrder(NamedTuple): id: str; collector_id: str; items: List[GarageItem]; total_price: int; timestamp: str


# ==============================================================================
# Утилитарные функции
# ==============================================================================
def flatten_eras(eras: Tuple[CarEra, ...], root_id: Optional[str]) -> Tuple[CarEra, ...]:
    flat_list = [];
    recurse_ids = set()

    def recurse(current_id: Optional[str]):
        if current_id in recurse_ids: return
        recurse_ids.add(current_id)
        children = tuple(e for e in eras if e.parent == current_id)
        for child in children: flat_list.append(child); recurse(child.id)

    root_era = next((e for e in eras if e.id == root_id), None)
    if root_era: flat_list.append(root_era)
    recurse(root_id)
    return tuple(flat_list)


def load_seed_data(path: str) -> Tuple:
    with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
    return (tuple(CarEra(**e) for e in data.get('eras', [])),
            tuple(Bolid(**b) for b in data.get('bolids', [])),
            tuple(Collector(**c) for c in data.get('collectors', [])),
            tuple(PurchaseOrder(**o) for o in data.get('purchase_orders', [])))


def add_to_garage(garage: Garage, bolid_id: str, quantity: int) -> Garage:
    new_items = list(g for g in garage.items if g.bolid_id != bolid_id)
    found_item = next((item for item in garage.items if item.bolid_id == bolid_id), None)
    new_quantity = (found_item.quantity if found_item else 0) + quantity
    new_items.append(GarageItem(bolid_id, new_quantity))
    return Garage(garage.collector_id, new_items)


def by_price_range(min_p: int, max_p: int) -> Callable: return lambda b: min_p <= b.price <= max_p


def by_team(team: str) -> Callable: return lambda b: b.team == team


# ==============================================================================
# Генерация данных
# ==============================================================================
def generate_f1_mock_data(seed_path=SEED_FILE):
    fake = Faker('ru_RU')
    with open(seed_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    curated_bolids = [
        # Ferrari
        {"name": "Ferrari 412 T2", "team": "Ferrari", "year": 1995, "era_id": "era_v10_early", "tags": ["V12"],
         "price_range": (2_000_000, 2_500_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Ferrari_412T2_front-left_2016_FOS.jpg/1280px-Ferrari_412T2_front-left_2016_FOS.jpg"},
        {"name": "Ferrari F2004", "team": "Ferrari", "year": 2004, "era_id": "era_v10_late",
         "tags": ["V10", "Чемпионский"], "price_range": (4_500_000, 5_000_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Ferrari_F2004_side_2004_United_States_GP.jpg/1280px-Ferrari_F2004_side_2004_United_States_GP.jpg"},
        {"name": "Ferrari F2007", "team": "Ferrari", "year": 2007, "era_id": "era_v8", "tags": ["V8", "Чемпионский"],
         "price_range": (3_500_000, 4_000_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Kimi_R%C3%A4ikk%C3%B6nen_2007_Brazil.jpg/1280px-Kimi_R%C3%A4ikk%C3%B6nen_2007_Brazil.jpg"},
        {"name": "Ferrari SF70H", "team": "Ferrari", "year": 2017, "era_id": "era_hybrid_wide",
         "tags": ["Гибрид", "Аэродинамический"], "price_range": (2_800_000, 3_200_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/F1-2017_Test_Barcelona_Vettel_1.jpg/1280px-F1-2017_Test_Barcelona_Vettel_1.jpg"},
        {"name": "Ferrari F1-75", "team": "Ferrari", "year": 2022, "era_id": "era_ground_effect",
         "tags": ["Гибрид", "Граунд-эффект"], "price_range": (3_000_000, 3_500_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Charles_Leclerc%2C_Ferrari_F1-75%2C_2022_Miami_Grand_Prix_%2852063534092%29.jpg/1280px-Charles_Leclerc%2C_Ferrari_F1-75%2C_2022_Miami_Grand_Prix_%2852063534092%29.jpg"},
        # Другие команды...
        {"name": "McLaren MP4/13", "team": "McLaren", "year": 1998, "era_id": "era_v10_early",
         "tags": ["V10", "Чемпионский"], "price_range": (2_200_000, 2_700_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/McLaren_MP4-13_at_the_2014_Goodwood_Festival_of_Speed.jpg/1280px-McLaren_MP4-13_at_the_2014_Goodwood_Festival_of_Speed.jpg"},
        {"name": "Williams FW19", "team": "Williams", "year": 1997, "era_id": "era_v10_early",
         "tags": ["V10", "Чемпионский"], "price_range": (2_400_000, 2_800_000),
         "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Williams_FW19_1997_Jacques_Villeneuve_Tribute_2012_side.jpg/1280px-Williams_FW19_1997_Jacques_Villeneuve_Tribute_2012_side.jpg"},
    ]

    bolids = []
    for i, b in enumerate(curated_bolids):
        bolids.append({
            "id": f"bolid_{i + 1}", "name": b["name"], "team": b["team"], "year": b["year"],
            "price": random.randint(b["price_range"][0], b["price_range"][1]),
            "era_id": b["era_id"], "tags": b["tags"], "quantity_available": random.randint(1, 3),
            "image_url": b["image_url"]
        })

    num_collectors = 20;
    num_orders = 40
    collectors = [{"id": f"coll_{i}", "name": fake.name(), "tier": random.choice(("Paddock Club", "Grandstand"))} for i
                  in range(1, num_collectors + 1)]
    orders = []
    if bolids:
        bolid_ids = [b['id'] for b in bolids];
        collector_ids = [c['id'] for c in collectors]
        for i in range(1, num_orders + 1):
            items = [{"bolid_id": bid, "quantity": 1} for bid in random.sample(bolid_ids, random.randint(1, 3))]
            total = sum(
                next(b['price'] for b in bolids if b['id'] == item['bolid_id']) * item['quantity'] for item in items)
            orders.append(
                {"id": f"order_{i}", "collector_id": random.choice(collector_ids), "items": items, "total_price": total,
                 "timestamp": fake.iso8601()})

    data.update({'bolids': bolids, 'collectors': collectors, 'purchase_orders': orders})
    with open(seed_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==============================================================================
# UI приложения
# ==============================================================================
st.set_page_config(layout="wide", page_title="F1 Collection Analytics", initial_sidebar_state="auto")
load_css()


# --- НОВАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ МЕНЮ ---
def animated_menu():
    st.sidebar.title("F1 Analytics")

    # Инициализация состояния меню при первом запуске
    if 'menu_choice' not in st.session_state:
        st.session_state.menu_choice = "Обзор"

    menu_items = ["Обзор", "Каталог болидов", "Мой гараж", "Данные"]

    for item in menu_items:
        # Для активной кнопки применяем специальный CSS класс через st.markdown
        if st.session_state.menu_choice == item:
            st.markdown(
                f'<style>div[data-testid="stButton-"{item}""] button {{ background-color: rgba(0, 210, 190, 0.2); color: #FFFFFF; border-left: 4px solid #00D2BE; font-weight: 700; }}</style>',
                unsafe_allow_html=True)

        if st.sidebar.button(item, key=f"stButton-{item}", use_container_width=True):
            st.session_state.menu_choice = item
            st.rerun()


# --- ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ ---

if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
try:
    if not os.path.exists(SEED_FILE) or os.path.getsize(SEED_FILE) < 100:
        st.warning(f"Файл {SEED_FILE} не найден или пуст. Создается новый файл...")
        base_structure = {
            "eras": [
                {"id": "era_v10", "name": "Эра V10 (1995-2005)", "parent": None},
                {"id": "era_v8", "name": "Эра V8 (2006-2013)", "parent": None},
                {"id": "era_hybrid", "name": "Гибридная эра (2014-н.в.)", "parent": None},
                {"id": "era_v10_early", "name": "Ранние V10 (1995-1999)", "parent": "era_v10"},
                {"id": "era_v10_late", "name": "Поздние V10 (2000-2005)", "parent": "era_v10"},
                {"id": "era_hybrid_early", "name": "Ранние гибриды (2014-2016)", "parent": "era_hybrid"},
                {"id": "era_hybrid_wide", "name": "Широкие машины (2017-2021)", "parent": "era_hybrid"},
                {"id": "era_ground_effect", "name": "Граунд-эффект (2022-н.в.)", "parent": "era_hybrid"}
            ], "bolids": [], "collectors": [], "purchase_orders": []}
        with open(SEED_FILE, 'w', encoding='utf-8') as f: json.dump(base_structure, f, indent=2, ensure_ascii=False)
        st.info("Файл создан. Перезагрузите страницу для генерации данных.")
        st.stop()

    with open(SEED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not data.get('bolids'):
        with st.spinner("Первый запуск: Генерируем тестовые данные..."):
            generate_f1_mock_data()
        st.rerun()
except (FileNotFoundError, json.JSONDecodeError) as e:
    st.error(f"Ошибка при загрузке {SEED_FILE}: {e}.");
    st.stop()


@st.cache_data
def get_app_data(): return load_seed_data(SEED_FILE)


ERAS, BOLIDS, COLLECTORS, ORDERS = get_app_data()
BOLID_MAP = {b.id: b for b in BOLIDS};
ERA_MAP = {e.id: e for e in ERAS}
if 'garage' not in st.session_state: st.session_state.garage = Garage("coll_1", [])

# Вызов новой функции меню
animated_menu()
menu_choice = st.session_state.menu_choice


def display_bolid_card(bolid: Bolid):
    with st.container(border=True):
        st.image(bolid.image_url, use_container_width=True)
        st.markdown(f'<h5>{bolid.name}</h5>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#00D2BE; margin-top:-10px;">{bolid.team} - {bolid.year}</p>',
                    unsafe_allow_html=True)
        tags_html = "".join([f'<span class="bolid-card-tag">{tag}</span>' for tag in bolid.tags])
        st.markdown(f'<div class="bolid-card-tags">{tags_html}</div>', unsafe_allow_html=True)
        st.markdown(f"""<hr style="border-color:#2D2D2D;"><p><b>Цена:</b> ${bolid.price:,}</p>""",
                    unsafe_allow_html=True)
        if st.button("В гараж", key=f"add_{bolid.id}"):
            st.session_state.garage = add_to_garage(st.session_state.garage, bolid.id, 1)
            st.toast(f"{bolid.name} добавлен в гараж!", icon="🏎️");
            time.sleep(1);
            st.rerun()


if menu_choice == "Обзор":
    st.header("🏁 Обзор коллекции")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Коллекционеров", f"{len(COLLECTORS)} 👥")
    col2.metric("Уникальных болидов", f"{len(BOLIDS)} 🏎️")
    col3.metric("Всего покупок", f"{len(ORDERS)} 🛒")
    total_sales_value = sum(o.total_price for o in ORDERS)
    col4.metric("Объем рынка", f"${total_sales_value:,}")
elif menu_choice == "Каталог болидов":
    st.header("🏎️ Каталог болидов")
    teams = sorted(list(set(b.team for b in BOLIDS)))
    era_options = ["all"] + [e.id for e in ERAS if e.parent is None]


    def format_era_name(era_id):
        return "Все эры" if era_id == "all" else ERA_MAP.get(era_id, CarEra(era_id, "Неизвестно", None)).name


    col1, col2, col3 = st.columns(3)
    selected_era_id = col1.selectbox("Фильтр по эре", options=era_options, format_func=format_era_name)
    price_range = col2.slider("Диапазон цен ($)", 0, 6000000, (0, 6000000))
    selected_team = col3.selectbox("Фильтр по команде", options=["Все"] + teams)

    filtered_bolids = list(BOLIDS)
    if selected_era_id != "all":
        era_ids_to_show = {e.id for e in flatten_eras(ERAS, selected_era_id)}
        filtered_bolids = [b for b in filtered_bolids if b.era_id in era_ids_to_show]
    filtered_bolids = [b for b in filtered_bolids if price_range[0] <= b.price <= price_range[1]]
    if selected_team != "Все": filtered_bolids = [b for b in filtered_bolids if b.team == selected_team]

    st.write(f"Найдено болидов: {len(filtered_bolids)}");
    st.markdown("---")
    cols = st.columns(3)
    for i, bolid in enumerate(filtered_bolids):
        with cols[i % 3]: display_bolid_card(bolid)
elif menu_choice == "Мой гараж":
    st.header("🛠️ Мой гараж")
    if not st.session_state.garage.items:
        st.info("Ваш гараж пуст.")
    else:
        total = sum(BOLID_MAP[item.bolid_id].price * item.quantity for item in st.session_state.garage.items)
        for item in st.session_state.garage.items:
            bolid = BOLID_MAP[item.bolid_id]
            col1, col2, col3 = st.columns([3, 1, 1]);
            col1.write(f"**{bolid.name}**");
            col2.write(f"Кол-во: {item.quantity}");
            col3.write(f"${bolid.price * item.quantity:,}")
        st.markdown("---");
        st.subheader(f"Итого: ${total:,}")
        if st.button("Оформить покупку"):
            st.success("Покупка успешно оформлена!");
            st.session_state.garage = Garage("coll_1", []);
            time.sleep(2);
            st.rerun()
elif menu_choice == "Данные":
    st.header("📄 Сырые данные (seed.json)")
    with st.expander("Эры Формулы 1"):
        st.dataframe(pd.DataFrame(ERAS))
    with st.expander("Болиды"):
        st.dataframe(pd.DataFrame(BOLIDS))
    with st.expander("Коллекционеры"):
        st.dataframe(pd.DataFrame(COLLECTORS))
    with st.expander("История покупок"):
        st.dataframe(pd.DataFrame(ORDERS))