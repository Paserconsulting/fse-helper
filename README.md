# fse-helper
Modulo Python per integrazione CDA2 in PDF + firma PAdES + validazione EDS per FSE 2.0 (WinPreGest)

Installazione
python -m pip install --upgrade pip
pip install -r requirements.txt

Uso (esempio)
python fse_tool.py ^
  --pdf in\referto.pdf ^
  --data in\referto.json ^
  --out out\referto_signed.pdf ^
  --cda-out out\referto_cda.xml ^
  --sign-p12 secrets\cert.p12 --sign-pass 123456 ^
  --eds-url https://<endpoint-eds-di-test> ^
  --mtls-cert secrets\client_cert.pem ^
  --mtls-key secrets\client_key.pem ^
  --ca secrets\gateway_ca.pem ^
  --log out\referto_log.json
