#!/usr/bin/env python3
"""Apply all reviewer corrections from comments to the 29-jul docx."""
from lxml import etree
import re, copy

DOCX_DIR = "unpacked_29jul/word"
W  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A  = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC= "http://schemas.openxmlformats.org/drawingml/2006/picture"
WPD= "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

def w(t): return f"{{{W}}}{t}"
def a(t): return f"{{{A}}}{t}"
def pic_ns(t): return f"{{{PIC}}}{t}"

# ── helpers ──────────────────────────────────────────────────────────────────
def para_text(p):
    return "".join((t.text or "") for t in p.iter(w("t")))

def run_text(r):
    t = r.find(w("t"))
    return t.text if t is not None else ""

def remove_bold(run):
    rpr = run.find(w("rPr"))
    if rpr is not None:
        for tag in (w("b"), w("bCs")):
            b = rpr.find(tag)
            if b is not None:
                rpr.remove(b)

def ensure_rpr(run):
    rpr = run.find(w("rPr"))
    if rpr is None:
        rpr = etree.SubElement(run, w("rPr"))
    return rpr

def set_italic(run):
    rpr = ensure_rpr(run)
    if rpr.find(w("i")) is None:
        etree.SubElement(rpr, w("i"))
    if rpr.find(w("iCs")) is None:
        etree.SubElement(rpr, w("iCs"))

def set_size(run, size_half_pts):
    """size_half_pts: 20 = 10pt, 24 = 12pt"""
    rpr = ensure_rpr(run)
    for tag in (w("sz"), w("szCs")):
        el = rpr.find(tag)
        if el is None:
            el = etree.SubElement(rpr, tag)
        el.set(w("val"), str(size_half_pts))

def make_simple_run(text, bold=False, italic=False, size=None):
    r = etree.Element(w("r"))
    rpr = etree.SubElement(r, w("rPr"))
    if bold:
        etree.SubElement(rpr, w("b"))
        etree.SubElement(rpr, w("bCs"))
    if italic:
        etree.SubElement(rpr, w("i"))
        etree.SubElement(rpr, w("iCs"))
    if size:
        s = etree.SubElement(rpr, w("sz"))
        s.set(w("val"), str(size))
        sc = etree.SubElement(rpr, w("szCs"))
        sc.set(w("val"), str(size))
    t = etree.SubElement(r, w("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r

def make_para(text, style=None, center=False, indent=None, bold=False,
              italic=False, size=None):
    p = etree.Element(w("p"))
    ppr = etree.SubElement(p, w("pPr"))
    if style:
        ps = etree.SubElement(ppr, w("pStyle"))
        ps.set(w("val"), style)
    if center:
        jc = etree.SubElement(ppr, w("jc"))
        jc.set(w("val"), "center")
    if indent is not None:
        ind = etree.SubElement(ppr, w("ind"))
        ind.set(w("firstLine"), str(indent))
    etree.SubElement(ppr, w("contextualSpacing"))
    p.append(make_simple_run(text, bold=bold, italic=italic, size=size))
    return p

def make_list_para(text_runs, num_id=2):
    """text_runs: list of (text, italic_bool)"""
    p = etree.Element(w("p"))
    ppr = etree.SubElement(p, w("pPr"))
    ps = etree.SubElement(ppr, w("pStyle"))
    ps.set(w("val"), "ListParagraph")
    np_ = etree.SubElement(ppr, w("numPr"))
    ilvl = etree.SubElement(np_, w("ilvl"))
    ilvl.set(w("val"), "0")
    nid = etree.SubElement(np_, w("numId"))
    nid.set(w("val"), str(num_id))
    etree.SubElement(ppr, w("contextualSpacing"))
    for text, italic in text_runs:
        p.append(make_simple_run(text, italic=italic))
    return p

# ── parse documents ──────────────────────────────────────────────────────────
doc_tree = etree.parse(f"{DOCX_DIR}/document.xml")
doc_root = doc_tree.getroot()
fn_tree  = etree.parse(f"{DOCX_DIR}/footnotes.xml")
fn_root  = fn_tree.getroot()
num_tree = etree.parse(f"{DOCX_DIR}/numbering.xml")

body    = doc_root.find(f".//{w('body')}")
kids    = list(body)

# ── 1. FIX DATE on cover page ────────────────────────────────────────────────
for p in kids:
    if para_text(p) == "Guatemala, julio de 2026":
        for r in p.findall(w("r")):
            t = r.find(w("t"))
            if t is not None and "julio de 2026" in (t.text or ""):
                t.text = t.text.replace("julio de 2026", "29 de julio de 2026")
        break
print("✓ Date fixed")

# ── 2. DELETE 'innecesario' paragraph ────────────────────────────────────────
for p in list(body):
    if "El presente documento se organiza de la siguiente manera" in para_text(p):
        body.remove(p)
        break
print("✓ Deleted 'innecesario' paragraph")

# Refresh kids list after deletion
kids = list(body)

# ── 3. RED TEXT → LOWERCASE + REMOVE RED COLOR ───────────────────────────────
# Words marked EE0000 are incorrectly capitalized; lowercase them
for p in kids:
    for r in p.findall(w("r")):
        rpr = r.find(w("rPr"))
        if rpr is None: continue
        color = rpr.find(w("color"))
        if color is not None and color.get(w("val")) == "EE0000":
            t = r.find(w("t"))
            if t is not None and t.text:
                # Only lowercase letters that were incorrectly capitalised
                # (punctuation-only runs just lose the color)
                text = t.text
                # If the run is entirely punctuation, just remove color
                if not re.search(r'[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]', text):
                    rpr.remove(color)
                    continue
                t.text = text[0] + text[1:].lower() if len(text) > 1 else text.lower()
            # Remove red color
            rpr.remove(color)
print("✓ Red-text capitalization fixed")

# ── 4. GREEN HIGHLIGHT → ITALIC + REMOVE HIGHLIGHT ───────────────────────────
for p in kids:
    for r in p.findall(w("r")):
        rpr = r.find(w("rPr"))
        if rpr is None: continue
        hl = rpr.find(w("highlight"))
        if hl is not None and hl.get(w("val")) == "green":
            # Add italic if not already
            if rpr.find(w("i")) is None:
                etree.SubElement(rpr, w("i"))
            if rpr.find(w("iCs")) is None:
                etree.SubElement(rpr, w("iCs"))
            rpr.remove(hl)
print("✓ Green highlights → italic")

# ── 5. REPLACE "APIs" → "API" AND "URIs" → "URI" ─────────────────────────────
for p in kids:
    for t in p.iter(w("t")):
        if t.text:
            t.text = re.sub(r'\bAPIs\b', 'API', t.text)
            t.text = re.sub(r'\bURIs\b', 'URI', t.text)
# Also fix in footnotes
for t in fn_root.iter(w("t")):
    if t.text:
        t.text = re.sub(r'\bAPIs\b', 'API', t.text)
        t.text = re.sub(r'\bURIs\b', 'URI', t.text)
print("✓ APIs→API, URIs→URI")

# ── 6. REMOVE BOLD FROM FIGURE CAPTIONS (Figura No. 1 and 2) ─────────────────
for p in kids:
    txt = para_text(p)
    if txt.strip() in ("Figura No. 1", "Figura No. 2",
                       "ARQUITECTURA DEL SISTEMA DE AUDITORÍA DE SEGURIDAD",
                       "FLUJO DEL PIPELINE DE GENERACIÓN AUMENTADA POR RECUPERACIÓN (RAG)"):
        for r in p.findall(w("r")):
            remove_bold(r)
print("✓ Bold removed from figure captions")

# ── 7. ADD INTRO PARAGRAPH BEFORE FIGURA NO. 1 ───────────────────────────────
fig1_idx = None
for i, p in enumerate(kids):
    if para_text(p).strip() == "Figura No. 1":
        fig1_idx = i
        break
if fig1_idx is not None:
    intro_text = (
        "La Figura No. 1 presenta la arquitectura general del sistema de auditoría "
        "propuesto, compuesta por cinco módulos que operan en secuencia: el analizador "
        "estático, el analizador dinámico, la base de conocimiento RAG, el pipeline "
        "de generación con el modelo de lenguaje y el generador de reportes."
    )
    new_para = make_para(intro_text, indent=709)
    body.insert(fig1_idx, new_para)
    kids = list(body)
    print("✓ Intro paragraph added before Figure 1")

# ── 8. REMOVE BOLD FROM CUADRO No. 1, 2, 3 ──────────────────────────────────
for p in kids:
    txt = para_text(p).strip()
    if txt in ("Cuadro No. 1", "Cuadro No. 2", "Cuadro No. 3"):
        for r in p.findall(w("r")):
            remove_bold(r)
print("✓ Bold removed from Cuadro titles")

# ── 9. SET "Fuente: Propia." TO SIZE 10 ──────────────────────────────────────
for p in kids:
    txt = para_text(p).strip()
    if txt == "Fuente: Propia.":
        for r in p.findall(w("r")):
            set_size(r, 20)   # 20 half-pts = 10pt
print("✓ 'Fuente: Propia.' set to size 10")

# ── 10. CONVERT PROCEDURE PARAGRAPH TO BULLET LIST ───────────────────────────
proc_idx = None
for i, p in enumerate(kids):
    if "El procedimiento de investigación se estructura" in para_text(p):
        proc_idx = i
        break

if proc_idx is not None:
    proc_para = kids[proc_idx]
    # Collect all runs (with text and italic state)
    all_runs = []
    for r in proc_para.findall(w("r")):
        t = r.find(w("t"))
        if t is None or not t.text: continue
        rpr = r.find(w("rPr"))
        is_italic = rpr is not None and rpr.find(w("i")) is not None
        is_comment_ref = rpr is not None and (
            rpr.find(w("rStyle")) is not None and
            rpr.find(w("rStyle")).get(w("val")) == "CommentReference"
        ) or r.find(w("commentReference")) is not None
        if is_comment_ref: continue
        all_runs.append((t.text, is_italic))

    # Join all text to split by step markers
    full_text = "".join(text for text, _ in all_runs)

    # Split text at markers like "; (1) ", ": (1) ", "; y (11) "
    # Intro sentence ends at ":"
    intro_match = re.match(r'^(.+?secuenciales:)\s*', full_text)
    intro = intro_match.group(1) if intro_match else "El procedimiento de investigación se estructura en once etapas secuenciales:"

    # Split into numbered items
    item_pattern = re.compile(r';\s*(?:y\s+)?\((\d+)\)\s*')
    # Find start after intro
    rest = full_text[len(intro_match.group(0)):]
    # First item starts here
    items_raw = re.split(r';\s*(?:y\s+)?\((\d+)\)\s*', rest)
    # Rebuild items list
    items = []
    first_item_text = re.sub(r'^\s*\(1\)\s*', '', rest.split(';')[0] if ';' in rest else rest)

    # Better split: find all "(N)" markers
    all_parts = re.split(r'(?:;\s*(?:y\s+)?)?\((\d+)\)\s*', full_text[len(intro):])
    # all_parts[0] is empty (text before first (1)), then alternates: num, text
    step_items = []
    i2 = 1  # skip empty first
    while i2 < len(all_parts) - 1:
        num = all_parts[i2]
        text_part = all_parts[i2+1]
        # Remove trailing semicolon
        text_part = text_part.rstrip('; ')
        step_items.append(text_part)
        i2 += 2

    # Now for each item, determine which runs contain italic text
    # Re-map runs to text positions
    def get_runs_for_text(target_text, source_runs):
        """Given a target text string, find and return (text_segment, italic) pairs."""
        result = []
        # Try to find italic portions
        combined = "".join(t for t, _ in source_runs)
        pos = combined.find(target_text)
        if pos < 0:
            return [(target_text, False)]
        # Walk runs
        char_pos = 0
        target_start = pos
        target_end = pos + len(target_text)
        result_runs = []
        for text, italic in source_runs:
            run_start = char_pos
            run_end = char_pos + len(text)
            # Overlap with target?
            overlap_start = max(run_start, target_start)
            overlap_end = min(run_end, target_end)
            if overlap_start < overlap_end:
                segment = text[overlap_start - run_start: overlap_end - run_start]
                if segment:
                    result_runs.append((segment, italic))
            char_pos = run_end
            if char_pos >= target_end:
                break
        return result_runs if result_runs else [(target_text, False)]

    # Remove the original procedure paragraph and insert new ones
    body.remove(proc_para)
    kids = list(body)

    # Find new index (it was removed so search for the next elem after its position)
    # Insert at proc_idx position
    # Create intro paragraph
    intro_p = make_para(intro, indent=709)
    body.insert(proc_idx, intro_p)

    # Create list items
    for step_i, item_text in enumerate(step_items):
        item_text = item_text.strip().rstrip('.')
        runs_for_item = get_runs_for_text(item_text, all_runs)
        list_p = make_list_para(runs_for_item)
        body.insert(proc_idx + 1 + step_i, list_p)

    kids = list(body)
    print(f"✓ Procedure converted to {len(step_items)}-item bullet list")

# ── 11. ADD MISSING CITATION (ablation study, Comment 10) ────────────────────
# Find ablation study paragraph and add footnote reference after first sentence
# First determine next footnote ID
all_fn_ids = [int(fn.get(w("id"), 0)) for fn in fn_root.findall(w("footnote"))
              if fn.get(w("id"), "").lstrip("-").isdigit()]
next_fn_id = max(all_fn_ids) + 1

# The citation will be LEWIS Op. Cit. (abbreviated since already cited)
lewis_opcit = ("LEWIS, Patrick, et al. Retrieval-Augmented Generation for "
               "Knowledge-Intensive NLP Tasks. Op. Cit.")

for p in kids:
    txt = para_text(p)
    if ("Un estudio de ablación es un experimento" in txt and
            "para cuantificar su contribución individual" in txt):
        # Find run containing "para cuantificar su contribución individual."
        target = "para cuantificar su contribución individual"
        for r in p.findall(w("r")):
            t = r.find(w("t"))
            if t is not None and target in (t.text or ""):
                # Split the run text: insert fnRef after "...individual."
                full = t.text
                idx_cut = full.find(target) + len(target) + 1  # +1 for period
                if idx_cut <= len(full):
                    before = full[:idx_cut]
                    after  = full[idx_cut:]
                    t.text = before
                    # Build footnote reference run
                    fn_run = etree.Element(w("r"))
                    fn_rpr = etree.SubElement(fn_run, w("rPr"))
                    rs = etree.SubElement(fn_rpr, w("rStyle"))
                    rs.set(w("val"), "FootnoteReference")
                    sz = etree.SubElement(fn_rpr, w("sz"))
                    sz.set(w("val"), "24")
                    szcs = etree.SubElement(fn_rpr, w("szCs"))
                    szcs.set(w("val"), "24")
                    fnref = etree.SubElement(fn_run, w("footnoteReference"))
                    fnref.set(w("id"), str(next_fn_id))
                    # Insert fn_run after current run
                    r_idx = list(p).index(r)
                    p.insert(r_idx + 1, fn_run)
                    if after:
                        after_run = make_simple_run(after)
                        p.insert(r_idx + 2, after_run)
                    # Create footnote definition
                    new_fn = etree.SubElement(fn_root, w("footnote"))
                    new_fn.set(w("id"), str(next_fn_id))
                    new_fn.set(w("type"), "footnote") if False else None
                    fn_p = etree.SubElement(new_fn, w("p"))
                    fn_ppr = etree.SubElement(fn_p, w("pPr"))
                    fn_pstyle = etree.SubElement(fn_ppr, w("pStyle"))
                    fn_pstyle.set(w("val"), "FootnoteText")
                    # footnote mark run
                    fn_mark_run = etree.SubElement(fn_p, w("r"))
                    fn_mark_rpr = etree.SubElement(fn_mark_run, w("rPr"))
                    fn_mark_rs = etree.SubElement(fn_mark_rpr, w("rStyle"))
                    fn_mark_rs.set(w("val"), "FootnoteReference")
                    fn_mark = etree.SubElement(fn_mark_run, w("footnoteMark"))
                    # text run
                    fn_text_run = etree.SubElement(fn_p, w("r"))
                    fn_text_rpr = etree.SubElement(fn_text_run, w("rPr"))
                    fn_sz = etree.SubElement(fn_text_rpr, w("sz"))
                    fn_sz.set(w("val"), "20")
                    fn_szcs = etree.SubElement(fn_text_rpr, w("szCs"))
                    fn_szcs.set(w("val"), "20")
                    fn_t = etree.SubElement(fn_text_run, w("t"))
                    fn_t.text = lewis_opcit
                    fn_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                break
        break
print("✓ Missing citation added to ablation study")

# ── 12. REPEATED CITATIONS → IBID. / OP. CIT. ───────────────────────────────
# Build: fn_id → full_text from footnotes.xml
fn_id_to_text = {}
for fn in fn_root.findall(w("footnote")):
    fid = fn.get(w("id"))
    text = "".join((t.text or "") for t in fn.iter(w("t")))
    # Skip the footnote mark character at the start
    text = re.sub(r'^\s*', '', text)
    fn_id_to_text[fid] = text

# Normalize: group by first 50 chars of text (dedup key)
def source_key(text):
    return text[:55].strip()

def first_author(text):
    m = re.match(r'^([A-ZÁÉÍÓÚÜÑ][^,\.]{1,30})', text)
    return m.group(1).strip() if m else text.split()[0]

# Build: source_key → first_id (lowest-numbered id per group)
from collections import defaultdict
key_to_ids = defaultdict(list)
for fid, text in fn_id_to_text.items():
    if fid in ('-1', '0'): continue
    key_to_ids[source_key(text)].append(int(fid))

# For each group, the first_id is the min
key_to_first_id = {k: str(min(ids)) for k, ids in key_to_ids.items()}
# Reverse: id → source_key
id_to_key = {str(id_val): k for k, ids in key_to_ids.items() for id_val in ids}

# Walk document body, collect footnote references IN ORDER
fn_refs_in_order = []
for elem in doc_root.iter():
    if elem.tag == w("footnoteReference"):
        fid = elem.get(w("id"))
        if fid and fid not in ('-1', '0'):
            fn_refs_in_order.append(fid)

# Now update footnote texts for repeated citations
prev_key = None
for fid in fn_refs_in_order:
    if fid in ('-1', '0'): continue
    text = fn_id_to_text.get(fid, "")
    key = id_to_key.get(fid)
    if key is None: continue
    first_id = key_to_first_id.get(key)

    if fid == first_id:
        # First citation: keep full text
        prev_key = key
        continue

    # Repeated citation
    fn_elem = fn_root.find(f".//{w('footnote')}[@{w('id')}='{fid}']")
    if fn_elem is None:
        prev_key = key
        continue

    author = first_author(fn_id_to_text.get(first_id, fid))
    if key == prev_key:
        new_text = "Ibid."
    else:
        new_text = f"{author}, Op. Cit."

    # Update all w:t elements in this footnote
    for t_elem in fn_elem.iter(w("t")):
        if t_elem.text and len(t_elem.text.strip()) > 2:  # skip footnote mark char
            t_elem.text = new_text
            new_text = ""  # only first substantial t gets the text

    prev_key = key

print("✓ Repeated citations → Ibid./Op. Cit.")

# ── 13. BIBLIOGRAPHY RESTRUCTURE: REMOVE STRUCK HEADERS, ADD "Documentos Electrónicos" ──
# Remove struck-through category paragraphs (Tesis Doctoral, Estándar Técnico, Artículos...)
kids = list(body)
to_remove = []
for p in kids:
    ppr = p.find(w("pPr"))
    has_ppr_strike = ppr is not None and ppr.find(f".//{w('strike')}") is not None
    txt = para_text(p).strip()
    if has_ppr_strike and txt in ("Tesis Doctoral", "Estándar Técnico",
                                   "Artículos en Revistas y Conferencias"):
        to_remove.append(p)

for p in to_remove:
    body.remove(p)
print(f"✓ Removed {len(to_remove)} struck bibliography category headers")

# Add "Documentos Electrónicos" header before the bibliography entries
kids = list(body)
bib_idx = None
for i, p in enumerate(kids):
    if para_text(p).strip() == "BIBLIOGRAFÍA":
        bib_idx = i
        break

if bib_idx is not None:
    # Find first bib entry (FIELDING...)
    for i in range(bib_idx + 1, len(kids)):
        txt = para_text(kids[i]).strip()
        if txt and not txt == "":
            # Insert "Documentos Electrónicos" header before first entry
            header_p = make_para("Documentos Electrónicos", bold=False)
            body.insert(i, header_p)
            break
    print("✓ 'Documentos Electrónicos' header added to bibliography")

# ── 14. ADD BORDERS TO FIGURE IMAGES ─────────────────────────────────────────
NS_A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"

for p in doc_root.iter(w("p")):
    for spPr in p.iter(f"{{{NS_PIC}}}spPr"):
        # Add a solid black 1pt border line
        prstGeom = spPr.find(f"{{{NS_A}}}prstGeom")
        if prstGeom is not None:
            # Check border doesn't already exist
            ln_existing = spPr.find(f"{{{NS_A}}}ln")
            if ln_existing is None:
                ln = etree.SubElement(spPr, f"{{{NS_A}}}ln")
                ln.set("w", "12700")  # 1pt in EMU
                solidFill = etree.SubElement(ln, f"{{{NS_A}}}solidFill")
                srgbClr = etree.SubElement(solidFill, f"{{{NS_A}}}srgbClr")
                srgbClr.set("val", "000000")
print("✓ Borders added to figures")

# ── 15. FIX FIRST-LINE INDENT ON PARAGRAPHS MISSING IT ───────────────────────
# Add indent to body paragraphs that don't have it and are not headings/list/centered
HEADING_STYLES = {"Heading1","Heading2","Heading3","Heading4","Heading5",
                  "Heading6","ListParagraph","FootnoteText"}
for p in doc_root.iter(w("p")):
    ppr = p.find(w("pPr"))
    if ppr is None:
        ppr = etree.SubElement(p, w("pPr"))
        p.insert(0, ppr)
    # Skip headings
    pstyle = ppr.find(w("pStyle"))
    if pstyle is not None and pstyle.get(w("val")) in HEADING_STYLES:
        continue
    # Skip centered paragraphs
    jc = ppr.find(w("jc"))
    if jc is not None and jc.get(w("val")) == "center":
        continue
    # Skip list paragraphs
    numPr = ppr.find(w("numPr"))
    if numPr is not None:
        continue
    # Skip empty paragraphs
    txt = para_text(p).strip()
    if not txt:
        continue
    # Skip headings by checking if first run is bold with specific patterns
    # (numbered headings like "1. MARCO DE REFERENCIA")
    if re.match(r'^\d+\.?\s*[A-ZÁÉÍÓÚÜÑ]', txt) and len(txt) < 80:
        # Could be heading - check if bold
        first_r = p.find(w("r"))
        if first_r is not None:
            rpr_check = first_r.find(w("rPr"))
            if rpr_check is not None and rpr_check.find(w("b")) is not None:
                continue
    # Skip bibliography entries (they start with APELLIDO,)
    if re.match(r'^[A-ZÁÉÍÓÚÜÑ]{2,}[^a-záéíóúüñ]', txt) and "Disponible en:" in txt:
        continue
    # Add indent if not present
    ind = ppr.find(w("ind"))
    if ind is None:
        ind = etree.SubElement(ppr, w("ind"))
        ind.set(w("firstLine"), "709")
    elif ind.get(w("firstLine")) is None and ind.get(w("left")) is None:
        ind.set(w("firstLine"), "709")
print("✓ First-line indentation applied")

# ── SAVE ─────────────────────────────────────────────────────────────────────
doc_tree.write(f"{DOCX_DIR}/document.xml",
               xml_declaration=True, encoding="UTF-8", standalone=True)
fn_tree.write(f"{DOCX_DIR}/footnotes.xml",
              xml_declaration=True, encoding="UTF-8", standalone=True)
print("\n✓ All changes saved to document.xml and footnotes.xml")
