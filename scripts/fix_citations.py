"""
Comprehensive citation fix for anteproyecto docx.
Applies three types of corrections:
  A. Split 14 double-citation paragraphs at natural sentence boundaries
  B. Convert ~40 repeated footnotes to Ibid./Op.Cit. in footnotes.xml
  C. Add fn76/fn77/fn78 to §1.3.8.2 (currently uncited section)
"""

import copy
import sys
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
XML = "http://www.w3.org/XML/1998/namespace"

def w(tag): return f"{{{W}}}{tag}"

# ──────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ──────────────────────────────────────────────────────────────

def get_fn_ids_in_para(para):
    return [int(r.get(w('id'))) for r in para.iter(w('footnoteReference'))]

def get_para_text(para):
    return ''.join(t.text for t in para.iter(w('t')) if t.text)

def make_fn_ref_run(fn_ids, source_rpr=None):
    """Create <w:r> with footnoteReference(s). If source_rpr given, copy it."""
    run = etree.Element(w('r'))
    if source_rpr is not None:
        run.append(copy.deepcopy(source_rpr))
    else:
        rPr = etree.SubElement(run, w('rPr'))
        rStyle = etree.SubElement(rPr, w('rStyle'))
        rStyle.set(w('val'), 'Refdenotaalpie')
    for fid in fn_ids:
        ref = etree.SubElement(run, w('footnoteReference'))
        ref.set(w('id'), str(fid))
    return run


def split_text_run_at(run, anchor_text):
    """
    Split run at end of anchor_text.
    Returns (before_run, after_run). Modifies run in-place as before_run.
    Returns (run, None) if anchor not in run or anchor is at exact end.
    """
    t_elem = run.find(w('t'))
    if t_elem is None or not t_elem.text:
        return run, None

    text = t_elem.text
    pos = text.find(anchor_text)
    if pos == -1:
        return run, None

    split_pos = pos + len(anchor_text)
    before_text = text[:split_pos]
    after_text = text[split_pos:]

    if not after_text:
        return run, None  # anchor is at the end of this run

    # Modify original run (becomes before_run)
    t_elem.text = before_text
    if before_text and (before_text[0] == ' ' or before_text[-1] == ' '):
        t_elem.set(f'{{{XML}}}space', 'preserve')

    # Create after_run (deep copy preserves rPr, annotations, etc.)
    after_run = copy.deepcopy(run)
    at = after_run.find(w('t'))
    at.text = after_text
    if after_text[0] == ' ':
        at.set(f'{{{XML}}}space', 'preserve')
    elif f'{{{XML}}}space' in at.attrib:
        del at.attrib[f'{{{XML}}}space']

    return run, after_run


def find_double_fn_run(para):
    """Find the run containing 2+ footnoteReference elements, return (run, index among para children)."""
    for i, child in enumerate(para):
        if child.tag == w('r'):
            refs = child.findall(w('footnoteReference'))
            if len(refs) >= 2:
                return child, i
    return None, None


def split_para_at_anchor(para, anchor_text, fn_a_ids, fn_b_ids, mode='after'):
    """
    Split para into [para1, para2].

    mode='after': para1 ENDS with anchor_text + fn_a_ids run.
                  para2 starts with text after anchor_text + fn_b_ids run.
    mode='before': para1 ends with text BEFORE anchor_text + fn_a_ids run.
                   para2 STARTS with anchor_text + fn_b_ids run.

    para is modified in-place as para1.
    para2 is returned as a new element.
    """
    fn_run, fn_run_idx = find_double_fn_run(para)
    if fn_run is None:
        print(f"  WARNING: No double-citation run in para, skipping split")
        return [para]

    # Source rPr for new runs (preserves color, etc.)
    source_rpr = fn_run.find(w('rPr'))

    pPr = para.find(w('pPr'))
    all_children = list(para)

    # Find anchor in text runs (only search before fn_run)
    anchor_run_idx = None
    anchor_run_after = None   # text after anchor (goes to para2) in 'after' mode
    anchor_run_before = None  # text before anchor (goes to para1) in 'before' mode

    for i, child in enumerate(all_children):
        if i >= fn_run_idx:
            break
        if child.tag != w('r'):
            continue
        t = child.find(w('t'))
        if t is None or not t.text:
            continue
        if anchor_text in t.text:
            anchor_run_idx = i
            if mode == 'after':
                _, run_after = split_text_run_at(child, anchor_text)
                anchor_run_after = run_after
            else:  # 'before'
                pos = t.text.find(anchor_text)
                if pos == 0:
                    # anchor is at the very start of the run; nothing stays in para1 from this run
                    anchor_run_before = None  # don't include this run in para1
                else:
                    before_text = t.text[:pos]
                    after_text = t.text[pos:]
                    # Modify run to have only the before part
                    t.text = before_text
                    if before_text[0] == ' ' or before_text[-1] == ' ':
                        t.set(f'{{{XML}}}space', 'preserve')
                    # Create after run with anchor onwards
                    after_run = copy.deepcopy(child)
                    at = after_run.find(w('t'))
                    at.text = after_text
                    if after_text[0] == ' ':
                        at.set(f'{{{XML}}}space', 'preserve')
                    elif f'{{{XML}}}space' in at.attrib:
                        del at.attrib[f'{{{XML}}}space']
                    anchor_run_before = child   # keep in para1
                    # Replace child in para with anchor_run_before only (already done)
                    # The after_run becomes the FIRST element of para2
                    anchor_run_after_for_para2 = after_run
                    anchor_run_idx_split = anchor_run_idx  # para1 includes runs up to here
                    # Reconfigure: in 'before' mode, para2 starts with anchor_run_after_for_para2
                    anchor_run_after = after_run
            break

    if anchor_run_idx is None:
        print(f"  WARNING: Anchor not found: '{anchor_text}'")
        return [para]

    if mode == 'before' and anchor_run_before is None:
        # anchor was at start of the run: para1 ends BEFORE this run entirely
        # para2 includes run[anchor_run_idx] onwards
        # Adjust: para1 includes up to anchor_run_idx - 1
        effective_last_idx = anchor_run_idx - 1
        # children for para2 start at anchor_run_idx
        para2_start_children = all_children[anchor_run_idx: fn_run_idx]
    elif mode == 'before':
        # run was split: para1 includes up to anchor_run_before (same run, now truncated)
        effective_last_idx = anchor_run_idx
        # anchor_run_after goes first in para2
        para2_start_children = [anchor_run_after] + all_children[anchor_run_idx + 1: fn_run_idx]
    else:
        # mode == 'after'
        effective_last_idx = anchor_run_idx
        para2_start_children = []
        if anchor_run_after is not None:
            para2_start_children.append(anchor_run_after)
        para2_start_children += all_children[anchor_run_idx + 1: fn_run_idx]

    # Trailing children (after fn_run: commentRangeEnd, etc.)
    trailing = all_children[fn_run_idx + 1:]

    # Build para2 XML
    para2 = etree.Element(w('p'))
    for attr, val in para.attrib.items():
        para2.set(attr, val)

    if pPr is not None:
        para2.append(copy.deepcopy(pPr))

    for c in para2_start_children:
        para2.append(c)

    fn_b_run = make_fn_ref_run(fn_b_ids, source_rpr)
    para2.append(fn_b_run)

    for c in trailing:
        para2.append(c)

    # Rebuild para1 (modify in place)
    # Remove everything after effective_last_idx (including fn_run)
    to_remove = all_children[effective_last_idx + 1:]
    for c in to_remove:
        try:
            para.remove(c)
        except ValueError:
            pass

    fn_a_run = make_fn_ref_run(fn_a_ids, source_rpr)
    para.append(fn_a_run)

    return [para, para2]


def insert_fn_ref_after(para, anchor_text, fn_ids):
    """
    Insert a footnoteReference run immediately after anchor_text within para.
    Used for adding citations to §1.3.8.2 without splitting the paragraph.
    """
    all_children = list(para)

    for i, child in enumerate(all_children):
        if child.tag != w('r'):
            continue
        t = child.find(w('t'))
        if t is None or not t.text:
            continue
        if anchor_text in t.text:
            # Split the run
            _, run_after = split_text_run_at(child, anchor_text)

            # Create footnoteReference run (no color - these are new correct citations)
            fn_run = make_fn_ref_run(fn_ids)

            # Insert fn_run and run_after after child
            child_idx = list(para).index(child)
            para.insert(child_idx + 1, fn_run)
            if run_after is not None:
                para.insert(child_idx + 2, run_after)
            return True

    print(f"  WARNING: inline anchor not found: '{anchor_text}'")
    return False


# ──────────────────────────────────────────────────────────────
# PART A: PARAGRAPH SPLITS
# ──────────────────────────────────────────────────────────────

# Each entry: ( (fn_ids_tuple), [(anchor, fn_a_ids, fn_b_ids, mode), ...] )
# mode='after'  → para1 ends WITH anchor text (default)
# mode='before' → para2 STARTS WITH anchor text (use when anchor spans run boundary)
PARA_SPLITS = [
    # [7, 8]: Jiang (Mistral) | Touvron (Llama 2)
    ((7, 8), [
        ("de la generación anterior.", [7], [8], 'after'),
    ]),
    # [9, 10]: Viglianisi | Atlidakis
    # "Django REST Framework." spans two runs; split before " Viglianisi"
    ((9, 10), [
        (" Viglianisi et al. (2020)", [9], [10], 'before'),
    ]),
    # [12, 13]: Jiang | Karpukhin
    ((12, 13), [
        ("en entornos de producción.", [12], [13], 'after'),
    ]),
    # [18, 19]: Atlidakis | Zhou
    ((18, 19), [
        ("vulnerabilidades explotables automáticamente.", [18], [19], 'after'),
    ]),
    # [39, 40, 41]: LI SySeVR | FU LineVul | FENG CodeBERT
    ((39, 40, 41), [
        ("(P = TP / (TP + FP)).", [39], [40, 41], 'after'),   # first split
        ("enfoques puramente basados en reglas.", [40], [41], 'after'),  # second split on para2
    ]),
    # [42, 43]: Atlidakis | Viglianisi
    ((42, 43), [
        ("comportamientos que indiquen vulnerabilidades.", [42], [43], 'after'),
    ]),
    # [44, 45]: Atlidakis | Viglianisi
    # "DEFAULT_THROTTLE_CLASSES" is a run without period; split before " Spectral"
    ((44, 45), [
        (" Spectral y 42Crunch", [44], [45], 'before'),
    ]),
    # [48, 49]: Vaswani | Pearce
    ((48, 49), [
        ("Vaswani et al. (2017).", [48], [49], 'after'),
    ]),
    # [50, 51]: Ji | Pearce
    ((50, 51), [
        ("en modelos de lenguaje naturales.", [50], [51], 'after'),
    ]),
    # [52, 53]: Devlin | Brown
    ((52, 53), [
        ("(Devlin et al., 2019).", [52], [53], 'after'),
    ]),
    # [55, 56]: Jiang (Ibid.) | Touvron
    ((55, 56), [
        ("sin modificaciones de hardware.", [55], [56], 'after'),
    ]),
    # [58, 59, 60]: Lewis | Gao | Borgeaud
    ((58, 59, 60), [
        ("conocimiento específico del dominio.", [58], [59, 60], 'after'),  # first split
        (" Borgeaud et al. (2022)", [59], [60], 'before'),  # second split on para2
    ]),
    # [63, 64]: Karpukhin | Johnson
    ((63, 64), [
        ("sin conectividad a internet.", [63], [64], 'after'),
    ]),
    # [73, 74]: Karpukhin | Reimers
    ((73, 74), [
        ("Cuadro No. 2.", [73], [74], 'after'),
    ]),
]


def apply_para_splits(doc_root):
    paras = doc_root.findall(f".//{w('p')}")

    for target_ids_tuple, split_ops in PARA_SPLITS:
        target_ids_set = set(target_ids_tuple)

        # Find the paragraph with these exact footnote IDs
        found_para = None
        found_parent = None
        found_idx = None

        for para in paras:
            fn_ids = get_fn_ids_in_para(para)
            if set(fn_ids) == target_ids_set:
                found_para = para
                found_parent = para.getparent()
                found_idx = list(found_parent).index(para)
                break

        if found_para is None:
            print(f"  SKIP: para with fn{target_ids_tuple} not found")
            continue

        print(f"  Splitting fn{target_ids_tuple}...")

        # Apply all split operations for this entry
        # After the first split, the second split applies to the SECOND resulting paragraph
        current_para = found_para
        current_idx = found_idx
        all_new_paras = [current_para]

        for op_num, (anchor, fn_a_ids, fn_b_ids, mode) in enumerate(split_ops):
            print(f"    op{op_num+1}: split {mode} '{anchor[:50]}', fn_a={fn_a_ids}, fn_b={fn_b_ids}")
            result = split_para_at_anchor(current_para, anchor, fn_a_ids, fn_b_ids, mode)

            if len(result) == 2:
                para1, para2 = result
                # Insert para2 after para1 in the parent
                insert_idx = list(found_parent).index(para1) + 1
                found_parent.insert(insert_idx, para2)
                all_new_paras = [p for p in all_new_paras if p is not para1]
                all_new_paras.append(para1)
                all_new_paras.append(para2)
                # Next split operation (if any) targets para2
                current_para = para2
            else:
                print(f"    WARNING: split op{op_num+1} failed, skipping")


# ──────────────────────────────────────────────────────────────
# PART B: IBID./OP.CIT. FOOTNOTE REPLACEMENTS
# ──────────────────────────────────────────────────────────────

# Map of fn_id → replacement text
IBID_OPCIT = {
    11: "TOUVRON, Hugo, et al., Op. Cit.",
    12: "JIANG, Albert Q., et al., Op. Cit.",
    14: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    15: "VIGLIANISI, Emanuele, et al., Op. Cit.",
    16: "FIELDING, Roy Thomas, Op. Cit.",
    17: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    18: "ATLIDAKIS, Vaggelis, et al., Op. Cit.",
    20: "OWASP Foundation, Op. Cit.",
    21: "Ibid.",
    22: "Ibid.",
    23: "Ibid.",
    24: "Ibid.",
    25: "Ibid.",
    26: "Ibid.",
    27: "Ibid.",
    28: "Ibid.",
    29: "Ibid.",
    30: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    31: "PEARCE, Hammond, et al., Op. Cit.",
    33: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    34: "PEARCE, Hammond, et al., Op. Cit.",
    35: "Ibid.",
    36: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    37: "Ibid.",
    38: "LI, Zhen, et al., Op. Cit.",
    42: "ATLIDAKIS, Vaggelis, et al., Op. Cit.",
    43: "VIGLIANISI, Emanuele, et al., Op. Cit.",
    44: "ATLIDAKIS, Vaggelis, et al., Op. Cit.",
    45: "VIGLIANISI, Emanuele, et al., Op. Cit.",
    46: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    47: "ATLIDAKIS, Vaggelis, et al., Op. Cit.",
    49: "PEARCE, Hammond, et al., Op. Cit.",
    51: "PEARCE, Hammond, et al., Op. Cit.",
    54: "JIANG, Albert Q., et al., Op. Cit.",
    55: "Ibid.",
    56: "TOUVRON, Hugo, et al., Op. Cit.",
    57: "LEWIS, Patrick, et al., Op. Cit.",
    58: "Ibid.",
    62: "REIMERS, Nils y GUREVYCH, Iryna, Op. Cit.",
    63: "KARPUKHIN, Vladimir, et al., Op. Cit.",
    65: "LEWIS, Patrick, et al., Op. Cit.",
    66: "Ibid.",
    67: "CHESS, Brian y McGRAW, Gary, Op. Cit.",
    68: "Ibid.",
    70: "PEARCE, Hammond, et al., Op. Cit.",
    71: "LEWIS, Patrick, et al., Op. Cit.",
    72: "FAWCETT, Tom, Op. Cit.",
    73: "KARPUKHIN, Vladimir, et al., Op. Cit.",
    74: "REIMERS, Nils y GUREVYCH, Iryna, Op. Cit.",
    75: "LEWIS, Patrick, et al., Op. Cit.",
}


def replace_fn_text(fn_elem, new_text):
    """
    Replace all text content in a footnote element with a single text run.
    Preserves the <w:footnoteRef/> run. Does NOT touch <w:color> elements.
    """
    # Find the paragraph inside the footnote
    para = fn_elem.find(w('p'))
    if para is None:
        return

    # Find the footnoteRef run (must keep it)
    fn_ref_run = None
    for r in para.findall(w('r')):
        if r.find(w('footnoteRef')) is not None:
            fn_ref_run = r
            break

    # Get pPr
    pPr = para.find(w('pPr'))

    # Remove all children of para
    for child in list(para):
        para.remove(child)

    # Re-add pPr
    if pPr is not None:
        para.append(pPr)

    # Re-add footnoteRef run
    if fn_ref_run is not None:
        para.append(fn_ref_run)

    # Add the new text run
    new_run = etree.SubElement(para, w('r'))
    new_t = etree.SubElement(new_run, w('t'))
    new_t.text = new_text
    if new_text[0] == ' ':
        new_t.set(f'{{{XML}}}space', 'preserve')


def apply_ibid_opcit(fn_root):
    for fn_elem in fn_root.findall(f".//{w('footnote')}"):
        fid_str = fn_elem.get(w('id'))
        if fid_str is None:
            continue
        try:
            fid = int(fid_str)
        except ValueError:
            continue
        if fid in IBID_OPCIT:
            new_text = IBID_OPCIT[fid]
            print(f"  fn{fid}: → '{new_text}'")
            replace_fn_text(fn_elem, new_text)


# ──────────────────────────────────────────────────────────────
# PART C: ADD fn76, fn77, fn78 TO §1.3.8.2
# ──────────────────────────────────────────────────────────────

NEW_FOOTNOTES = {
    76: "LEWIS, Patrick, et al., Op. Cit.",
    77: "PEARCE, Hammond, et al., Op. Cit.",
    78: "FAWCETT, Tom, Op. Cit.",
}

# Anchors in §1.3.8.2 paragraph (all in one paragraph).
# "trazabilidad" is an italic run; " de fuentes (TF)." is in the next run.
SECTION_1382_ANCHORS = [
    ("contribución individual.", 76),
    (" de fuentes (TF).", 77),
    ("independientemente del evaluador.", 78),
]


def add_new_footnotes(fn_root):
    """Append fn76, fn77, fn78 to footnotes.xml root."""
    # Find the last real footnote to copy its structure as a template
    last_fn = None
    for fn_elem in fn_root.findall(w('footnote')):
        fid_str = fn_elem.get(w('id'))
        if fid_str and fid_str not in ('-1', '0'):
            last_fn = fn_elem

    if last_fn is None:
        print("  ERROR: no existing footnotes found")
        return

    # Get a simple footnote (fn75) as template
    template_fn = None
    for fn_elem in fn_root.findall(w('footnote')):
        if fn_elem.get(w('id')) == '75':
            template_fn = fn_elem
            break

    for fn_id, text in NEW_FOOTNOTES.items():
        new_fn = etree.SubElement(fn_root, w('footnote'))
        new_fn.set(w('id'), str(fn_id))

        para = etree.SubElement(new_fn, w('p'))
        pPr = etree.SubElement(para, w('pPr'))
        pStyle = etree.SubElement(pPr, w('pStyle'))
        pStyle.set(w('val'), 'Textonotapie')

        fn_ref_run = etree.SubElement(para, w('r'))
        fn_ref_rPr = etree.SubElement(fn_ref_run, w('rPr'))
        fn_ref_rStyle = etree.SubElement(fn_ref_rPr, w('rStyle'))
        fn_ref_rStyle.set(w('val'), 'Refdenotaalpie')
        etree.SubElement(fn_ref_run, w('footnoteRef'))

        text_run = etree.SubElement(para, w('r'))
        t_elem = etree.SubElement(text_run, w('t'))
        t_elem.text = text
        if text[0] == ' ':
            t_elem.set(f'{{{XML}}}space', 'preserve')

        print(f"  Added fn{fn_id}: '{text}'")


def insert_section_1382_refs(doc_root):
    """Insert fn76/77/78 references in the §1.3.8.2 paragraph."""
    paras = doc_root.findall(f".//{w('p')}")

    # Find the paragraph containing all three anchor texts
    target_para = None
    for para in paras:
        text = get_para_text(para)
        if ("contribución individual" in text
                and "trazabilidad de fuentes" in text
                and "independientemente del evaluador" in text):
            target_para = para
            break

    if target_para is None:
        print("  ERROR: §1.3.8.2 paragraph not found")
        return

    print(f"  Found §1.3.8.2 paragraph, inserting fn76/77/78...")

    # Insert in reverse order to avoid index shifting issues
    for anchor, fn_id in reversed(SECTION_1382_ANCHORS):
        result = insert_fn_ref_after(target_para, anchor, [fn_id])
        if result:
            print(f"    Inserted fn{fn_id} after '{anchor}'")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    import os

    base = "/Users/nohelestradap/Documents/tesis_proyecto/unpacked_fix"
    doc_path = os.path.join(base, "word/document.xml")
    fn_path = os.path.join(base, "word/footnotes.xml")

    # Parse (using iterparse-compatible parser to preserve namespaces)
    doc_parser = etree.XMLParser(remove_blank_text=False)
    fn_parser = etree.XMLParser(remove_blank_text=False)

    doc_tree = etree.parse(doc_path, doc_parser)
    fn_tree = etree.parse(fn_path, fn_parser)

    doc_root = doc_tree.getroot()
    fn_root = fn_tree.getroot()

    print("\n=== PART A: Splitting double-citation paragraphs ===")
    apply_para_splits(doc_root)

    print("\n=== PART B: Replacing repeated footnotes with Ibid./Op.Cit. ===")
    apply_ibid_opcit(fn_root)

    print("\n=== PART C: Adding fn76/77/78 to §1.3.8.2 ===")
    add_new_footnotes(fn_root)
    insert_section_1382_refs(doc_root)

    # Save
    doc_tree.write(doc_path, xml_declaration=True, encoding='UTF-8', standalone=True)
    fn_tree.write(fn_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    print("\n=== DONE ===")
    print(f"Saved: {doc_path}")
    print(f"Saved: {fn_path}")


if __name__ == "__main__":
    main()
