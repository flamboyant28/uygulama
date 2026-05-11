import streamlit as st
from solver import solve_cube
from cube_engine import apply_move
import streamlit.components.v1 as components
from alternative_solver import get_alternative_solutions, render_alternatives_ui
from cfop_solver import render_cfop_ui
import json

st.set_page_config(page_title="Rubik Küp Çözücü")

st.title("🧩 Rubik Küp Çözücü (Offline)")

st.warning("""
⚠️ Küpü şu şekilde tut:

- Üst = Sarı (U)
- Alt = Beyaz (D)
- Sağ = Yeşil (R)
- Sol = Mavi (L)
- Ön = Kırmızı (F)

Küpü çözüm boyunca döndürme!
""")

st.markdown("""
<style>
div.stButton > button {
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 22px !important;
    line-height: 1 !important;
    border: 2px solid rgba(0,0,0,0.35) !important;
    box-shadow: inset 0 2px 4px rgba(255,255,255,0.10), 0 2px 6px rgba(0,0,0,0.4) !important;
    transition: transform 0.1s !important;
    background: #111827 !important;
}
div.stButton > button:hover {
    transform: scale(1.12) !important;
    border-color: rgba(255,255,255,0.5) !important;
}
div.stButton > button:focus {
    outline: none !important;
}
div.stButton > button:disabled {
    opacity: 1 !important;
    border: 3px solid rgba(255,255,255,0.6) !important;
    cursor: default !important;
}
</style>
""", unsafe_allow_html=True)

# ---- RENKLER ----
colors = ["⬜", "🟥", "🟩", "🟨", "🟧", "🟦"]

color_map = {
    "⬜": "D",
    "🟥": "F",
    "🟩": "R",
    "🟨": "U",
    "🟧": "B",
    "🟦": "L"
}

EMOJI_TO_HEX = {
    "⬜": "#f8f9fa",
    "🟨": "#ffd60a",
    "🟥": "#d00000",
    "🟧": "#ff7b00",
    "🟩": "#38b000",
    "🟦": "#1d4ed8",
}

# ---- SESSION STATE ----
if "cube" not in st.session_state:
    st.session_state.cube = {
        "D": ["⬜"] * 9,
        "F": ["🟥"] * 9,
        "R": ["🟩"] * 9,
        "U": ["🟨"] * 9,
        "B": ["🟧"] * 9,
        "L": ["🟦"] * 9
    }

if "solution_moves" not in st.session_state:
    st.session_state.solution_moves = []

if "solution_index" not in st.session_state:
    st.session_state.solution_index = 0

if "initial_cube" not in st.session_state:
    st.session_state.initial_cube = None

if "alternative_solutions" not in st.session_state:
    st.session_state.alternative_solutions = []

if "cfop_cube_string" not in st.session_state:
    st.session_state.cfop_cube_string = None

if "scramble_count" not in st.session_state:
    st.session_state.scramble_count = None

if "selected_color" not in st.session_state:
    st.session_state.selected_color = "🟨"  # varsayılan sarı


def get_initial_cube_copy():
    if st.session_state.initial_cube is None:
        return {f: st.session_state.cube[f][:] for f in ["U", "R", "F", "D", "L", "B"]}
    return {f: st.session_state.initial_cube[f][:] for f in ["U", "R", "F", "D", "L", "B"]}


def normalize_move(move):
    move = move.strip()
    if not move:
        return None
    face = move[0]
    if len(move) == 1:
        return face
    suffix = move[1:]
    if suffix == "1":   return face
    elif suffix == "2": return face + "2"
    elif suffix == "3": return face + "'"
    elif suffix == "'": return face + "'"
    else:               return move


def emoji_to_css_color(emoji):
    return EMOJI_TO_HEX.get(emoji, "#666666")


def render_face_html(face_name, stickers, active=False):
    cells = ""
    for s in stickers:
        color = emoji_to_css_color(s)
        cells += (
            f"<div style='width:36px;height:36px;background:{color};"
            f"border:2px solid #222;border-radius:7px;box-sizing:border-box;'></div>"
        )
    glow = "box-shadow:0 0 18px rgba(255,255,0,0.50);" if active else ""
    return (
        f"<div style='display:flex;flex-direction:column;align-items:center;gap:8px;'>"
        f"<div style='color:white;font-weight:bold;font-size:16px;line-height:1;margin-bottom:2px;'>{face_name}</div>"
        f"<div style='display:grid;grid-template-columns:repeat(3,36px);gap:4px;"
        f"padding:10px;border-radius:12px;background:#111827;border:1px solid #374151;{glow}'>"
        f"{cells}</div></div>"
    )


def get_active_face(move):
    return move[0] if move else None


def render_cube_net(cube, active_move=None):
    active_face = get_active_face(active_move)
    u_html = render_face_html("U", cube["U"], active=(active_face == "U"))
    l_html = render_face_html("L", cube["L"], active=(active_face == "L"))
    f_html = render_face_html("F", cube["F"], active=(active_face == "F"))
    r_html = render_face_html("R", cube["R"], active=(active_face == "R"))
    b_html = render_face_html("B", cube["B"], active=(active_face == "B"))
    d_html = render_face_html("D", cube["D"], active=(active_face == "D"))
    html = (
        f"<div style='background:#030712;padding:28px 32px;border-radius:18px;"
        f"color:white;width:fit-content;margin:auto;font-family:Arial,sans-serif;'>"
        f"<div style='display:grid;grid-template-columns:repeat(4,auto);"
        f"column-gap:14px;row-gap:18px;justify-content:center;align-items:start;'>"
        f"<div></div><div style='display:flex;justify-content:center;'>{u_html}</div><div></div><div></div>"
        f"<div style='display:flex;justify-content:center;'>{l_html}</div>"
        f"<div style='display:flex;justify-content:center;'>{f_html}</div>"
        f"<div style='display:flex;justify-content:center;'>{r_html}</div>"
        f"<div style='display:flex;justify-content:center;'>{b_html}</div>"
        f"<div></div><div style='display:flex;justify-content:center;'>{d_html}</div><div></div><div></div>"
        f"</div></div>"
    )
    components.html(html, height=600)


def cycle_sticker(face_name, idx):
    # Seçili renk varsa onu ata, yoksa sıradakine geç
    if st.session_state.selected_color:
        st.session_state.cube[face_name][idx] = st.session_state.selected_color
    else:
        current = st.session_state.cube[face_name][idx]
        next_color = colors[(colors.index(current) + 1) % len(colors)]
        st.session_state.cube[face_name][idx] = next_color


FACE_LABEL_COLORS = {
    "U": "#ffd60a", "D": "#e5e7eb", "F": "#ef4444",
    "B": "#f97316", "R": "#22c55e", "L": "#3b82f6",
}

FACE_FULL_NAMES = {
    "U": "ÜST", "D": "ALT", "F": "ÖN",
    "B": "ARKA", "R": "SAĞ", "L": "SOL",
}


def draw_face_pretty(face_name):
    color = FACE_LABEL_COLORS.get(face_name, "#9ca3af")
    full  = FACE_FULL_NAMES.get(face_name, face_name)

    # Çerçeve + etiket birlikte açılıyor
    st.markdown(
        f"<div style='border:2px solid {color}66;border-radius:12px;"
        f"padding:8px 6px 6px 6px;background:rgba(255,255,255,0.02);"
        f"width:100%;box-sizing:border-box;'>"
        f"<div style='text-align:center;margin-bottom:6px;'>"
        f"<span style='font-weight:800;font-size:11px;letter-spacing:2px;"
        f"text-transform:uppercase;color:{color};'>"
        f"{face_name} · {full}</span></div>",
        unsafe_allow_html=True
    )
    face = st.session_state.cube[face_name]
    for row in range(3):
        cols = st.columns(3, gap="small")
        for col in range(3):
            idx = row * 3 + col
            with cols[col]:
                if idx == 4:
                    st.button(face[idx], key=f"fixed_{face_name}_{idx}", disabled=True, use_container_width=False)
                else:
                    if st.button(face[idx], key=f"sticker_{face_name}_{idx}", use_container_width=False):
                        cycle_sticker(face_name, idx)
                        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ---- Renkli algoritma gösterimi ----
def render_algorithm_colored(moves):
    """
    Hamleleri renkli HTML olarak göster:
    - Beyaz  → saat yönü (R, U, F ...)
    - Yeşil  → saat yönünün tersi (R', U', F' ...)
    - Sarı   → çift dönüş (R2, U2, F2 ...)
    """
    spans = []
    for m in moves:
        if m.endswith("'"):
            color = "#22c55e"
            title = "Saat yönünün tersi"
        elif m.endswith("2"):
            color = "#ffd60a"
            title = "2 kez"
        else:
            color = "#f8f9fa"
            title = "Saat yönü"
        spans.append(
            f"<span title='{title}' style='color:{color};font-family:monospace;"
            f"font-size:15px;font-weight:600;margin-right:6px;'>{m}</span>"
        )
    html = (
        "<div style='background:#1e293b;padding:12px 16px;border-radius:8px;"
        "border:1px solid #334155;line-height:2.2;'>"
        + "".join(spans) +
        "</div>"
        "<div style='margin-top:6px;font-size:11px;color:#6b7280;'>"
        "<span style='color:#f8f9fa;font-weight:700;margin-right:4px;'>■</span>Saat yönü &nbsp;&nbsp;"
        "<span style='color:#22c55e;font-weight:700;margin-right:4px;'>■</span>Saat yönünün tersi (') &nbsp;&nbsp;"
        "<span style='color:#ffd60a;font-weight:700;margin-right:4px;'>■</span>Çift dönüş (2)"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ---- 3D KÜP ----
def cube_state_to_hex(cube):
    result = {}
    for face in ["U", "R", "F", "D", "L", "B"]:
        result[face] = [EMOJI_TO_HEX.get(e, "#666666") for e in cube[face]]
    return result


def render_3d_cube(cube, moves_json="[]", current_index=0):
    state = cube_state_to_hex(cube)
    state_json = json.dumps(state)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0a0f; overflow: hidden; font-family: Arial, sans-serif; }}
  #container {{ width: 100%; height: 520px; position: relative; }}
  canvas {{ display: block; width: 100%; height: 100%; }}
  #info {{ position: absolute; top: 10px; left: 12px; font-size: 11px; color: #6b7280; }}
  #controls {{
    position: absolute; bottom: 0; left: 0; right: 0;
    display: flex; align-items: center; justify-content: center;
    gap: 10px; padding: 10px 12px;
    background: rgba(10,10,15,0.85);
    border-top: 1px solid rgba(255,255,255,0.08);
  }}
  .btn {{
    background: #1e293b; color: white;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px; padding: 6px 16px;
    cursor: pointer; font-size: 18px; line-height: 1;
    transition: background 0.15s, transform 0.1s;
    user-select: none;
  }}
  .btn:hover {{ background: #334155; transform: scale(1.05); }}
  .btn:active {{ transform: scale(0.97); }}
  .btn:disabled {{ opacity: 0.35; cursor: default; transform: none; }}
  #move-badge {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px; padding: 5px 14px;
    font-size: 15px; font-weight: 700; color: white;
    min-width: 64px; text-align: center; letter-spacing: 1px;
  }}
  #step-counter {{ font-size: 12px; color: #6b7280; min-width: 80px; text-align: center; }}
  #auto-btn {{
    background: #1e293b; color: #22c55e;
    border: 1px solid #22c55e44;
    border-radius: 8px; padding: 6px 14px;
    cursor: pointer; font-size: 12px; font-weight: 600;
    transition: background 0.15s;
  }}
  #auto-btn:hover {{ background: #14532d44; }}
  #auto-btn.playing {{ color: #ef4444; border-color: #ef444444; }}
</style>
</head>
<body>
<div id="container">
  <canvas id="c"></canvas>
  <div id="info">sürükle: döndür</div>
  <div id="controls">
    <button class="btn" id="btn-first" title="Başa al">⏮</button>
    <button class="btn" id="btn-prev"  title="Geri">◀</button>
    <div id="move-badge">—</div>
    <button class="btn" id="btn-next"  title="İleri">▶</button>
    <button class="btn" id="btn-last"  title="Sona al">⏭</button>
    <div id="step-counter">0 / 0</div>
    <button id="auto-btn">▶ Otomatik</button>
  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const INIT_STATE  = {state_json};
const ALL_MOVES   = {moves_json};
const INIT_INDEX  = {current_index};
const CX = 0x111827;

function hexToNum(h) {{ return parseInt(h.replace('#',''), 16); }}

let state = {{}};
function resetState() {{
  for (const f of ['U','R','F','D','L','B'])
    state[f] = INIT_STATE[f].map(hexToNum);
}}
resetState();

function rotateFaceCW(f) {{ return [f[6],f[3],f[0],f[7],f[4],f[1],f[8],f[5],f[2]]; }}

function applyMoveCW(face) {{
  const s = state;
  if (face==='U') {{
    s.U=rotateFaceCW(s.U);
    const t=[s.F[0],s.F[1],s.F[2]];
    [s.F[0],s.F[1],s.F[2]]=[s.R[0],s.R[1],s.R[2]];
    [s.R[0],s.R[1],s.R[2]]=[s.B[0],s.B[1],s.B[2]];
    [s.B[0],s.B[1],s.B[2]]=[s.L[0],s.L[1],s.L[2]];
    [s.L[0],s.L[1],s.L[2]]=t;
  }} else if (face==='D') {{
    s.D=rotateFaceCW(s.D);
    const t=[s.F[6],s.F[7],s.F[8]];
    [s.F[6],s.F[7],s.F[8]]=[s.L[6],s.L[7],s.L[8]];
    [s.L[6],s.L[7],s.L[8]]=[s.B[6],s.B[7],s.B[8]];
    [s.B[6],s.B[7],s.B[8]]=[s.R[6],s.R[7],s.R[8]];
    [s.R[6],s.R[7],s.R[8]]=t;
  }} else if (face==='R') {{
    s.R=rotateFaceCW(s.R);
    const t=[s.U[2],s.U[5],s.U[8]];
    [s.U[2],s.U[5],s.U[8]]=[s.F[2],s.F[5],s.F[8]];
    [s.F[2],s.F[5],s.F[8]]=[s.D[2],s.D[5],s.D[8]];
    [s.D[2],s.D[5],s.D[8]]=[s.B[6],s.B[3],s.B[0]];
    [s.B[6],s.B[3],s.B[0]]=t;
  }} else if (face==='L') {{
    s.L=rotateFaceCW(s.L);
    const t=[s.U[0],s.U[3],s.U[6]];
    [s.U[0],s.U[3],s.U[6]]=[s.B[8],s.B[5],s.B[2]];
    [s.B[8],s.B[5],s.B[2]]=[s.D[0],s.D[3],s.D[6]];
    [s.D[0],s.D[3],s.D[6]]=[s.F[0],s.F[3],s.F[6]];
    [s.F[0],s.F[3],s.F[6]]=t;
  }} else if (face==='F') {{
    s.F=rotateFaceCW(s.F);
    const t=[s.U[6],s.U[7],s.U[8]];
    [s.U[6],s.U[7],s.U[8]]=[s.L[8],s.L[5],s.L[2]];
    [s.L[8],s.L[5],s.L[2]]=[s.D[2],s.D[1],s.D[0]];
    [s.D[2],s.D[1],s.D[0]]=[s.R[0],s.R[3],s.R[6]];
    [s.R[0],s.R[3],s.R[6]]=t;
  }} else if (face==='B') {{
    s.B=rotateFaceCW(s.B);
    const t=[s.U[0],s.U[1],s.U[2]];
    [s.U[0],s.U[1],s.U[2]]=[s.R[2],s.R[5],s.R[8]];
    [s.R[2],s.R[5],s.R[8]]=[s.D[8],s.D[7],s.D[6]];
    [s.D[8],s.D[7],s.D[6]]=[s.L[6],s.L[3],s.L[0]];
    [s.L[6],s.L[3],s.L[0]]=t;
  }}
}}

function applyMove(move) {{
  const face=move[0], prime=move.endsWith("'"), double=move.endsWith('2');
  const times=double?2:(prime?3:1);
  for(let i=0;i<times;i++) applyMoveCW(face);
}}

const cont = document.getElementById('container');
const W = cont.clientWidth, H = 520;
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({{canvas,antialias:true,alpha:true}});
renderer.setSize(W,H); renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42,W/H,0.1,100);
camera.position.set(4.5,3.8,5.5); camera.lookAt(0,0,0);
scene.add(new THREE.AmbientLight(0xffffff,0.85));
const dl=new THREE.DirectionalLight(0xffffff,0.45);
dl.position.set(6,9,6); scene.add(dl);

function makeCubelet(x,y,z) {{
  const mats=Array(6).fill(null).map(()=>new THREE.MeshLambertMaterial({{color:CX}}));
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(0.92,0.92,0.92),mats);
  mesh.position.set(x,y,z); return mesh;
}}

const cubelets=[];
const cubeGroup=new THREE.Group(); scene.add(cubeGroup);
for(let x=-1;x<=1;x++) for(let y=-1;y<=1;y++) for(let z=-1;z<=1;z++) {{
  const mesh=makeCubelet(x,y,z);
  cubelets.push({{mesh,x,y,z}}); cubeGroup.add(mesh);
}}

function getSticker(face,cx,cy,cz) {{
  let row,col;
  if(face==='U'){{row=cz+1;col=cx+1;}}
  else if(face==='D'){{row=1-cz;col=cx+1;}}
  else if(face==='F'){{row=1-cy;col=cx+1;}}
  else if(face==='B'){{row=1-cy;col=1-cx;}}
  else if(face==='R'){{row=1-cy;col=1-cz;}}
  else if(face==='L'){{row=1-cy;col=cz+1;}}
  return state[face][row*3+col];
}}

function updateColors() {{
  for(const {{mesh,x,y,z}} of cubelets) {{
    const m=mesh.material;
    m[0].color.setHex(x===1 ?getSticker('R',x,y,z):CX);
    m[1].color.setHex(x===-1?getSticker('L',x,y,z):CX);
    m[2].color.setHex(y===1 ?getSticker('U',x,y,z):CX);
    m[3].color.setHex(y===-1?getSticker('D',x,y,z):CX);
    m[4].color.setHex(z===1 ?getSticker('F',x,y,z):CX);
    m[5].color.setHex(z===-1?getSticker('B',x,y,z):CX);
  }}
}}

let isDrag=false,px=0,py=0;
canvas.addEventListener('mousedown',e=>{{isDrag=true;px=e.clientX;py=e.clientY;}});
window.addEventListener('mouseup',()=>isDrag=false);
window.addEventListener('mousemove',e=>{{
  if(!isDrag)return;
  cubeGroup.rotation.y+=(e.clientX-px)*0.012;
  cubeGroup.rotation.x+=(e.clientY-py)*0.012;
  px=e.clientX;py=e.clientY;
}});
canvas.addEventListener('touchstart',e=>{{isDrag=true;px=e.touches[0].clientX;py=e.touches[0].clientY;}},{{passive:true}});
canvas.addEventListener('touchend',()=>isDrag=false);
canvas.addEventListener('touchmove',e=>{{
  if(!isDrag)return;
  cubeGroup.rotation.y+=(e.touches[0].clientX-px)*0.012;
  cubeGroup.rotation.x+=(e.touches[0].clientY-py)*0.012;
  px=e.touches[0].clientX;py=e.touches[0].clientY;
}},{{passive:true}});

const ANIM_DEF={{
  'U':{{axis:'y',layer:1}},"U'":{{axis:'y',layer:1}},
  'D':{{axis:'y',layer:-1}},"D'":{{axis:'y',layer:-1}},
  'R':{{axis:'x',layer:1}}, "R'":{{axis:'x',layer:1}},
  'L':{{axis:'x',layer:-1}},"L'":{{axis:'x',layer:-1}},
  'F':{{axis:'z',layer:1}}, "F'":{{axis:'z',layer:1}},
  'B':{{axis:'z',layer:-1}},"B'":{{axis:'z',layer:-1}},
  'U2':{{axis:'y',layer:1}},'D2':{{axis:'y',layer:-1}},
  'R2':{{axis:'x',layer:1}},'L2':{{axis:'x',layer:-1}},
  'F2':{{axis:'z',layer:1}},'B2':{{axis:'z',layer:-1}},
}};
const ANIM_DIR={{
  'U':-1,"U'":1,'U2':-1,'D':1,"D'":-1,'D2':1,
  'R':-1,"R'":1,'R2':-1,'L':1,"L'":-1,'L2':1,
  'F':-1,"F'":1,'F2':-1,'B':1,"B'":-1,'B2':1,
}};

let animating=false;
const queue=[];

function enqueue(move,onDone) {{
  queue.push({{move,onDone}});
  if(!animating) processQueue();
}}

function processQueue() {{
  if(!queue.length){{animating=false;updateUI();return;}}
  animating=true;
  const {{move,onDone}}=queue.shift();
  const def=ANIM_DEF[move];
  if(!def){{applyMove(move);updateColors();if(onDone)onDone();processQueue();return;}}
  const {{axis,layer}}=def;
  const dir=ANIM_DIR[move]||-1;
  const isDouble=move.endsWith('2');
  const affected=cubelets.filter(c=>c[axis]===layer);
  const pivot=new THREE.Group();
  cubeGroup.add(pivot);
  affected.forEach(c=>{{cubeGroup.remove(c.mesh);pivot.add(c.mesh);}});
  const totalAngle=(Math.PI/2)*(isDouble?2:1)*dir;
  const STEPS=isDouble?20:12;
  let step=0;
  function tick() {{
    step++;
    pivot.rotation[axis]=totalAngle*(step/STEPS);
    if(step<STEPS){{requestAnimationFrame(tick);return;}}
    affected.forEach(c=>{{
      pivot.remove(c.mesh);cubeGroup.add(c.mesh);
      c.mesh.position.set(c.x,c.y,c.z);
      c.mesh.quaternion.set(0,0,0,1);
    }});
    cubeGroup.remove(pivot);
    applyMove(move);
    updateColors();
    if(onDone) onDone();
    setTimeout(processQueue,20);
  }}
  tick();
}}

let currentStep = INIT_INDEX;

function updateUI() {{
  const badge = document.getElementById('move-badge');
  const counter = document.getElementById('step-counter');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnFirst = document.getElementById('btn-first');
  const btnLast = document.getElementById('btn-last');
  if(currentStep>0 && currentStep<=ALL_MOVES.length)
    badge.textContent = ALL_MOVES[currentStep-1];
  else
    badge.textContent = '—';
  counter.textContent = currentStep + ' / ' + ALL_MOVES.length;
  btnPrev.disabled  = currentStep<=0;
  btnNext.disabled  = currentStep>=ALL_MOVES.length;
  btnFirst.disabled = currentStep<=0;
  btnLast.disabled  = currentStep>=ALL_MOVES.length;
}}

function stepForward() {{
  if(currentStep>=ALL_MOVES.length||animating) return;
  const move=ALL_MOVES[currentStep];
  currentStep++;
  updateUI();
  enqueue(move, updateUI);
}}

function stepBackward() {{
  if(currentStep<=0||animating) return;
  currentStep--;
  resetState();
  for(let i=0;i<currentStep;i++) applyMove(ALL_MOVES[i]);
  updateColors();
  updateUI();
}}

function goFirst() {{
  if(animating) return;
  currentStep=0;
  resetState();
  updateColors();
  updateUI();
}}

function goLast() {{
  if(animating) return;
  currentStep=ALL_MOVES.length;
  resetState();
  for(let i=0;i<ALL_MOVES.length;i++) applyMove(ALL_MOVES[i]);
  updateColors();
  updateUI();
}}

let autoTimer=null;
function toggleAuto() {{
  const btn=document.getElementById('auto-btn');
  if(autoTimer) {{
    clearInterval(autoTimer);
    autoTimer=null;
    btn.textContent='▶ Otomatik';
    btn.classList.remove('playing');
  }} else {{
    btn.textContent='⏹ Durdur';
    btn.classList.add('playing');
    autoTimer=setInterval(()=>{{
      if(currentStep>=ALL_MOVES.length) {{
        clearInterval(autoTimer); autoTimer=null;
        btn.textContent='▶ Otomatik';
        btn.classList.remove('playing');
        return;
      }}
      if(!animating) stepForward();
    }},400);
  }}
}}

document.getElementById('btn-prev').addEventListener('click',stepBackward);
document.getElementById('btn-next').addEventListener('click',stepForward);
document.getElementById('btn-first').addEventListener('click',goFirst);
document.getElementById('btn-last').addEventListener('click',goLast);
document.getElementById('auto-btn').addEventListener('click',toggleAuto);

resetState();
for(let i=0;i<INIT_INDEX;i++) applyMove(ALL_MOVES[i]);
updateColors();
updateUI();

function render() {{
  requestAnimationFrame(render);
  renderer.render(scene,camera);
}}
render();
</script>
</body>
</html>
"""
    components.html(html, height=530)


# ---- TÜM YÜZLER ----
faces_order = ["U", "R", "F", "D", "L", "B"]

st.markdown("### 🧩 Küp Girişi")

# ---- RENK PALETİ ----
PALETTE = [
    ("🟨", "#ffd60a", "Sarı (U)"),
    ("🟥", "#d00000", "Kırmızı (F)"),
    ("🟩", "#38b000", "Yeşil (R)"),
    ("⬜", "#f8f9fa", "Beyaz (D)"),
    ("🟧", "#ff7b00", "Turuncu (B)"),
    ("🟦", "#1d4ed8", "Mavi (L)"),
]

palette_html = "<div style='display:flex;gap:6px;align-items:center;margin-bottom:12px;flex-wrap:wrap;'>"
palette_html += "<span style='font-size:11px;color:#6b7280;margin-right:4px;font-weight:600;'>RENK SEÇ:</span>"
for emoji, hex_color, label in PALETTE:
    selected = st.session_state.selected_color == emoji
    ring = f"box-shadow:0 0 0 3px {hex_color},0 0 0 5px #0f172a;" if selected else ""
    scale = "transform:scale(1.2);" if selected else ""
    palette_html += (
        f"<div title='{label}' style='width:32px;height:32px;background:{hex_color};"
        f"border-radius:8px;cursor:pointer;{ring}{scale}"
        f"transition:transform 0.1s;border:2px solid rgba(0,0,0,0.3);'></div>"
    )
palette_html += "</div>"
st.markdown(palette_html, unsafe_allow_html=True)

pal_cols = st.columns(len(PALETTE) + 1)
for i, (emoji, hex_color, label) in enumerate(PALETTE):
    with pal_cols[i]:
        selected = st.session_state.selected_color == emoji
        label_text = f"{'✓ ' if selected else ''}{label.split('(')[0].strip()}"
        if st.button(
            emoji,
            key=f"palette_{emoji}",
            help=label,
            use_container_width=False,
        ):
            st.session_state.selected_color = emoji
            st.rerun()

# Seçili rengi göster
sel = st.session_state.selected_color
sel_hex = EMOJI_TO_HEX.get(sel, "#666")
sel_name = next((l for e,h,l in PALETTE if e == sel), sel)
st.markdown(
    f"<div style='margin-bottom:10px;font-size:12px;color:#9ca3af;'>"
    f"Seçili renk: "
    f"<span style='display:inline-block;width:14px;height:14px;background:{sel_hex};"
    f"border-radius:3px;vertical-align:middle;margin:0 4px;border:1px solid rgba(255,255,255,0.2);'></span>"
    f"<span style='color:white;font-weight:600;'>{sel_name}</span>"
    f" — tıkladığın kareye uygulanır</div>",
    unsafe_allow_html=True
)

top_cols = st.columns([1, 1, 1, 1], gap="small")
with top_cols[1]:
    draw_face_pretty("U")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

mid_cols = st.columns([1, 1, 1, 1], gap="small")
with mid_cols[0]:
    draw_face_pretty("L")
with mid_cols[1]:
    draw_face_pretty("F")
with mid_cols[2]:
    draw_face_pretty("R")
with mid_cols[3]:
    draw_face_pretty("B")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

bot_cols = st.columns([1, 1, 1, 1], gap="small")
with bot_cols[1]:
    draw_face_pretty("D")


# ---- STRING OLUŞTUR ----
def get_cube_string():
    result = ""
    for f in faces_order:
        for c in st.session_state.cube[f]:
            result += color_map[c]
    return result


def validate_cube(cube_string):
    if len(cube_string) != 54:
        return False, "Eksik veya fazla giriş var"
    from collections import Counter
    count = Counter(cube_string)
    for face in "URFDLB":
        if count[face] != 9:
            return False, f"{face} renginden 9 tane olmalı"
    return True, "OK"


def translate_move(move):
    mapping = {
        "R": "Sağ yüz", "L": "Sol yüz", "U": "Üst yüz",
        "D": "Alt yüz", "F": "Ön yüz",  "B": "Arka yüz",
    }
    face = mapping[move[0]]
    if len(move) == 1:        return f"{face} ↻ saat yönünde 1 kez çevir"
    elif move.endswith("2"):  return f"{face} ⟲ 2 kez çevir"
    elif move.endswith("'"): return f"{face} ↺ saat yönünün tersine 1 kez çevir"


def rebuild_cube_to_step(step_index):
    temp_cube = get_initial_cube_copy()
    for i in range(step_index):
        temp_cube = apply_move(temp_cube, st.session_state.solution_moves[i])
    st.session_state.cube = temp_cube


# ---- KARIŞTIR & SIFIRLA ----
import random as _random

def scramble_cube():
    """Rastgele geçerli küp üret"""
    MOVES = ["U","U'","U2","D","D'","D2","R","R'","R2",
             "L","L'","L2","F","F'","F2","B","B'","B2"]
    cube = {
        "D": ["⬜"]*9, "F": ["🟥"]*9, "R": ["🟩"]*9,
        "U": ["🟨"]*9, "B": ["🟧"]*9, "L": ["🟦"]*9
    }
    count = _random.randint(18, 25)
    moves_applied = []
    last_face = None
    for _ in range(count):
        candidates = [m for m in MOVES if m[0] != last_face]
        move = _random.choice(candidates)
        cube = apply_move(cube, move)
        moves_applied.append(move)
        last_face = move[0]
    return cube, count

# ---- ANA BUTON ÇUBUĞU ----
st.markdown("""
<div style='
    display:flex;gap:10px;align-items:center;
    background:#111827;border:1px solid #1f2937;
    border-radius:12px;padding:10px 14px;margin-bottom:8px;
'>
""", unsafe_allow_html=True)

bar_cols = st.columns([1,1,1,2,1,1])

with bar_cols[0]:
    solve_clicked = st.button("🔍 Çöz", use_container_width=True)

with bar_cols[1]:
    scramble_clicked = st.button("🔀 Karıştır", use_container_width=True)

with bar_cols[2]:
    reset_clicked = st.button("↺ Sıfırla", use_container_width=True)

# Geri / İleri butonları — her zaman görünür, çözüm yoksa devre dışı
with bar_cols[4]:
    back_clicked = st.button(
        "⬅ Geri",
        use_container_width=True,
        disabled=(not st.session_state.solution_moves or st.session_state.solution_index <= 0)
    )

with bar_cols[5]:
    fwd_clicked = st.button(
        "➡ İleri",
        use_container_width=True,
        disabled=(not st.session_state.solution_moves or
                  st.session_state.solution_index >= len(st.session_state.solution_moves))
    )

st.markdown("</div>", unsafe_allow_html=True)

# Buton aksiyonları
if scramble_clicked:
    new_cube, count = scramble_cube()
    st.session_state.cube = new_cube
    st.session_state.scramble_count = count
    st.session_state.solution_moves = []
    st.session_state.solution_index = 0
    st.session_state.initial_cube = None
    st.session_state.alternative_solutions = []
    st.session_state.cfop_cube_string = None
    st.rerun()

if reset_clicked:
    st.session_state.cube = {
        "D": ["⬜"]*9, "F": ["🟥"]*9, "R": ["🟩"]*9,
        "U": ["🟨"]*9, "B": ["🟧"]*9, "L": ["🟦"]*9
    }
    st.session_state.solution_moves = []
    st.session_state.solution_index = 0
    st.session_state.initial_cube = None
    st.session_state.alternative_solutions = []
    st.session_state.cfop_cube_string = None
    st.session_state.scramble_count = None
    st.rerun()

if back_clicked and st.session_state.solution_index > 0:
    st.session_state.solution_index -= 1
    rebuild_cube_to_step(st.session_state.solution_index)

if fwd_clicked and st.session_state.solution_index < len(st.session_state.solution_moves):
    st.session_state.solution_index += 1
    rebuild_cube_to_step(st.session_state.solution_index)

if st.session_state.scramble_count:
    st.caption(f"🔀 Küp {st.session_state.scramble_count} rastgele hamle ile karıştırıldı.")

# ---- ÇÖZ ----
if solve_clicked:
    try:
        cube_string = get_cube_string()
        valid, msg = validate_cube(cube_string)
        if not valid:
            st.error(f"❌ Hatalı küp: {msg}")
            st.stop()

        result = solve_cube(cube_string)

        if isinstance(result, list):
            result = " ".join(str(m) for m in result)
        result = str(result).split("(")[0].strip()

        st.success("✅ Çözüm bulundu!")

        moves = result.split()
        moves = [normalize_move(m) for m in moves]
        moves = [m for m in moves if m is not None]

        st.session_state.solution_moves = moves
        st.session_state.solution_index = 0
        st.session_state.initial_cube = {
            f: st.session_state.cube[f][:] for f in ["U", "R", "F", "D", "L", "B"]
        }
        st.session_state.cfop_cube_string = cube_string

        with st.spinner("Alternatif çözümler hesaplanıyor..."):
            st.session_state.alternative_solutions = get_alternative_solutions(
                cube_string, count=5
            )

    except Exception as e:
        st.error(f"Hata: {e}")


# ---- ÇÖZÜM GÖSTER ----
if st.session_state.solution_moves:
    active_move = None
    if st.session_state.solution_index < len(st.session_state.solution_moves):
        active_move = st.session_state.solution_moves[st.session_state.solution_index]

    # Güncel index ile active_move hesapla
    active_move = None
    if st.session_state.solution_index < len(st.session_state.solution_moves):
        active_move = st.session_state.solution_moves[st.session_state.solution_index]

    st.subheader("🧊 Görsel Küp (2D)")
    render_cube_net(st.session_state.cube, active_move=active_move)

    st.subheader("🎲 Görsel Küp (3D)")
    render_3d_cube(
        st.session_state.initial_cube,
        moves_json=json.dumps(st.session_state.solution_moves),
        current_index=st.session_state.solution_index
    )

    if active_move:
        st.info(f"Aktif hamle: {active_move} — {translate_move(active_move)}")

    st.subheader("🧠 Algoritma")
    render_algorithm_colored(st.session_state.solution_moves)

    st.subheader("📋 Adımlar:")
    for i, move in enumerate(st.session_state.solution_moves):
        st.write(f"{i + 1}. {translate_move(move)}")
        st.caption(f"Algoritma: {move}")

    st.info(
        f"Şu anki adım: {st.session_state.solution_index} / {len(st.session_state.solution_moves)}"
    )

    if st.session_state.alternative_solutions:
        st.divider()
        render_alternatives_ui(st.session_state.alternative_solutions)

    if st.session_state.cfop_cube_string:
        st.divider()
        st.subheader("🧩 CFOP Çözümü (İnsan Yöntemi)")
        st.markdown(
            "Cross → F2L → OLL → PLL aşamalarıyla adım adım çözüm. "
            "Her aşama kendi algoritmasıyla gösterilir."
        )
        render_cfop_ui(st.session_state.cfop_cube_string)

# =====================================================
# ALT BİLGİ
# =====================================================
st.divider()
st.caption("© Kociemba İle Rübik Küp Çözücü | Streamlit + Python | 2026 Enes Özkan")