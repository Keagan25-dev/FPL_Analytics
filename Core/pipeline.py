import streamlit as st
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_URL = "https://premierleague.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=3600)
def fetch_bootstrap_data():
    try:
        return requests.get(f"{BASE_URL}bootstrap-static/", headers=HEADERS, verify=False, timeout=15).json()
    except Exception: return None

@st.cache_data(ttl=3600)
def fetch_fixtures_data():
    try:
        return requests.get(f"{BASE_URL}fixtures/", headers=HEADERS, verify=False, timeout=15).json()
    except Exception: return []

@st.cache_data(ttl=3600)
def fetch_manager_team(m_id, gw):
    try:
        res = requests.get(f"{BASE_URL}entry/{m_id}/event/{gw}/picks/", headers=HEADERS, verify=False, timeout=15)
        if res.status_code == 200: return res.json()
    except Exception: pass
    try:
        hist = requests.get(f"{BASE_URL}entry/{m_id}/history/", headers=HEADERS, verify=False, timeout=15).json()
        if 'current' in hist and len(hist['current']) > 0:
            last_gw = hist['current'][-1]['event']
            res = requests.get(f"{BASE_URL}entry/{m_id}/event/{last_gw}/picks/", headers=HEADERS, verify=False, timeout=15)
            if res.status_code == 200: return res.json()
    except Exception: return None
