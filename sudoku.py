"""
Sudoku Çözücü & Üretici — Streamlit versiyonu
pip install streamlit reportlab openpyxl
"""

import streamlit as st
import streamlit.components.v1 as components
import random, copy, time, io

st.set_page_config(page_title="Sudoku", page_icon="🎯", layout="centered")

# ── Sudoku Motoru ──────────────────────────────────────────────────────────────
class SudokuEngine:
    @staticmethod
    def is_valid(board, row, col, num):
        if num in board[row]: return False
        if num in [board[r][col] for r in range(9)]: return False
        br, bc = (row // 3) * 3, (col // 3) * 3
        for r in range(br, br+3):
            for c in range(bc, bc+3):
                if board[r][c] == num: return False
        return True

    @staticmethod
    def solve(board, find_all=False):
        solutions = []
        def _solve(b):
            if find_all and len(solutions) > 1:
                return
            for row in range(9):
                for col in range(9):
                    if b[row][col] == 0:
                        nums = list(range(1, 10))
                        random.shuffle(nums)
                        for num in nums:
                            if SudokuEngine.is_valid(b, row, col, num):
                                b[row][col] = num
                                _solve(b)
                                if not find_all and solutions:
                                    return
                                b[row][col] = 0
                        return
            solutions.append(copy.deepcopy(b))
        _solve(board)
        return solutions

    @staticmethod
    def has_unique_solution(board):
        sols = SudokuEngine.solve(copy.deepcopy(board), find_all=True)
        return len(sols) == 1

    @classmethod
    def generate(cls, difficulty="orta"):
        board = [[0]*9 for _ in range(9)]
        sols  = cls.solve(board)
        full  = sols[0]
        remove_counts = {"kolay": 36, "orta": 46, "zor": 54, "uzman": 58}
        to_remove = remove_counts.get(difficulty, 46)
        puzzle = copy.deepcopy(full)
        cells  = list(range(81))
        random.shuffle(cells)
        removed = 0
        for idx in cells:
            if removed >= to_remove: break
            r, c   = divmod(idx, 9)
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            if cls.has_unique_solution(puzzle):
                removed += 1
            else:
                puzzle[r][c] = backup
        return puzzle, full

    @staticmethod
    def get_errors(board, solution):
        errors = set()
        for r in range(9):
            for c in range(9):
                if board[r][c] != 0 and board[r][c] != solution[r][c]:
                    errors.add((r, c))
        return errors

    @staticmethod
    def count_filled(board):
        return sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)

# ── PDF Export ─────────────────────────────────────────────────────────────────
def export_pdf(puzzles_data, buf, per_page=1, show_solution=False):
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    W, H = A4
    c = rl_canvas.Canvas(buf, pagesize=A4)

    def draw_sudoku(c, board, x0, y0, size, title=""):
        cell = size / 9
        if title:
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#333333"))
            c.drawString(x0, y0 + size + 14, title)
        c.setFillColor(colors.white)
        c.rect(x0, y0, size, size, fill=1, stroke=0)
        for row in range(9):
            for col in range(9):
                val = board[row][col]
                if val != 0:
                    cx = x0 + col * cell + cell/2
                    cy = y0 + (8 - row) * cell + cell/2 - 5
                    c.setFont("Helvetica-Bold", int(cell * 0.45))
                    c.setFillColor(colors.HexColor("#1a1a2e"))
                    c.drawCentredString(cx, cy, str(val))
        c.setStrokeColor(colors.HexColor("#aaaaaa"))
        c.setLineWidth(0.5)
        for i in range(10):
            if i % 3 != 0:
                c.line(x0+i*cell, y0, x0+i*cell, y0+size)
                c.line(x0, y0+i*cell, x0+size, y0+i*cell)
        c.setStrokeColor(colors.HexColor("#1a1a2e"))
        c.setLineWidth(2.5)
        for i in range(0, 10, 3):
            c.line(x0+i*cell, y0, x0+i*cell, y0+size)
            c.line(x0, y0+i*cell, x0+size, y0+i*cell)

    if per_page == 1:
        for puzzle, solution, difficulty in puzzles_data:
            margin = 72
            size   = W - 2 * margin
            c.setFont("Helvetica-Bold", 18)
            c.setFillColor(colors.HexColor("#1a1a2e"))
            c.drawCentredString(W/2, H - 50, "SUDOKU")
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#666666"))
            c.drawCentredString(W/2, H - 68, f"Zorluk: {difficulty.capitalize()}")
            y0 = (H - size) / 2
            draw_sudoku(c, puzzle, margin, y0, size)
            filled = SudokuEngine.count_filled(puzzle)
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#999999"))
            c.drawCentredString(W/2, 30, f"Doldurulacak: {81 - filled} hücre")
            c.showPage()
            if show_solution:
                c.setFont("Helvetica-Bold", 18)
                c.setFillColor(colors.HexColor("#1a1a2e"))
                c.drawCentredString(W/2, H - 50, "ÇÖZÜM")
                c.setFont("Helvetica", 11)
                c.setFillColor(colors.HexColor("#666666"))
                c.drawCentredString(W/2, H - 68, f"Zorluk: {difficulty.capitalize()}")
                draw_sudoku(c, solution, margin, y0, size)
                c.showPage()
    elif per_page == 4:
        for page_start in range(0, len(puzzles_data), 4):
            batch = puzzles_data[page_start:page_start+4]
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor("#1a1a2e"))
            c.drawCentredString(W/2, H - 35, "SUDOKU")
            margin  = 30; gap = 20
            size    = (W - 2*margin - gap) / 2
            positions = [
                (margin,              H/2 + gap/2),
                (margin + size + gap, H/2 + gap/2),
                (margin,              H/2 - size - gap/2),
                (margin + size + gap, H/2 - size - gap/2),
            ]
            for i, (puzzle, solution, difficulty) in enumerate(batch):
                x0, y0 = positions[i]
                draw_sudoku(c, puzzle, x0, y0, size,
                            title=f"#{page_start+i+1} — {difficulty.capitalize()}")
            c.showPage()
            if show_solution:
                c.setFont("Helvetica-Bold", 14)
                c.setFillColor(colors.HexColor("#1a1a2e"))
                c.drawCentredString(W/2, H - 35, "ÇÖZÜMLER")
                for i, (puzzle, solution, difficulty) in enumerate(batch):
                    x0, y0 = positions[i]
                    draw_sudoku(c, solution, x0, y0, size,
                                title=f"#{page_start+i+1} Çözüm")
                c.showPage()
    c.save()

# ── Excel Export ───────────────────────────────────────────────────────────────
def export_excel(puzzles_data, buf, show_solution=False):
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    thick = Side(style="medium", color="1a1a2e")
    thin  = Side(style="thin",   color="aaaaaa")

    def get_border(row, col):
        top    = thick if row % 3 == 0 else thin
        left   = thick if col % 3 == 0 else thin
        bottom = thick if row == 8 else (thick if (row+1) % 3 == 0 else thin)
        right  = thick if col == 8 else (thick if (col+1) % 3 == 0 else thin)
        return Border(top=top, left=left, bottom=bottom, right=right)

    def write_board(ws, board, given_board, start_row, start_col):
        for r in range(9):
            for c in range(9):
                cell = ws.cell(row=start_row+r, column=start_col+c)
                val  = board[r][c]
                cell.value     = val if val != 0 else None
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border    = get_border(r, c)
                if given_board and given_board[r][c] != 0:
                    cell.font = Font(name="Calibri", size=11, bold=True,  color="1a1a2e")
                    cell.fill = PatternFill("solid", fgColor="EFEFEF")
                elif val != 0:
                    cell.font = Font(name="Calibri", size=11, bold=False, color="1f6feb")
                else:
                    cell.font = Font(name="Calibri", size=11)
                    cell.fill = PatternFill("solid", fgColor="FFFFFF")
        for c in range(9):
            ws.column_dimensions[get_column_letter(start_col+c)].width = 4.0
        for r in range(9):
            ws.row_dimensions[start_row+r].height = 22

    PER_PAGE    = 6
    COL_OFFSETS = [1, 11]
    ROW_OFFSETS = [3, 14, 25]
    POSITIONS   = [(r, c) for r in range(3) for c in range(2)]

    def make_sheet(ws, batch, page_start, is_solution=False):
        ws.sheet_view.showGridLines = False
        ws.row_dimensions[1].height = 20
        ws.merge_cells("A1:S1")
        t = ws.cell(row=1, column=1,
                    value="ÇÖZÜMLER" if is_solution else
                    f"SUDOKU — {batch[0][2].upper()}")
        t.font      = Font(name="Calibri", size=13, bold=True,
                           color="0f9b8e" if is_solution else "1a1a2e")
        t.alignment = Alignment(horizontal="center")
        for slot_idx, (puzzle, solution, difficulty) in enumerate(batch):
            ri, ci    = POSITIONS[slot_idx]
            start_col = COL_OFFSETS[ci]
            start_row = ROW_OFFSETS[ri]
            num       = page_start + slot_idx + 1
            board     = solution if is_solution else puzzle
            given     = puzzle   if is_solution else None
            hdr_row   = start_row - 1
            ws.merge_cells(start_row=hdr_row, start_column=start_col,
                           end_row=hdr_row,   end_column=start_col+8)
            hdr = ws.cell(row=hdr_row, column=start_col,
                          value=f"#{num} {'Çözüm' if is_solution else difficulty.capitalize()}")
            hdr.font      = Font(name="Calibri", size=9, bold=True,
                                 color="0f9b8e" if is_solution else "555555")
            hdr.alignment = Alignment(horizontal="left")
            ws.row_dimensions[hdr_row].height = 14
            write_board(ws, board, given, start_row, start_col)
        ws.page_setup.orientation = "portrait"
        ws.page_setup.paperSize   = ws.PAPERSIZE_A4
        ws.page_setup.fitToPage   = True
        ws.page_setup.fitToWidth  = 1
        ws.page_setup.fitToHeight = 1

    for page_idx, page_start in enumerate(range(0, len(puzzles_data), PER_PAGE)):
        batch    = puzzles_data[page_start:page_start+PER_PAGE]
        name     = f"Sayfa {page_idx+1}" if len(puzzles_data) > PER_PAGE else "Bulmacalar"
        make_sheet(wb.create_sheet(title=name), batch, page_start, is_solution=False)
        if show_solution:
            sol_name = (f"Çözümler {page_idx+1}"
                        if len(puzzles_data) > PER_PAGE else "Çözümler")
            make_sheet(wb.create_sheet(title=sol_name), batch, page_start, is_solution=True)

    wb.save(buf)

# ── Board HTML ─────────────────────────────────────────────────────────────────
def board_html(board, given, solution, selected):
    has_sol = any(solution[r][c] for r in range(9) for c in range(9))
    errors  = SudokuEngine.get_errors(board, solution) if has_sol else set()

    sel_r = selected[0] if selected else -1
    sel_c = selected[1] if selected else -1

    html = """
<style>
  body { margin:0; background:#1a1a2e; display:flex; justify-content:center; padding:8px; }
  table { border-collapse:collapse; }
  td {
    width:52px; height:52px; text-align:center; vertical-align:middle;
    font-family:'Consolas',monospace; font-size:22px; font-weight:bold;
    border:1px solid #3a3a5a; background:#16213e; color:#16213e;
    transition: background 0.1s;
  }
  tr:nth-child(3n) td        { border-bottom:3px solid #c0c0d0; }
  tr:nth-child(3n+1) td      { border-top:3px solid #c0c0d0; }
  td:nth-child(3n)            { border-right:3px solid #c0c0d0; }
  td:nth-child(3n+1)          { border-left:3px solid #c0c0d0; }
  .sel   { background:#2a3a6a !important; }
  .hi    { background:#1e2a4a !important; }
  .given { color:#ffffff; }
  .user  { color:#64b5f6; font-weight:normal; }
  .err   { color:#ef5350 !important; }
  .empty { color:#3a3a5a; font-size:10px; }
</style>
<table>
"""
    for r in range(9):
        html += "<tr>"
        for c in range(9):
            val = board[r][c]
            cls = []
            if r == sel_r and c == sel_c:
                cls.append("sel")
            elif sel_r >= 0 and (r == sel_r or c == sel_c or
                (r//3 == sel_r//3 and c//3 == sel_c//3)):
                cls.append("hi")

            if (r, c) in errors:
                cls.append("err")

            if val != 0:
                if given[r][c]:
                    cls.append("given")
                else:
                    cls.append("user")
                text = str(val)
            else:
                cls.append("empty")
                text = "·"

            html += f'<td class="{" ".join(cls)}">{text}</td>'
        html += "</tr>"
    html += "</table>"
    return html

# ── Session State ──────────────────────────────────────────────────────────────
def init():
    if "board" not in st.session_state:
        st.session_state.board      = [[0]*9 for _ in range(9)]
        st.session_state.given      = [[False]*9 for _ in range(9)]
        st.session_state.solution   = [[0]*9 for _ in range(9)]
        st.session_state.selected   = (0, 0)
        st.session_state.start_time = None
        st.session_state.difficulty = "orta"
        st.session_state.msg        = ("", "")   # (text, type)
        _new_game("orta")

def _new_game(diff):
    with st.spinner("Bulmaca üretiliyor..."):
        puzzle, solution = SudokuEngine.generate(diff)
    st.session_state.board      = copy.deepcopy(puzzle)
    st.session_state.solution   = solution
    st.session_state.given      = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
    st.session_state.selected   = (0, 0)
    st.session_state.start_time = time.time()
    st.session_state.difficulty = diff
    filled = SudokuEngine.count_filled(puzzle)
    st.session_state.msg = (f"Yeni oyun · {diff.capitalize()} · {81-filled} hücre boş", "info")

def input_num(n):
    r, c = st.session_state.selected
    if not st.session_state.given[r][c]:
        st.session_state.board[r][c] = n
        _check_complete()

def _check_complete():
    board    = st.session_state.board
    solution = st.session_state.solution
    if all(board[r][c] != 0 for r in range(9) for c in range(9)):
        errors = SudokuEngine.get_errors(board, solution)
        if not errors:
            elapsed = time.time() - st.session_state.start_time
            m, s = divmod(int(elapsed), 60)
            st.session_state.msg = (f"🎉 Tebrikler! {m:02d}:{s:02d} sürede tamamladın!", "success")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  section.main > div { padding-top: 1rem; }
  div[data-testid="stHorizontalBlock"] > div { gap: 0.3rem; }
  .stButton button {
    width: 100%; border-radius: 8px; font-family: 'Consolas', monospace;
    font-weight: bold; border: none;
  }
  .stButton button:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ── Ana Uygulama ───────────────────────────────────────────────────────────────
init()

st.markdown("## 🎯 Sudoku")

# ── Üst kontroller ──
c1, c2, c3, c4, c5, c6 = st.columns([2,1,1,1,1,1])
with c1:
    diff = st.selectbox("Zorluk", ["kolay","orta","zor","uzman"],
                        index=["kolay","orta","zor","uzman"].index(st.session_state.difficulty),
                        label_visibility="collapsed")
with c2:
    if st.button("🎲 Yeni", use_container_width=True):
        _new_game(diff)
        st.rerun()
with c3:
    if st.button("✓ Çöz", use_container_width=True):
        st.session_state.board = copy.deepcopy(st.session_state.solution)
        st.session_state.msg   = ("Çözüm gösterildi!", "info")
with c4:
    if st.button("💡 İpucu", use_container_width=True):
        empties = [(r,c) for r in range(9) for c in range(9)
                   if st.session_state.board[r][c] == 0]
        if empties:
            r, c = random.choice(empties)
            st.session_state.board[r][c] = st.session_state.solution[r][c]
            st.session_state.selected    = (r, c)
            st.session_state.msg = (f"İpucu: Satır {r+1}, Sütun {c+1} → {st.session_state.solution[r][c]}", "info")
            _check_complete()
with c5:
    if st.button("🗑 Temizle", use_container_width=True):
        for r in range(9):
            for c in range(9):
                if not st.session_state.given[r][c]:
                    st.session_state.board[r][c] = 0
        st.session_state.msg = ("Temizlendi.", "info")
with c6:
    if st.button("✔ Kontrol", use_container_width=True):
        errors = SudokuEngine.get_errors(st.session_state.board, st.session_state.solution)
        if not errors:
            filled = SudokuEngine.count_filled(st.session_state.board)
            st.session_state.msg = (
                "🎉 Mükemmel! Sudoku tamamlandı!" if filled == 81 else "✓ Şu ana kadar hata yok!",
                "success"
            )
        else:
            st.session_state.msg = (f"⚠ {len(errors)} hatalı hücre var!", "error")

# ── Timer ──
if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    m, s = divmod(int(elapsed), 60)
    st.caption(f"⏱ {m:02d}:{s:02d}  |  Zorluk: **{st.session_state.difficulty.capitalize()}**")

# ── Tahta ──
components.html(
    board_html(
        st.session_state.board,
        st.session_state.given,
        st.session_state.solution,
        st.session_state.selected,
    ),
    height=500,
)

# ── Hücre seçici ──
st.markdown("**Hücre seç:**")
sc1, sc2 = st.columns(2)
with sc1:
    sel_r = st.selectbox("Satır (1-9)", range(1,10),
                         index=st.session_state.selected[0],
                         key="sel_r", label_visibility="visible")
with sc2:
    sel_c = st.selectbox("Sütun (1-9)", range(1,10),
                         index=st.session_state.selected[1],
                         key="sel_c", label_visibility="visible")
st.session_state.selected = (sel_r - 1, sel_c - 1)

# ── Numpad ──
st.markdown("**Sayı gir:**")
ncols = st.columns(10)
for i, n in enumerate(range(1, 10)):
    # Kalan sayı göstergesi
    cnt = sum(1 for r in range(9) for c in range(9) if st.session_state.board[r][c] == n)
    rem = 9 - cnt
    with ncols[i]:
        label = f"{n}\n✓" if rem <= 0 else f"{n}\n{rem}"
        if st.button(label, key=f"n{n}", use_container_width=True):
            input_num(n)
            st.rerun()
with ncols[9]:
    if st.button("⌫\n–", key="del", use_container_width=True):
        input_num(0)
        st.rerun()

# ── Mesaj ──
msg_text, msg_type = st.session_state.msg
if msg_text:
    if msg_type == "success":
        st.success(msg_text)
    elif msg_type == "error":
        st.error(msg_text)
    else:
        st.info(msg_text)

# ── Export ──
st.markdown("---")
with st.expander("📤 Dışa Aktar"):
    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        export_count = st.number_input("Bulmaca sayısı", 1, 200, 1)
    with ex2:
        per_page = st.radio("Sayfa başına", [1, 4], horizontal=True)
    with ex3:
        show_sol = st.checkbox("Çözüm dahil", value=True)

    def gen_puzzles(count):
        data = []
        bar  = st.progress(0, text="Üretiliyor...")
        for i in range(count):
            p, s = SudokuEngine.generate(st.session_state.difficulty)
            data.append((p, s, st.session_state.difficulty))
            bar.progress((i+1)/count, text=f"{i+1}/{count} üretildi")
        bar.empty()
        return data

    ep1, ep2 = st.columns(2)
    with ep1:
        if st.button("📄 PDF Oluştur", use_container_width=True):
            puzzles = gen_puzzles(export_count)
            buf = io.BytesIO()
            export_pdf(puzzles, buf, per_page=per_page, show_solution=show_sol)
            buf.seek(0)
            st.download_button(
                "⬇ PDF İndir", buf, "sudoku.pdf", "application/pdf",
                use_container_width=True
            )
    with ep2:
        if st.button("📊 Excel Oluştur", use_container_width=True):
            puzzles = gen_puzzles(export_count)
            buf = io.BytesIO()
            export_excel(puzzles, buf, show_solution=show_sol)
            buf.seek(0)
            st.download_button(
                "⬇ Excel İndir", buf, "sudoku.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
