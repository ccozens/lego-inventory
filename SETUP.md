# Lego Set Inventory Logger — Setup Guide

## Project Structure

```
lego_inventory/
├── app.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml        ← YOU CREATE THIS (never commit to git)
```

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Get a Rebrickable API Key

1. Create a free account at https://rebrickable.com
2. Go to **Account → Settings → API** and copy your API key.

---

## 3. Set Up Google Service Account

### 3a. Create a Service Account

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. Go to **APIs & Services → Library** and enable the **Google Docs API**.
3. Go to **APIs & Services → Credentials → Create Credentials → Service Account**.
4. Give it a name (e.g. `lego-inventory-bot`), click **Done**.
5. Click the new service account, go to the **Keys** tab, and click **Add Key → Create new key → JSON**.
6. Download the JSON file — you'll use its contents in `secrets.toml`.


### 3b. Use existing Google Doc

Need The Document ID — it's in the URL when you have the Doc open:
https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
Copy that long string and put it in your secrets.toml as doc_id.
Share the Doc with your service account — open the Doc, click Share, and add the client_email from your service account JSON (it looks like something@your-project.iam.gserviceaccount.com) with Editor permissions.


### 3c. OR Prepare new Google Doc

1. Create a new Google Doc.
2. Insert a table (Insert → Table) with **5 columns** and at least **1 header row**. Label the headers:
   `Set ID | Name | Year | Theme | Date Added`
3. **Share the Doc** with your service account email (found in the JSON as `client_email`), giving it **Editor** access.
4. Copy the **Document ID** from the URL:
   `https://docs.google.com/document/d/THIS_IS_THE_DOC_ID/edit`

---

## 4. Create `.streamlit/secrets.toml`

Create the file at `.streamlit/secrets.toml` inside your project folder:

```toml
# Rebrickable API
[lego]
api_key = "your_rebrickable_api_key_here"

# Google Doc ID
[google]
doc_id = "your_google_doc_id_here"

# Google Service Account credentials (paste the contents of the JSON key file)
[gcp_service_account]
type                        = "service_account"
project_id                  = "your-project-id"
private_key_id              = "abc123..."
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email                = "lego-inventory-bot@your-project.iam.gserviceaccount.com"
client_id                   = "123456789"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/lego-inventory-bot%40your-project.iam.gserviceaccount.com"
```

> ⚠️ **Important**: Add `.streamlit/secrets.toml` to your `.gitignore` to avoid leaking credentials.

---

## 5. Run the App

```bash
streamlit run app.py
```

---

## 6. Using the App

1. Type a **Lego Set ID** (e.g. `75192` or `75192-1`) into the text box.
2. Click **Look Up** — the app will pull the set name, year, theme, image, and piece count from Rebrickable.
3. Confirm the details look correct.
4. Click **Add to Inventory** — a new row is appended to your Google Doc table.
5. The **Recent Additions** table at the bottom tracks everything logged in the current session.

---

## Deploying to Streamlit Community Cloud

If you deploy via [share.streamlit.io](https://share.streamlit.io):

1. Push your code (without `secrets.toml`) to a GitHub repo.
2. In the Streamlit Cloud dashboard, go to **App Settings → Secrets**.
3. Paste the contents of your `secrets.toml` there.
