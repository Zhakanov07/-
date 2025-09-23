# ==============================================================================
#
#  Проект: «Аналитика коллекции болидов Формулы 1»
#  Финальная версия со стилизацией и динамическими изображениями
#
# ==============================================================================

import streamlit as st
import pandas as pd
import time
import json
import uuid
from faker import Faker
from datetime import datetime
from functools import reduce, lru_cache
from typing import NamedTuple, Optional, List, Tuple, Callable
import os

# ==============================================================================
# СТИЛИЗАЦИЯ (CSS)
# ==============================================================================
def load_css():
    """Функция для внедрения кастомного CSS в приложение."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700&display=swap');

            /* Основной шрифт и фон */
            html, body, [class*="st-"] {
                font-family: 'Titillium Web', sans-serif;
            }
            .stApp {
                background-color: #121212;
                color: #E0E0E0;
            }
            h1, h2, h3 {
                color: #FFFFFF;
            }

            /* Боковая панель */
            .st-emotion-cache-16txtl3 {
                background-color: #1E1E1E;
                border-right: 1px solid #2D2D2D;
            }
            .st-emotion-cache-16txtl3 .st-emotion-cache-1v0mbdj { /* Заголовки на боковой панели */
                 color: #FFFFFF;
            }
             .st-emotion-cache-16txtl3 .st-emotion-cache-1kyxreq { /* Радио-кнопки */
                 color: #E0E0E0;
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
            }
            .stButton>button:hover {
                background-color: #00A693;
            }
            .stButton>button:focus {
                box-shadow: 0 0 0 2px #00D2BE;
            }

            /* Карточки болидов */
            .bolid-card {
                background-color: #1E1E1E;
                border: 1px solid #2D2D2D;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                transition: box-shadow 0.3s ease;
                height: 95%;
            }
            .bolid-card:hover {
                box-shadow: 0px 5px 15px rgba(0, 210, 190, 0.2);
            }
            .bolid-card img {
                width: 100%;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            .bolid-card-title {
                font-size: 1.5em;
                font-weight: 700;
                color: #FFFFFF;
            }
            .bolid-card-team {
                font-size: 1.1em;
                color: #00D2BE;
                margin-bottom: 10px;
            }
            .bolid-card-tag {
                background-color: #2D2D2D;
                color: #00D2BE;
                padding: 3px 8px;
                border-radius: 5px;
                font-size: 0.8em;
                margin-right: 5px;
                display: inline-block;
            }

            /* Таблицы и метрики */
            .stDataFrame {
                background-color: #1E1E1E;
            }
            .stMetric {
                background-color: #1E1E1E;
                border: 1px solid #2D2D2D;
                border-radius: 10px;
                padding: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# МОДЕЛИ ДАННЫХ
# ==============================================================================
class CarEra(NamedTuple):
    id: str; name: str; parent: Optional[str]

class Bolid(NamedTuple):
    id: str; name: str; team: str; year: int; price: int; era_id: str; tags: List[str]; quantity_available: int; image_url: str

class Collector(NamedTuple):
    id: str; name: str; tier: str

class GarageItem(NamedTuple):
    bolid_id: str; quantity: int

class Garage(NamedTuple):
    collector_id: str; items: List[GarageItem]

class PurchaseOrder(NamedTuple):
    id: str; collector_id: str; items: List[GarageItem]; total_price: int; timestamp: str

# ==============================================================================
# УТИЛИТАРНЫЕ ФУНКЦИИ
# ==============================================================================
def get_children(eras: Tuple[CarEra, ...], era_id: Optional[str]) -> Tuple[CarEra, ...]:
    return tuple(e for e in eras if e.parent == era_id)

def flatten_eras(eras: Tuple[CarEra, ...], root_id: Optional[str]) -> Tuple[CarEra, ...]:
    flat_list = []; recurse_ids = set()
    def recurse(current_id: Optional[str]):
        if current_id in recurse_ids: return
        recurse_ids.add(current_id)
        for child in get_children(eras, current_id): flat_list.append(child); recurse(child.id)
    root_era = next((e for e in eras if e.id == root_id), None)
    if root_era: flat_list.append(root_era)
    recurse(root_id)
    return tuple(flat_list)

def collect_bolids_recursive(eras: Tuple[CarEra, ...], bolids: Tuple[Bolid, ...], root_id: str) -> Tuple[Bolid, ...]:
    target_era_ids = {e.id for e in flatten_eras(eras, root_id)}
    return tuple(b for b in bolids if b.era_id in target_era_ids)

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

def finalize_purchase(garage: Garage, bolids: Tuple[Bolid, ...], timestamp: str) -> PurchaseOrder:
    bolid_map = {b.id: b for b in bolids}
    total = sum(bolid_map[item.bolid_id].price * item.quantity for item in garage.items)
    return PurchaseOrder(str(uuid.uuid4()), garage.collector_id, list(garage.items), total, timestamp)

def total_sales(orders: Tuple[PurchaseOrder, ...]) -> int:
    return reduce(lambda acc, o: acc + o.total_price, orders, 0)

def by_price_range(min_p: int, max_p: int) -> Callable:
    return lambda b: min_p <= b.price <= max_p

def by_team(team: str) -> Callable:
    return lambda b: b.team == team

@lru_cache(maxsize=128)
def top_selling_bolids(orders: Tuple[PurchaseOrder, ...], bolids: Tuple[Bolid, ...], k: int = 10) -> Tuple:
    time.sleep(1)
    sales = {b.id: 0 for b in bolids}
    for order in orders:
        for item in order.items:
            if item.bolid_id in sales: sales[item.bolid_id] += item.quantity
    sorted_ids = sorted(sales, key=sales.get, reverse=True)[:k]
    bolid_map = {b.id: b for b in bolids}
    return tuple(bolid_map[bid] for bid in sorted_ids)

# ==============================================================================
# ГЕНЕРАЦИЯ ДАННЫХ
# ==============================================================================
def generate_f1_mock_data(seed_path='data/seed.json', num_bolids=50, num_collectors=20, num_orders=40):
    fake = Faker(); Faker.seed(0)
    with open(seed_path, 'r', encoding='utf-8') as f: data = json.load(f)
    eras = data.get('eras', []); era_ids = [e['id'] for e in eras]
    teams = ["Mercedes", "Ferrari", "Red Bull Racing", "McLaren", "Williams", "Renault", "Jordan"]
    tags = ["Чемпионский", "V10", "V8", "Гибрид", "Аэродинамический"]
    image_urls = [
        "https://www.mercedesamgf1.com/wp-content/uploads/sites/3/2023/02/W14_render_34_front_16x9_g-1.jpg",
        "https://media.formula1.com/image/upload/f_auto,c_limit,w_1920,q_auto/f_auto,c_limit,w_1920,q_auto/f1-website/2023/Car-launches/Ferrari/SF-23_side_view.jpg",
        "https://media.formula1.com/image/upload/f_auto,c_limit,w_1920,q_auto/f_auto,c_limit,w_1920,q_auto/f1-website/2023/Car-launches/Red-Bull-Racing/Red-Bull-RB19-side-2.jpg",
        "https://media.formula1.com/image/upload/f_auto,c_limit,w_1920,q_auto/f_auto,c_limit,w_1920,q_auto/f1-website/2023/Car-launches/McLaren/MCL60-side.jpg",
        "https://media.formula1.com/image/upload/f_auto,c_limit,w_1920,q_auto/f_auto,c_limit,w_1920,q_auto/f1-website/2023/Car-launches/Alpine/A523-side.jpg"
    ]
    bolids = []
    for i in range(1, num_bolids + 1):
        year = fake.random_int(min=1990, max=2023); team = fake.random_element(elements=teams)
        bolids.append({"id": f"bolid_{i}", "name": f"{team} {fake.word().capitalize()}{year}", "team": team, "year": year, "price": fake.random_int(min=100000, max=5000000), "era_id": fake.random_element(elements=era_ids), "tags": fake.random_elements(elements=tags, length=fake.random_int(min=1, max=2), unique=True), "quantity_available": fake.random_int(min=0, max=5), "image_url": fake.random_element(elements=image_urls)})
    collectors = [{"id": f"coll_{i}", "name": fake.name(), "tier": fake.random_element(elements=("Paddock Club", "Grandstand"))} for i in range(1, num_collectors + 1)]
    orders = []
    collector_ids = [c['id'] for c in collectors]; bolid_ids = [b['id'] for b in bolids]
    if not bolid_ids: return
    for i in range(1, num_orders + 1):
        garage_items = [{"bolid_id": bid, "quantity": 1} for bid in fake.random_elements(elements=bolid_ids, length=fake.random_int(min=1, max=3), unique=True)]
        if not garage_items: continue
        total_price = sum(next((b['price'] for b in bolids if b['id'] == item['bolid_id']), 0) * item['quantity'] for item in garage_items)
        orders.append({"id": f"order_{i}", "collector_id": fake.random_element(elements=collector_ids), "items": garage_items, "total_price": total_price, "timestamp": fake.iso8601()})
    data.update({'bolids': bolids, 'collectors': collectors, 'purchase_orders': orders})
    with open(seed_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

# ==============================================================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (UI)
# ==============================================================================
st.set_page_config(layout="wide", page_title="F1 Collection Analytics")
load_css()
SEED_FILE = 'data/seed.json'
if not os.path.exists('data'): os.makedirs('data')
try:
    with open(SEED_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
    if not data.get('bolids'): generate_f1_mock_data(SEED_FILE)
except (FileNotFoundError, json.JSONDecodeError):
    st.error(f"Не удалось загрузить или создать файл {SEED_FILE}. Убедитесь, что папка 'data' и файл 'seed.json' с базовыми 'eras' существуют."); st.stop()

@st.cache_data
def load_app_data(): return load_seed_data(SEED_FILE)

ERAS, BOLIDS, COLLECTORS, ORDERS = load_app_data()
BOLID_MAP = {b.id: b for b in BOLIDS}; ERA_MAP = {e.id: e for e in ERAS}

if 'garage' not in st.session_state:
    st.session_state.garage = Garage("coll_1", [])

st.sidebar.title("F1 Analytics")
menu_choice = st.sidebar.radio("Меню", ["Обзор", "Каталог болидов", "Мой гараж", "Отчеты", "Данные"])

# --- Функция для отображения карточки болида ---
def display_bolid_card(bolid: Bolid):
    with st.container():
        st.markdown('<div class="bolid-card">', unsafe_allow_html=True)
        st.image(bolid.image_url, use_column_width=True)
        st.markdown(f'<p class="bolid-card-title">{bolid.name}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="bolid-card-team">{bolid.team} - {bolid.year}</p>', unsafe_allow_html=True)
        tags_html = "".join([f'<span class="bolid-card-tag">{tag}</span>' for tag in bolid.tags])
        st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)
        era_name = ERA_MAP[bolid.era_id].name if bolid.era_id in ERA_MAP else "Неизвестно"
        st.markdown(f'<hr style="border-color:#2D2D2D;"><p><b>Цена:</b> ${bolid.price:,}</p><p><b>Эра:</b> {era_name}</p>', unsafe_allow_html=True)
        if st.button("В гараж", key=f"add_{bolid.id}"):
            st.session_state.garage = add_to_garage(st.session_state.garage, bolid.id, 1)
            st.toast(f"{bolid.name} добавлен в гараж!", icon="🏎️"); time.sleep(1); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Основные экраны ---
if menu_choice == "Обзор":
    st.header("🏁 Обзор коллекции")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Коллекционеров", f"{len(COLLECTORS)} 👥")
    col2.metric("Уникальных болидов", f"{len(BOLIDS)} 🏎️")
    col3.metric("Всего покупок", f"{len(ORDERS)} 🛒")
    col4.metric("Объем рынка", f"${total_sales(ORDERS):,}")

elif menu_choice == "Каталог болидов":
    st.header("🏎️ Каталог болидов")
    teams = sorted(list(set(b.team for b in BOLIDS)))
    col1, col2, col3 = st.columns(3)
    with col1: selected_era_id = st.selectbox("Фильтр по эре", options=list(ERA_MAP.keys()), format_func=lambda x: ERA_MAP[x].name)
    with col2: price_range = st.slider("Диапазон цен ($)", 0, 5000000, (0, 5000000))
    with col3: selected_team = st.selectbox("Фильтр по команде", options=["Все"] + teams)
    filtered_bolids = list(collect_bolids_recursive(ERAS, BOLIDS, selected_era_id))
    filtered_bolids = list(filter(by_price_range(price_range[0], price_range[1]), filtered_bolids))
    if selected_team != "Все": filtered_bolids = list(filter(by_team(selected_team), filtered_bolids))
    st.write(f"Найдено болидов: {len(filtered_bolids)}"); st.markdown("---")
    cols = st.columns(3)
    for i, bolid in enumerate(filtered_bolids):
        with cols[i % 3]:
            display_bolid_card(bolid)

elif menu_choice == "Мой гараж":
    st.header("🛠️ Мой гараж")
    garage = st.session_state.garage
    if not garage.items:
        st.info("Ваш гараж пуст. Добавьте болиды из каталога.")
    else:
        total = sum(BOLID_MAP[item.bolid_id].price * item.quantity for item in garage.items)
        for item in garage.items:
            bolid = BOLID_MAP[item.bolid_id]
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{bolid.name}**")
            col2.write(f"Кол-во: {item.quantity}")
            col3.write(f"${bolid.price * item.quantity:,}")
        st.markdown("---")
        st.subheader(f"Итого: ${total:,}")
        if st.button("Оформить покупку"):
            finalize_purchase(garage, BOLIDS, datetime.now().isoformat())
            st.success("Покупка успешно оформлена!")
            st.session_state.garage = Garage("coll_1", [])
            time.sleep(2)
            st.rerun()

elif menu_choice == "Отчеты":
    st.header("📊 Отчеты")
    st.subheader("Топ самых продаваемых болидов")
    k_top = st.slider("Количество топ-болидов", 1, 10, 5)
    if st.button("Сгенерировать отчет"):
        with st.spinner("Анализируем данные..."):
            top_selling_bolids.cache_clear()
            top_bolids = top_selling_bolids(ORDERS, BOLIDS, k_top)
        st.success("Отчет готов!")
        st.dataframe(pd.DataFrame(top_bolids), use_container_width=True)

elif menu_choice == "Данные":
    st.header("📄 Сырые данные (seed.json)")
    with st.expander("Эры Формулы 1"): st.dataframe(pd.DataFrame(ERAS))
    with st.expander("Болиды"): st.dataframe(pd.DataFrame(BOLIDS))
    with st.expander("Коллекционеры"): st.dataframe(pd.DataFrame(COLLECTORS))
    with st.expander("История покупок"): st.dataframe(pd.DataFrame(ORDERS))