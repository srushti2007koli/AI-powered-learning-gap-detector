LIGHT = dict(bg="#F4F6FB", card="#FFFFFF", text="#1B1F3B", muted="#667085", border="#E4E7EC",
             shadow="rgba(27,31,59,0.08)", accent="#6C5CE7", accent2="#00B8A9",
             good="#0E9F5C", good_bg="#E3F7EC", warn="#C77700", warn_bg="#FFF1D6",
             bad="#D92D20", bad_bg="#FDE7E5", input_bg="#FFFFFF")
DARK = dict(bg="#0B1020", card="#151B2E", text="#E8EBF5", muted="#98A2B3", border="#27304F",
            shadow="rgba(0,0,0,0.45)", accent="#8B7BFF", accent2="#2DD4BF",
            good="#32D583", good_bg="#12352A", warn="#FDB022", warn_bg="#3B2A0B",
            bad="#F97066", bad_bg="#3E1715", input_bg="#0F1527")

CSS = """
.stApp{--bg:@@bg@@;--card:@@card@@;--text:@@text@@;--muted:@@muted@@;--border:@@border@@;--shadow:@@shadow@@;--accent:@@accent@@;--accent2:@@accent2@@;--good:@@good@@;--good-bg:@@good_bg@@;--warn:@@warn@@;--warn-bg:@@warn_bg@@;--bad:@@bad@@;--bad-bg:@@bad_bg@@;--neutral:@@accent@@;background:@@bg@@;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:@@card@@;border-right:1px solid @@border@@;}
.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6,.stApp summary,[data-testid="stSidebar"] span,[data-testid="stWidgetLabel"] *{color:@@text@@;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:@@muted@@;}
[data-baseweb="popover"],[data-baseweb="popover"] ul,[data-baseweb="menu"]{background:@@card@@ !important;}
[data-baseweb="popover"] li,[data-baseweb="popover"] li *{color:@@text@@ !important;}
.block-container{padding-top:2rem;max-width:1200px;}
.stButton>button,[data-testid="stFormSubmitButton"]>button{background:@@accent@@;border:0;border-radius:12px;padding:.55rem 1.3rem;font-weight:600;transition:transform .15s,box-shadow .15s;}
.stButton>button p,[data-testid="stFormSubmitButton"]>button p{color:#fff !important;}
.stButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover{transform:translateY(-2px);box-shadow:0 6px 16px @@shadow@@;background:@@accent@@;}
.stTextInput input,.stTextArea textarea,[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="input"]>div{background:@@input_bg@@ !important;color:@@text@@ !important;border-color:@@border@@ !important;}
[data-testid="stForm"]{background:@@card@@;border:1px solid @@border@@;border-radius:16px;padding:18px 20px;}
.stTextInput input::placeholder{color:@@muted@@ !important;opacity:.8;}
[data-baseweb="input"] button{background:transparent !important;}
[data-baseweb="input"] svg{fill:@@muted@@;color:@@muted@@;}
[data-testid="stFileUploaderDropzone"]{background:@@input_bg@@ !important;border:1.5px dashed @@accent@@ !important;border-radius:14px;}
[data-testid="stFileUploaderDropzone"] *{color:@@text@@ !important;}
[data-testid="stFileUploaderDropzone"] small{color:@@muted@@ !important;}
[data-testid="stFileUploaderDropzone"] button{background:@@accent@@ !important;border:0 !important;border-radius:10px !important;}
[data-testid="stFileUploaderDropzone"] button,[data-testid="stFileUploaderDropzone"] button *{color:#fff !important;}
.stTabs [data-baseweb="tab"] p{font-weight:600;color:@@muted@@;}
.stTabs [aria-selected="true"] p{color:@@accent@@;}
.stTabs [data-baseweb="tab-highlight"]{background:@@accent@@;}
[data-testid="stExpander"]{background:@@card@@;border:1px solid @@border@@;border-radius:12px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px 20px;margin-bottom:14px;box-shadow:0 2px 10px var(--shadow);transition:transform .2s,box-shadow .2s;animation:fade .5s ease;}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 26px var(--shadow);}
.hero{background:linear-gradient(120deg,var(--accent),var(--accent2));border-radius:22px;padding:28px 32px;margin-bottom:18px;animation:fade .6s ease;}
.hero div{color:#fff;}
.ht{font-size:28px;font-weight:700;}.hs{font-size:15px;opacity:.92;margin-top:4px;}.hc{margin-top:14px;}
.hero .pill{background:rgba(255,255,255,.22);color:#fff;margin-right:8px;}
.muted{color:var(--muted);}.sm{font-size:13px;}.big{font-size:18px;font-weight:700;color:var(--text);}
.kpi .v{font-size:32px;font-weight:700;color:var(--text);line-height:1.2;margin:4px 0;}
.goodc{color:var(--good) !important;}.warnc{color:var(--warn) !important;}.badc{color:var(--bad) !important;}
.pill{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:600;margin-right:6px;}
.pill.good{background:var(--good-bg);color:var(--good);}.pill.warn{background:var(--warn-bg);color:var(--warn);}
.pill.bad{background:var(--bad-bg);color:var(--bad);}.pill.neutral{background:var(--border);color:var(--text);}
.meter{height:9px;border-radius:99px;background:var(--border);overflow:hidden;margin:8px 0;}
.meter i{display:block;height:100%;border-radius:99px;animation:grow 1.1s ease;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;}
.chain{display:flex;align-items:center;flex-wrap:wrap;gap:8px;}
.chip{padding:8px 14px;border-radius:12px;font-weight:600;font-size:13px;transition:transform .15s;}
.chip:hover{transform:scale(1.07);}
.chip.good{background:var(--good-bg);color:var(--good);}.chip.warn{background:var(--warn-bg);color:var(--warn);}.chip.bad{background:var(--bad-bg);color:var(--bad);}
.arrow{color:var(--muted);font-size:18px;}
.ev{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--border);}
.ev .q{font-family:monospace;font-weight:700;color:var(--accent);min-width:34px;}
.ev .t{flex:1;color:var(--text);font-size:14px;line-height:1.5;}
table.heat{width:100%;border-collapse:separate;border-spacing:6px;}
table.heat th{font-size:12px;color:var(--muted);font-weight:600;padding:4px;}
table.heat td.n{font-weight:600;color:var(--text);font-size:14px;}
table.heat td.c{text-align:center;padding:12px 4px;border-radius:12px;font-weight:700;font-size:14px;transition:transform .15s;}
table.heat td.c:hover{transform:scale(1.1);}
td.c.neutral{background:var(--border);color:var(--muted);}td.c.good{background:var(--good-bg);color:var(--good);}td.c.warn{background:var(--warn-bg);color:var(--warn);}td.c.bad{background:var(--bad-bg);color:var(--bad);}
.qbox{font-size:22px;font-weight:600;color:var(--text);padding:6px 0;}
@keyframes fade{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}
@keyframes grow{from{width:0;}}
"""


def css(dark=True):
    out = CSS
    for k, v in (DARK if dark else LIGHT).items():
        out = out.replace(f"@@{k}@@", v)
    return "".join(line.strip() for line in out.splitlines())