<p align="center">
  <img src="https://via.placeholder.com/200x80.png?text=Pa.Ser+Consulting+Group" alt="Pa.Ser Consulting Group">
</p>

# 🩺 FSE Helper – Modulo Python
### by **Pa.Ser Consulting Group della dott.ssa Pier Paola Lai**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Stato-In%20fase%20di%20accreditamento-yellow.svg)](#-accreditamento-fse)

> 🔧 **Sito ufficiale:** [paserconsulting.it](https://paserconsulting.it) — *attualmente in ristrutturazione*

---

## 🧩 Descrizione

**FSE Helper** è un modulo Python sviluppato da **Pa.Ser Consulting Group della dott.ssa Pier Paola Lai**  
per l’integrazione dei referti clinici con il **Fascicolo Sanitario Elettronico 2.0 (FSE 2.0)**.  

Fa parte del gestionale sanitario **WinPreGest** e consente:
- la generazione automatica del documento **CDA R2** a partire da un file JSON;
- l’iniezione del CDA nel PDF come *Associated File* (AFRelationship=Alternative);
- la firma digitale **PAdES-B** tramite certificato PKCS#12;
- la validazione tramite il servizio **EDS** in ambiente **mTLS** (gateway FSE 2.0);
- la produzione dei log tecnici con `traceId` e `workflowInstanceId`.

Il modulo è stato realizzato in conformità con le linee guida AgID e SOGEI per l’interoperabilità dei referti verso il FSE.

---

## ⚙️ Installazione

Richiede **Python 3.12+**

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt

Le principali dipendenze includono:

pikepdf → gestione PDF/A e file associati

lxml → generazione CDA XML

pyHanko → firma digitale PAdES

requests → validazione EDS in mTLS

▶️ Uso (esempio)

Esecuzione del tool da riga di comando:

python fse_tool.py ^
  --pdf in/referto.pdf ^
  --data in/referto.json ^
  --out out/referto_signed.pdf ^
  --cda-out out/referto_cda.xml ^
  --sign-p12 secrets/cert.p12 ^
  --sign-pass 123456 ^
  --eds-url https://<gateway-preprod>/eds/validation ^
  --mtls-cert secrets/client_cert.pem ^
  --mtls-key secrets/client_key.pem ^
  --ca secrets/gateway_ca.pem ^
  --log out/referto_log.json


Output generato:

📄 out/referto_cda.xml → documento CDA R2 XML

📑 out/referto_signed.pdf → PDF firmato PAdES con CDA allegato

🧾 out/referto_log.json → log completo della validazione EDS

🧾 Accreditamento FSE

Modulo attualmente in fase di accreditamento nazionale presso SOGEI / Dipartimento per la Trasformazione Digitale
nell’ambito dell’interoperabilità del Fascicolo Sanitario Elettronico 2.0.

Software: WinPreGest
Versione: 5.1_A08
Tipologia documento: Referto di Specialistica Ambulatoriale (nota di consulto)
Servizi oggetto di accreditamento: Validazione + Pubblicazione

Società fornitrice:
Pa.Ser Consulting Group della dott.ssa Pier Paola Lai
📍 Via Salvatore Dau, 11 — 07100 Sassari (Italia)
📧 paserconsulting@pec.it

📄 P.IVA 02216530903 — C.F. LAIPPL71A44I452H

Referente tecnico:
👤 Sergio Busonera
📧 sergio.busonera@paserconsulting.it

📞 +39 347 3493596

📄 Licenza

Questo progetto è distribuito con licenza MIT.
Consulta il file LICENSE per i dettagli.

© 2025 – Pa.Ser Consulting Group della dott.ssa Pier Paola Lai
Tutti i diritti riservati.
