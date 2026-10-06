"""Look and feel for the pages shown before sign in: landing, log in and sign up.

Everything here is scoped to those three pages. The signed-in app keeps using ui/theme.py.
"""
import streamlit as st

ORANGE, ORANGE_DARK = "#FF6A1F", "#E8560F"
INK = "#0A2540"

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
.stApp{background:radial-gradient(900px 520px at 88% 12%,rgba(255,120,40,.34),transparent 62%),linear-gradient(135deg,#0B4D61 0%,#0A2D4B 52%,#0A1F3A 100%) fixed !important;font-family:'Poppins','Segoe UI',Arial,sans-serif;}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"],[data-testid="stBottom"]{background:transparent !important;}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"],[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none !important;}
.stApp .block-container{max-width:1080px;padding:1.2rem 1.5rem 3rem;}
.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3{font-family:'Poppins','Segoe UI',Arial,sans-serif;color:#fff;}

.lg-brand{display:flex;align-items:center;gap:9px;font-weight:600;font-size:20px;color:#fff;padding-top:6px;}
.lg-brand svg{width:26px;height:26px;stroke:#FF8A3D;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}

.stApp .stButton>button{background:transparent;border:1.5px solid rgba(255,255,255,.5);border-radius:99px;padding:.45rem 1.4rem;min-height:44px;box-shadow:none;transition:background .15s,border-color .15s;}
.stApp .stButton>button p{color:#fff !important;font-weight:600;font-size:15px;}
.stApp .stButton>button:hover{background:rgba(255,255,255,.14);border-color:#fff;transform:none;box-shadow:none;}
.stApp .stButton>button:focus-visible,.stApp [data-testid="stFormSubmitButton"]>button:focus-visible{outline:3px solid #fff;outline-offset:2px;}
.stApp .stButton>button[kind="primary"],.stApp .stButton>button[data-testid="stBaseButton-primary"],.stApp [data-testid="stFormSubmitButton"]>button{background:linear-gradient(180deg,#FF7A2E,@@orange@@);border:0;border-radius:99px;min-height:46px;box-shadow:0 8px 22px rgba(255,106,31,.38);}
.stApp .stButton>button[kind="primary"] p,.stApp .stButton>button[data-testid="stBaseButton-primary"] p,.stApp [data-testid="stFormSubmitButton"]>button p{color:#fff !important;font-weight:600;font-size:16px;}
.stApp .stButton>button[kind="primary"]:hover,.stApp .stButton>button[data-testid="stBaseButton-primary"]:hover,.stApp [data-testid="stFormSubmitButton"]>button:hover{background:linear-gradient(180deg,@@orange@@,@@orange_dark@@);transform:translateY(-1px);box-shadow:0 10px 26px rgba(255,106,31,.5);}
.st-key-land_cta button{min-height:54px !important;}
.st-key-land_cta button p{font-size:18px !important;}

.lg-hero{text-align:center;padding:78px 0 26px;}
.lg-quote{font-size:clamp(18px,2.4vw,24px);font-style:italic;font-weight:400;color:rgba(255,255,255,.88);margin:0 0 12px;}
.lg-hero h1{font-weight:700;font-size:clamp(36px,5.6vw,64px);line-height:1.1;letter-spacing:-1.2px;color:#fff;margin:0 auto;max-width:860px;padding:0;}
.lg-sub{font-size:clamp(16px,2vw,20px);line-height:1.6;color:rgba(255,255,255,.82);max-width:600px;margin:18px auto 30px;}

.lg-flow{display:flex;align-items:stretch;justify-content:center;gap:0;max-width:900px;margin:64px auto 0;}
.lg-flow .st{flex:1;display:flex;align-items:center;justify-content:center;min-height:62px;padding:12px 30px 12px 38px;margin-left:-14px;color:#fff;font-weight:600;font-size:16px;text-align:center;}
.lg-flow .st:first-child{margin-left:0;padding-left:26px;clip-path:polygon(0 0,calc(100% - 24px) 0,100% 50%,calc(100% - 24px) 100%,0 100%);}
.lg-flow .st:nth-child(2){clip-path:polygon(0 0,calc(100% - 24px) 0,100% 50%,calc(100% - 24px) 100%,0 100%,24px 50%);}
.lg-flow .st:nth-child(3){clip-path:polygon(0 0,calc(100% - 24px) 0,100% 50%,calc(100% - 24px) 100%,0 100%,24px 50%);}
.lg-flow .a{background:linear-gradient(90deg,#1693B0,#1F7FA9);}
.lg-flow .b{background:linear-gradient(90deg,#F2753A,#E8453C);}
.lg-flow .c{background:linear-gradient(90deg,#14B8A6,#0E9F8E);}
.lg-flow .note{flex:1.2;margin-left:18px;border:1px solid rgba(255,255,255,.28);border-radius:10px;padding:12px 16px;font-size:14px;line-height:1.5;color:rgba(255,255,255,.88);display:flex;align-items:center;background:rgba(255,255,255,.06);}

.lg-feats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px;max-width:960px;margin:70px auto 0;text-align:center;}
.lg-feat .ic{width:52px;height:52px;margin:0 auto 12px;border-radius:50%;background:rgba(255,138,61,.14);border:1px solid rgba(255,138,61,.4);display:flex;align-items:center;justify-content:center;}
.lg-feat svg{width:26px;height:26px;stroke:#FF8A3D;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
.lg-feat b{display:block;font-size:17px;font-weight:600;color:#fff;margin-bottom:4px;}
.lg-feat span{display:block;font-size:14.5px;line-height:1.55;color:rgba(255,255,255,.76);}
.lg-foot{text-align:center;color:rgba(255,255,255,.7);font-size:15px;margin-top:60px;}

.lg-side{padding:34px 8px 0 0;}
.lg-side h1{font-weight:700;font-size:clamp(32px,4.2vw,48px);line-height:1.12;letter-spacing:-1px;color:#fff;margin:0 0 16px;padding:0;}
.lg-side p{color:rgba(255,255,255,.84);font-size:18px;line-height:1.6;max-width:440px;margin:0 0 20px;}
.lg-side ul{list-style:none;padding:0;margin:0;}
.lg-side li{color:#fff;font-size:16px;line-height:1.5;padding:7px 0 7px 28px;position:relative;}
.lg-side li::before{content:"";position:absolute;left:0;top:14px;width:12px;height:12px;border-radius:50%;background:@@orange@@;}

.stApp [data-testid="stForm"]{background:#fff;border:0;border-radius:16px;padding:28px 28px 22px;box-shadow:0 24px 60px rgba(3,14,34,.45);}
.stApp [data-testid="stForm"] label,.stApp [data-testid="stForm"] label p,.stApp [data-testid="stForm"] [data-testid="stWidgetLabel"] *{color:@@ink@@ !important;font-weight:600;font-size:15px;}
.stApp [data-testid="stForm"] .stTextInput input{background:#fff !important;color:@@ink@@ !important;border:1.5px solid #CBD5E1 !important;border-radius:10px;font-family:'Poppins',sans-serif;font-size:16px;}
.stApp [data-testid="stForm"] [data-baseweb="input"],.stApp [data-testid="stForm"] [data-baseweb="base-input"]{background:#fff !important;border-radius:10px;}
.stApp [data-testid="stForm"] .stTextInput input::placeholder{color:#94A3B8 !important;}
.stApp [data-testid="stForm"] .stTextInput input:focus{border-color:@@orange@@ !important;box-shadow:0 0 0 3px rgba(255,106,31,.22);}
.stApp [data-testid="stForm"] [data-baseweb="input"] svg{fill:#64748B;color:#64748B;}
.stApp [data-testid="stForm"] [data-testid="stFormSubmitButton"] button{width:100%;}
.stApp [data-testid="stAlert"]{border-radius:10px;}
.stApp .stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid rgba(255,255,255,.25);}
.stApp .stTabs [data-baseweb="tab"]{background:transparent;padding:10px 18px;height:auto;}
.stApp .stTabs [data-baseweb="tab"] p{color:rgba(255,255,255,.7);font-weight:600;font-size:16px;}
.stApp .stTabs [aria-selected="true"] p{color:#fff;}
.stApp .stTabs [data-baseweb="tab-highlight"]{background:@@orange@@;height:3px;}
.stApp .stTabs [data-baseweb="tab-border"]{display:none;}
.stApp .stTabs [data-baseweb="tab-panel"]{padding-top:18px;}
.st-key-to_signup button,.st-key-to_login button{border:0 !important;padding:0 !important;min-height:0 !important;justify-content:flex-start;box-shadow:none !important;background:transparent !important;}
.st-key-to_signup button p,.st-key-to_login button p{text-decoration:underline;text-underline-offset:4px;font-weight:500 !important;}
@media (max-width:820px){.lg-hero{padding-top:36px;}.lg-flow{flex-direction:column;gap:10px;margin-top:44px;}.lg-flow .st,.lg-flow .st:first-child,.lg-flow .st:nth-child(2),.lg-flow .st:nth-child(3){clip-path:none;margin-left:0;border-radius:10px;padding:14px 18px;}.lg-flow .note{margin-left:0;}.lg-side{padding:14px 0 6px;}}
@media (prefers-reduced-motion:reduce){.stApp *{transition:none !important;}}
"""

_LOGO = ('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/>'
         '<circle cx="12" cy="12" r="1.2"/></svg>')
_ICONS = {
    "assess": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M8.5 12h7M8.5 16h5"/>',
    "report": '<path d="M5 20V10M12 20V4M19 20v-7"/>',
    "practice": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
    "class": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/>'
             '<rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
}


def inject():
    """Apply the pre sign-in look. Call at the top of landing, login and signup pages."""
    css = _CSS.replace("@@orange_dark@@", ORANGE_DARK).replace("@@orange@@", ORANGE).replace("@@ink@@", INK)
    st.markdown("<style>" + "".join(line.strip() for line in css.splitlines()) + "</style>", unsafe_allow_html=True)


def brand():
    return f'<div class="lg-brand">{_LOGO}Learning Gap Detector</div>'


def hero():
    return ('<div class="lg-hero"><div class="lg-quote">\u201cSimple. Clear. Effective.\u201d</div>'
            '<h1>Identify &amp; Close Learning Gaps.</h1>'
            '<div class="lg-sub">Find the weak topics a good score can hide, then practise the right questions until they close.</div></div>')


def flow():
    return ('<div class="lg-flow"><div class="st a">Take an assessment</div><div class="st b">Find your gaps</div>'
            '<div class="st c">Practise and close them</div>'
            '<div class="note">Shows each student\u2019s weak topics, and the whole class for teachers.</div></div>')


def features(items):
    cards = "".join(f'<div class="lg-feat"><div class="ic"><svg viewBox="0 0 24 24">{_ICONS[k]}</svg></div><b>{t}</b><span>{d}</span></div>'
                    for k, t, d in items)
    return f'<div class="lg-feats">{cards}</div>'


def footer():
    return '<div class="lg-foot">Built for students and teachers.</div>'


def side(headline, text, points):
    lis = "".join(f"<li>{p}</li>" for p in points)
    return f'<div class="lg-side"><h1>{headline}</h1><p>{text}</p><ul>{lis}</ul></div>'