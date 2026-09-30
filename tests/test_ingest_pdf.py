import pathlib


def test_read_pdf_subset():
    """pypdf extrae texto real de los 4 PDFs del subset ES."""
    from src.ingest import read_pdf_text

    for rel in [
        "data/acme/Customer_Support/Support_SOP.pdf",
        "data/acme/Customer_Support/Escalation_Guide.pdf",
        "data/acme/Customer_Support/SLA.pdf",
        "data/acme/HR/Leave_Policy.pdf",
    ]:
        t = read_pdf_text(pathlib.Path(rel))
        assert len(t.strip()) > 1000, f"poco texto en {rel}"
        assert "AcmeTech" in t, f"sin marca AcmeTech en {rel}"


def test_collect_files_finds_md_and_pdf_recursive():
    from src.ingest import collect_files

    files = collect_files(pathlib.Path("data/acme"))
    pdfs = [f for f in files if f.suffix == ".pdf"]
    assert len(pdfs) == 26, f"esperaba 26 PDFs, hallé {len(pdfs)}"
    assert any("Customer_Support" in str(f) for f in pdfs)


def test_collect_files_old_dirs_still_work():
    from src.ingest import collect_files

    es = collect_files(pathlib.Path("data/es"))
    assert any(f.suffix == ".md" for f in es), "data/es/*.md ya no se indexa"


def test_teaching_fixtures_never_reach_the_index():
    """cats/gatos/rag-intro son material de clase, no corpus: no se indexan."""
    from src.ingest import collect_lang_files

    fixtures = {"cats.md", "gatos.md", "rag-intro.md"}
    for lang in ("en", "es"):
        names = {f.name for f in collect_lang_files(lang)}
        assert not (names & fixtures), f"{lang}: el corpus contiene fixtures {names & fixtures}"
        assert names, f"{lang}: el corpus real quedó vacío"
