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
