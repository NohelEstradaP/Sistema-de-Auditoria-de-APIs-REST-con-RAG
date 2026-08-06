#!/usr/bin/env python3
"""Move double citations to their individual anchor points.

Strategy:
  1. For each paragraph whose fn refs are bundled in a single <w:r>, split them
     into individual <w:r> elements — one per <w:footnoteReference>.
  2. Move each individual fn run to its designated anchor position in the paragraph.
"""
import copy
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def w(t): return f"{{{W}}}{t}"
def para_text(p):
    return "".join((t.text or "") for t in p.iter(w("t")))

doc = etree.parse("unpacked_29jul/word/document.xml")
body = doc.getroot().find(f".//{w('body')}")

# ── Step 1: split bundled runs ─────────────────────────────────────────────────
for p in body:
    for child in list(p):
        fn_refs = child.findall(w("footnoteReference"))
        if len(fn_refs) <= 1:
            continue
        rpr = child.find(w("rPr"))
        idx = list(p).index(child)
        p.remove(child)
        for i, fnref in enumerate(fn_refs):
            new_run = etree.Element(w("r"))
            if rpr is not None:
                new_run.append(copy.deepcopy(rpr))
            new_fn = etree.SubElement(new_run, w("footnoteReference"))
            new_fn.set(w("id"), fnref.get(w("id")))
            p.insert(idx + i, new_run)
        ids = [r.get(w("id")) for r in fn_refs]
        print(f"Split run → {ids} in para: '{para_text(p)[:60]}'")

# ── Step 2: move each fn to its anchor ────────────────────────────────────────

def find_fn_run(para, fn_id):
    """Return the direct <w:r> child of para containing footnoteReference fn_id."""
    for child in para:
        fn = child.find(w("footnoteReference"))
        if fn is not None and fn.get(w("id")) == str(fn_id):
            return child
    return None


def move_fn_after_anchor(para, fn_id, anchor):
    """Move the fn run to immediately after the run whose cumulative text first
    contains `anchor`. Text is accumulated left-to-right, skipping fn runs."""
    fn_run = find_fn_run(para, fn_id)
    if fn_run is None:
        print(f"  ✗ fn {fn_id} not found in para")
        return

    # Find anchor position (before removal, so indices are stable)
    accumulated = ""
    target_run = None
    for child in para:
        if child.tag != w("r") or child is fn_run:
            continue
        accumulated += "".join((t.text or "") for t in child.iter(w("t")))
        if anchor in accumulated:
            target_run = child
            break

    if target_run is None:
        print(f"  ✗ anchor not found for fn {fn_id}: '{anchor[:60]}'")
        return

    # Remove fn run, then re-find target and insert after it
    para.remove(fn_run)
    children = list(para)
    try:
        insert_at = children.index(target_run) + 1
    except ValueError:
        insert_at = len(children)
    para.insert(insert_at, fn_run)
    print(f"  ✓ fn {fn_id} → after '{anchor[:60]}'")


# ── Citation anchor table ─────────────────────────────────────────────────────
# Each tuple: (anchor_text, fn_id)
# Tuples within a group are processed in the order listed.
moves = [
    # [7,8]: Jiang(Mistral 7B) / Touvron(Llama 2 — generación anterior)
    ("introdujo el modelo Mistral 7B.", 7),
    ("generación anterior.", 8),

    # [9,10]: Viglianisi(RESTTESTGEN) / Atlidakis(RESTler)
    ("Viglianisi et al. (2020)", 9),
    ("Atlidakis et al. (2019)", 10),

    # [12,13]: Jiang(Mistral 7B) / Karpukhin(ChromaDB)
    ("Mistral 7B)", 12),
    ("ChromaDB)", 13),

    # [18,19]: Atlidakis(REST vulns) / Zhou(Devign — detección estática)
    ("vulnerabilidades explotables automáticamente.", 18),
    ("enfoque del presente trabajo.", 19),

    # [39,40,41]: Li(SySeVR) / Fu+Tantithamthavorn(LineVul) / Feng(CodeBERT)
    ("Li et al., 2022)", 39),
    ("Tantithamthavorn, 2022)", 40),
    ("del presente trabajo.", 41),

    # [42,43]: Atlidakis(RESTler) / Viglianisi(RESTTESTGEN)
    ("Atlidakis et al. (2019)", 42),
    ("Viglianisi et al. (2020)", 43),

    # [44,45]: fn44=Atlidakis(no declaradas) / fn45=Spectral(visibilidad código)
    ("tienen visibilidad del código de implementación.", 45),
    ("no declaradas en la especificación.", 44),

    # [48,49]: Vaswani(Transformer) / Pearce(LLM security)
    ("Vaswani et al. (2017)", 48),
    ("generación de recomendaciones de remediación.", 49),

    # [50,51]: Ji(alucinaciones survey) / Pearce(referencia actualizada)
    ("en modelos de lenguaje naturales.", 50),
    ("de referencia actualizada.", 51),

    # [52,53]: Devlin(BERT) / Brown(GPT-3 few-shot)
    ("(Devlin et al., 2019).", 52),
    ("(few-shot learning)", 53),

    # [55,56]: Jiang(Q4_K_M tareas) / Touvron(sin modificaciones hardware)
    ("en la mayoría de tareas evaluadas.", 55),
    ("sin modificaciones de hardware.", 56),

    # [58,59,60]: Lewis(RAG paradigm) / Gao(prompt design) / Borgeaud(RETRO)
    ("conocimiento específico del dominio.", 58),
    ("y diseño del prompt de enriquecimiento.", 59),
    ("hasta corpus de billones de tokens.", 60),

    # [63,64]: Johnson(FAISS índices) / Karpukhin(DPR filtros)
    ("en lugar de índices de texto pleno.", 63),
    ("con filtros opcionales.", 64),

    # [73,74]: Karpukhin(Cuadro No. 2) / Reimers(completamente local)
    ("Cuadro No. 2.", 73),
    ("completamente local.", 74),
]

# Build a per-paragraph index of which fn_ids are relevant
all_targets = {fn_id for _, fn_id in moves}

for p in body:
    fnrefs = p.findall(f".//{w('footnoteReference')}")
    if len(fnrefs) < 2:
        continue
    ids_in_para = {int(r.get(w("id"))) for r in fnrefs}
    if not (ids_in_para & all_targets):
        continue
    print(f"\nPara: '{para_text(p)[:80]}'")
    for anchor, fn_id in moves:
        if fn_id in ids_in_para:
            move_fn_after_anchor(p, fn_id, anchor)

doc.write("unpacked_29jul/word/document.xml",
          xml_declaration=True, encoding="UTF-8", standalone=True)
print("\n✓ All citations moved and saved.")
