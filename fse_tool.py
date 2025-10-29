#!/usr/bin/env python3
"""
FSE TOOL (CLI)
===============
Helper esterno invocabile dal gestionale WinDev per:
1) costruire CDA R2 (XML) da un file JSON (dati referto),
2) iniettare il CDA nel PDF come Associated File (AFRelationship=Alternative),
3) firmare il PDF in PAdES,
4) invocare il servizio di Validazione EDS in mTLS,
5) produrre log (JSON) con traceId e workflowInstanceId.

Dipendenze suggerite (requirements.txt):
  pikepdf==9.3.0
  lxml==5.2.2
  pyhanko==0.24.0
  requests==2.32.3

Uso (esempio):
  python fse_tool.py \
    --pdf in/referto.pdf \
    --data in/dati_referto.json \
    --out out/referto_cda_signed.pdf \
    --cda-out out/cda.xml \
    --sign-p12 secrets/cert.p12 --sign-pass "123456" \
    --eds-url https://<gateway-preprod>/eds/validation \
    --mtls-cert secrets/client_cert.pem --mtls-key secrets/client_key.pem --ca secrets/gateway_ca.pem \
    --log out/eds_log.json

Nota: questo script non converte il PDF in PDF/A-3; allega il CDA come file associato e imposta AFRelationship.
Per la piena conformità PDF/A-3 si consiglia un pre-processing del PDF (o partire da un PDF/A) prima dell'iniezione.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from lxml import etree
import pikepdf
from pikepdf import Name, Dictionary, Array, Stream

# pyHanko: firma PAdES
from pyhanko.sign import signers
from pyhanko_certvalidator import ValidationContext
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko.sign.general import simple_cms_attribute
from pyhanko.sign.fields import PdfSignatureMetadata, SigSeedSubFilter
from pyhanko.sign.ades.api import CAdESSignedAttrSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.pkcs12 import load_pkcs12

import requests


# -----------------------------
# 1) COSTRUZIONE CDA R2 (XML)
# -----------------------------

CDA_NS = "urn:hl7-org:v3"
NSMAP = {None: CDA_NS}

def build_cda_xml(data: dict) -> bytes:
    """Costruisce un CDA R2 *minimale di esempio* da un dizionario.
    ATTENZIONE: questo è uno scheletro; va adattato alle IG HL7 Italia per il tipo documento.
    """
    root = etree.Element("ClinicalDocument", nsmap=NSMAP)

    # Header essenziali (placeholders / esempio)
    etree.SubElement(root, "typeId", root="2.16.840.1.113883.1.3", extension="POCD_HD000040")
    etree.SubElement(root, "id", root=data.get("doc_id_root", "1.2.3.4.5"), extension=data.get("doc_id_ext", "ABC-123"))
    etree.SubElement(root, "code", code=data.get("doc_code", "11502-2"), codeSystem="2.16.840.1.113883.6.1", displayName=data.get("doc_display", "Referto"))
    etree.SubElement(root, "title").text = data.get("title", "Referto")
    etree.SubElement(root, "effectiveTime", value=data.get("effectiveTime", datetime.utcnow().strftime("%Y%m%d%H%M%S")))

    # Paziente
    recordTarget = etree.SubElement(root, "recordTarget")
    patientRole = etree.SubElement(recordTarget, "patientRole")
    etree.SubElement(patientRole, "id", extension=data.get("patient_id", "TEMP-PAZ"))
    addr = etree.SubElement(patientRole, "addr")
    etree.SubElement(addr, "city").text = data.get("patient_city", "")
    patient = etree.SubElement(patientRole, "patient")
    name = etree.SubElement(patient, "name")
    etree.SubElement(name, "given").text = data.get("patient_given", "Mario")
    etree.SubElement(name, "family").text = data.get("patient_family", "Rossi")
    etree.SubElement(patient, "administrativeGenderCode", code=data.get("patient_gender", "M"))
    etree.SubElement(patient, "birthTime", value=data.get("patient_birth", "19700101"))

    # Autore
    author = etree.SubElement(root, "author")
    etree.SubElement(author, "time", value=data.get("author_time", datetime.utcnow().strftime("%Y%m%d%H%M%S")))
    assignedAuthor = etree.SubElement(author, "assignedAuthor")
    etree.SubElement(assignedAuthor, "id", extension=data.get("author_id", "AUTH-1"))
    assignedPerson = etree.SubElement(assignedAuthor, "assignedPerson")
    aname = etree.SubElement(assignedPerson, "name")
    etree.SubElement(aname, "given").text = data.get("author_given", "Giulia")
    etree.SubElement(aname, "family").text = data.get("author_family", "Bianchi")

    # Custodian (struttura)
    custodian = etree.SubElement(root, "custodian")
    assignedCustodian = etree.SubElement(custodian, "assignedCustodian")
    representedCustodianOrganization = etree.SubElement(assignedCustodian, "representedCustodianOrganization")
    etree.SubElement(representedCustodianOrganization, "id", extension=data.get("org_id", "ORG-1"))
    etree.SubElement(representedCustodianOrganization, "name").text = data.get("org_name", "Struttura Sanitaria")

    # Body semplificato
    component = etree.SubElement(root, "component")
    structuredBody = etree.SubElement(component, "structuredBody")
    comp_sec = etree.SubElement(structuredBody, "component")
    section = etree.SubElement(comp_sec, "section")
    etree.SubElement(section, "code", code=data.get("section_code", "30954-2"), codeSystem="2.16.840.1.113883.6.1", displayName="Testo referto")
    text = etree.SubElement(section, "text")
    text.text = data.get("report_text", "Referto: ...")

    # Serializza con XML declaration e UTF-8
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


# ---------------------------------------------------------
# 2) INIEZIONE CDA NEL PDF + AFRelationship=Alternative
# ---------------------------------------------------------

def attach_cda_to_pdf(pdf_in: Path, cda_bytes: bytes, pdf_out: Path, embedded_name: str = "cda.xml"):
    """Aggiunge cda.xml come embedded file e imposta l'array AF a livello documento.
    Non converte in PDF/A; si limita a creare l'associazione richiesta.
    """
    with pikepdf.open(str(pdf_in)) as pdf:
        ef_stream = Stream(pdf, cda_bytes)
        # Crea file spec
        filespec = Dictionary({
            Name("Type"): Name("Filespec"),
            Name("F"): embedded_name,
            Name("UF"): embedded_name,
            Name("EF"): Dictionary({Name("F"): ef_stream}),
            Name("AFRelationship"): Name("Alternative")
        })

        # Aggiungi ai Names > EmbeddedFiles
        names = pdf.root.get("Names", Dictionary())
        embedded = names.get(Name("EmbeddedFiles"))
        if embedded is None:
            embedded = Dictionary({Name("Names"): Array([])})
            names[Name("EmbeddedFiles")] = embedded
        name_array = embedded[Name("Names")]
        name_array.append(embedded_name)
        name_array.append(filespec)
        pdf.root[Name("Names")] = names

        # Imposta la chiave /AF nel catalogo del documento
        af_array = pdf.root.get(Name("AF"))
        if af_array is None:
            af_array = Array([])
        af_array.append(filespec)
        pdf.root[Name("AF")] = af_array

        pdf.save(str(pdf_out))


# --------------------
# 3) FIRMA PAdES
# --------------------

def sign_pdf_pades(pdf_in: Path, pdf_out: Path, p12_path: Path, p12_password: str):
    """Firma PAdES-B con pyHanko usando un certificato PKCS#12 (.p12)."""
    with open(p12_path, 'rb') as f:
        p12_bytes = f.read()
    p12 = load_pkcs12(p12_bytes, p12_password.encode('utf-8'))

    w = IncrementalPdfFileWriter(str(pdf_in))

    meta = PdfSignatureMetadata(field_name="Signature1", subfilter=SigSeedSubFilter.PADES, md_algorithm='sha256')

    signer = signers.SimpleSigner(
        signing_cert=p12.signing_cert,
        signing_key=p12.signing_key,
        cert_registry=signers.SimpleCertificateStore(p12.cert_chain or [])
    )

    # Firma in un passaggio
    out = signers.sign_pdf(w, meta, signer=signer)
    with open(pdf_out, 'wb') as outf:
        outf.write(out.getbuffer())


# -----------------------------------------
# 4) VALIDAZIONE EDS (REST mTLS) + LOG JSON
# -----------------------------------------

def validate_eds(eds_url: str, pdf_signed_path: Path, mtls_cert: Path, mtls_key: Path, ca_path: Path) -> dict:
    """Invoca il servizio di Validazione EDS via mTLS.
    Restituisce il payload JSON (dict) e solleva per errori HTTP.
    """
    with open(pdf_signed_path, 'rb') as f:
        data = f.read()

    resp = requests.post(
        eds_url,
        data=data,
        headers={"Content-Type": "application/pdf"},
        cert=(str(mtls_cert), str(mtls_key)),
        verify=str(ca_path),
        timeout=60
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


# --------------------
# CLI principale
# --------------------

def main():
    ap = argparse.ArgumentParser(description="FSE helper: CDA2inPDF + PAdES + Validazione EDS")
    ap.add_argument("--pdf", required=True, help="PDF referto di input")
    ap.add_argument("--data", required=True, help="JSON con i dati per il CDA")
    ap.add_argument("--out", required=True, help="PDF di output firmato")
    ap.add_argument("--cda-out", required=True, help="Percorso dove salvare il cda.xml")

    # Firma PAdES
    ap.add_argument("--sign-p12", required=True, help="PKCS#12 per firma PAdES")
    ap.add_argument("--sign-pass", required=True, help="Password PKCS#12")

    # EDS Validazione (mTLS)
    ap.add_argument("--eds-url", required=True, help="Endpoint Validazione EDS")
    ap.add_argument("--mtls-cert", required=True, help="Cert client (PEM)")
    ap.add_argument("--mtls-key", required=True, help="Key client (PEM)")
    ap.add_argument("--ca", required=True, help="CA gateway (PEM)")

    ap.add_argument("--log", required=True, help="file JSON log esito validazione")

    args = ap.parse_args()

    pdf_in = Path(args.pdf)
    data_json = Path(args.data)
    pdf_out = Path(args.out)
    cda_out = Path(args.cda_out)

    # 1) CDA XML
    data = json.loads(Path(data_json).read_text(encoding='utf-8'))
    cda = build_cda_xml(data)
    Path(cda_out).write_text(cda.decode('utf-8'), encoding='utf-8')

    # 2) Iniezione nel PDF
    tmp_cda_pdf = pdf_in.parent / f"{pdf_in.stem}_cda.pdf"
    attach_cda_to_pdf(pdf_in, cda, tmp_cda_pdf)

    # 3) Firma PAdES
    sign_pdf_pades(tmp_cda_pdf, pdf_out, Path(args.sign_p12), args.sign_pass)

    # 4) Validazione EDS
    result = validate_eds(args.eds_url, pdf_out, Path(args.mtls_cert), Path(args.mtls_key), Path(args.ca))

    # arricchisci con timestamp
    result_wrap = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pdf": str(pdf_out),
        "eds_result": result,
    }

    Path(args.log).write_text(json.dumps(result_wrap, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result_wrap, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
