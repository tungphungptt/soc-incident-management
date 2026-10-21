# Quick start on Windows

1. Install Python 3.12+, Node.js 20+, and MySQL 8.
2. Ensure `soc_incident_management` exists and has the 14 tables from the existing schema.
3. Run `.un-backend.ps1`. On first run it creates `backend/.env` and stops so you can edit credentials. Set `DATABASE_URL`, `JWT_SECRET`, `ADMIN_USERNAME`, and a strong `ADMIN_PASSWORD`. Run it again.
4. In another PowerShell window, run `.un-frontend.ps1`.
5. Open `http://localhost:5173`.
6. Verify backend health at `http://127.0.0.1:8000/health` and API docs at `http://127.0.0.1:8000/docs`.

If using a MySQL password with special URL characters, URL-encode the password in `DATABASE_URL`, or create a dedicated application database account with a simple generated password. Do not put real secrets in source control.
