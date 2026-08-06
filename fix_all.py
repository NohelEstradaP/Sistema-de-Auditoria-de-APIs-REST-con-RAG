#!/usr/bin/env python3
"""
Two fixes:
  1. Citations: move each fn ref to its specific anchor by SPLITTING the run
     that contains the anchor at the exact character position. This prevents
     two fn refs from ending up adjacent when both anchors are in the same run.
  2. Indentation: remove firstLine=709 from pPr; ensure each body paragraph
     starts with exactly 5 literal spaces.
"""
import copy
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
def w(t): return f"{{{W}}}{t}"


# ── Citation helpers ────────────────────────────────────────────────────────────

def run_full_text(run):
    return "".join((t.text or "") for t in run.iter(w("t")))


def split_run_at(run, offset):
    """Split run into two at character offset. Returns (run_before, run_after)."""
    full = run_full_text(run)
    rpr = run.find(w("rPr"))

    def make_run(text):
        r = etree.Element(w("r"))
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
        if text:
            t = etree.SubElement(r, w("t"))
            t.text = text
            if text != text.strip():
                t.set(f"{{{XML_NS}}}space", "preserve")
        return r

    return make_run(full[:offset]), make_run(full[offset:])


def find_fn_run(para, fn_id):
    for child in para:
        fn = child.find(w("footnoteReference"))
        if fn is not None and fn.get(w("id")) == str(fn_id):
            return child
    return None


def move_fn_after_anchor(para, fn_id, anchor):
    """Move fn ref run to immediately after the exact character position where
    `anchor` ends in the accumulated run text, splitting a run if necessary."""
    fn_run = find_fn_run(para, fn_id)
    if fn_run is None:
        print(f"  ✗ fn {fn_id} not found")
        return

    # Build text-position map from all <w:r> children except fn_run
    pos = 0
    run_map = []
    for child in para:
        if child.tag != w("r") or child is fn_run:
            continue
        txt = run_full_text(child)
        run_map.append((child, pos, pos + len(txt)))
        pos += len(txt)

    full_text = "".join(run_full_text(r) for r, _, _ in run_map)

    anchor_pos = full_text.find(anchor)
    if anchor_pos < 0:
        print(f"  ✗ anchor not found for fn {fn_id}: '{anchor[:60]}'")
        return

    anchor_end = anchor_pos + len(anchor)

    # Find which run contains the anchor endpoint
    target_run = None
    offset_in_run = 0
    for run, start, end in run_map:
        if start < anchor_end <= end:
            target_run = run
            offset_in_run = anchor_end - start
            break

    if target_run is None:
        print(f"  ✗ cannot locate target run for fn {fn_id}")
        return

    # Remove fn_run from wherever it currently sits
    para.remove(fn_run)

    children = list(para)
    try:
        tgt_idx = children.index(target_run)
    except ValueError:
        para.append(fn_run)
        print(f"  ✗ target_run lost after fn_run removal for fn {fn_id}")
        return

    run_len = len(run_full_text(target_run))

    if offset_in_run >= run_len:
        # Anchor ends exactly at the run boundary → just insert after
        para.insert(tgt_idx + 1, fn_run)
    else:
        # Anchor ends inside the run → split it
        run_before, run_after = split_run_at(target_run, offset_in_run)
        para.remove(target_run)
        para.insert(tgt_idx,     run_before)
        para.insert(tgt_idx + 1, fn_run)
        para.insert(tgt_idx + 2, run_after)

    print(f"  ✓ fn {fn_id} → after '{anchor[:60]}'")


# ── Citation anchor table ───────────────────────────────────────────────────────
moves = [
    # [7,8]: Jiang(Mistral 7B) / Touvron(Llama 2 — generación anterior)
    ("introdujo el modelo Mistral 7B.", 7),
    ("generación anterior.", 8),

    # [9,10]: Viglianisi / Atlidakis
    ("Viglianisi et al. (2020)", 9),
    ("Atlidakis et al. (2019)", 10),

    # [12,13]: Jiang(Mistral 7B) / Karpukhin(ChromaDB)
    ("Mistral 7B)", 12),
    ("ChromaDB)", 13),

    # [18,19]: Atlidakis(REST vulns) / Zhou(Devign)
    ("vulnerabilidades explotables automáticamente.", 18),
    ("enfoque del presente trabajo.", 19),

    # [39,40,41]: Li(SySeVR) / Fu+Tantithamthavorn(LineVul) / Feng(CodeBERT)
    ("Li et al., 2022)", 39),
    ("Tantithamthavorn, 2022)", 40),
    ("del presente trabajo.", 41),

    # [42,43]: Atlidakis / Viglianisi
    ("Atlidakis et al. (2019)", 42),
    ("Viglianisi et al. (2020)", 43),

    # [44,45]: fn44=Atlidakis(no declaradas) / fn45=Spectral(visibilidad código)
    ("tienen visibilidad del código de implementación.", 45),
    ("no declaradas en la especificación.", 44),

    # [48,49]: Vaswani(Transformer) / Pearce(LLM security)
    ("Vaswani et al. (2017)", 48),
    ("generación de recomendaciones de remediación.", 49),

    # [50,51]: Ji(alucinaciones) / Pearce(referencia actualizada)
    ("en modelos de lenguaje naturales.", 50),
    ("de referencia actualizada.", 51),

    # [52,53]: Devlin(BERT) / Brown(GPT-3 few-shot)
    ("(Devlin et al., 2019).", 52),
    ("(few-shot learning)", 53),

    # [55,56]: Jiang(Q4_K_M) / Touvron(sin modificaciones hardware)
    ("en la mayoría de tareas evaluadas.", 55),
    ("sin modificaciones de hardware.", 56),

    # [58,59,60]: Lewis(RAG) / Gao(prompt) / Borgeaud(RETRO)
    ("conocimiento específico del dominio.", 58),
    ("y diseño del prompt de enriquecimiento.", 59),
    ("hasta corpus de billones de tokens.", 60),

    # [63,64]: Johnson(FAISS) / Karpukhin(DPR filtros)
    ("en lugar de índices de texto pleno.", 63),
    ("con filtros opcionales.", 64),

    # [73,74]: Karpukhin(Cuadro 2) / Reimers(completamente local)
    ("Cuadro No. 2.", 73),
    ("completamente local.", 74),
]

all_targets = {fn_id for _, fn_id in moves}


# ── Load document ───────────────────────────────────────────────────────────────
doc = etree.parse("unpacked_29jul/word/document.xml")
body = doc.getroot().find(f".//{w('body')}")


# ── Fix 1: Move citations ───────────────────────────────────────────────────────
print("=== MOVING CITATIONS ===")
for p in body:
    fnrefs = p.findall(f".//{w('footnoteReference')}")
    if len(fnrefs) < 2:
        continue
    ids_in_para = {int(r.get(w("id"))) for r in fnrefs}
    if not (ids_in_para & all_targets):
        continue
    pt = "".join((t.text or "") for t in p.iter(w("t")))
    print(f"\nPara: '{pt[:80]}'")
    for anchor, fn_id in moves:
        if fn_id in ids_in_para:
            move_fn_after_anchor(p, fn_id, anchor)


# ── Fix 2: Indentation — remove firstLine=709, keep/add 5 literal spaces ───────
print("\n=== FIXING INDENTATION ===")
indent_fixed = 0
for p in body:
    pPr = p.find(w("pPr"))
    if pPr is None:
        continue
    ind = pPr.find(w("ind"))
    if ind is None:
        continue
    fl = ind.get(w("firstLine"))
    if not fl:
        continue

    # Remove firstLine attribute
    del ind.attrib[w("firstLine")]
    if not dict(ind.attrib):   # nothing left on <ind>
        pPr.remove(ind)

    # Ensure first text starts with 5 spaces
    for child in p:
        if child.tag != w("r"):
            continue
        t_elem = child.find(w("t"))
        if t_elem is None:
            continue
        txt = t_elem.text or ""
        if not txt.startswith("     "):
            t_elem.text = "     " + txt
            t_elem.set(f"{{{XML_NS}}}space", "preserve")
        break   # only touch the first text-bearing run

    indent_fixed += 1

print(f"Indentation fixed in {indent_fixed} paragraphs.")


# ── Verify no adjacent fn refs remain ──────────────────────────────────────────
print("\n=== ADJACENT FN REF CHECK ===")
adjacent = 0
for p in body:
    children = list(p)
    for i in range(len(children) - 1):
        c = children[i]
        n = children[i + 1]
        cf = c.find(w("footnoteReference")) if c.tag == w("r") else None
        nf = n.find(w("footnoteReference")) if n.tag == w("r") else None
        if cf is not None and nf is not None:
            pt = "".join((t.text or "") for t in p.iter(w("t")))[:80]
            print(f"  Still adjacent: fn{cf.get(w('id'))} + fn{nf.get(w('id'))} in: '{pt}'")
            adjacent += 1
if adjacent == 0:
    print("  None — all citations properly separated.")


# ── Save ────────────────────────────────────────────────────────────────────────
doc.write("unpacked_29jul/word/document.xml",
          xml_declaration=True, encoding="UTF-8", standalone=True)
print("\n✓ Saved unpacked_29jul/word/document.xml")
