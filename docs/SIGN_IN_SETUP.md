# Sign-in and private portfolios: setup

Once this is set up, each visitor signs in with Google and gets their own portfolio, watchlist and swing strategy,
saved permanently in Supabase. Google accounts support passkeys, so people can sign in with Face ID, Touch ID or
Windows Hello. SharkFin never sees a password or any biometric data. It gets only the account's ID, name and email.
It stores data under a hash of the ID, not the email.

| Secrets present | What happens |
| --- | --- |
| none (your own computer) | Works exactly as before: one portfolio in `.sharkfin/*.json`, no sign-in button. |
| `[auth]` only | Sign-in works. Signed-in data goes to `.sharkfin/users/<id>/`, which Streamlit Cloud wipes on restart. Guests keep data for their visit only. |
| `[auth]` + `[supabase]` | The full setup: signed-in data is saved in Supabase, and guests keep data for their visit only. |

Guests never write to the server, so visitors no longer share or overwrite one portfolio. If Supabase can't be
reached when a page loads, SharkFin shows a warning and refuses to save for that visit. That way an outage can't
replace a saved portfolio with an empty one.

## 1. Supabase (about 3 minutes)

1. Go to https://supabase.com, sign in, and click **New project**. The free plan is fine. Pick any name and region,
   and save the database password somewhere (SharkFin doesn't need it).
2. Open **SQL Editor**, paste the following, and click **Run**:

   ```sql
   create table if not exists public.sharkfin_user_data (
     user_id    text        not null,
     name       text        not null,
     data       jsonb       not null default '[]'::jsonb,
     updated_at timestamptz not null default now(),
     primary key (user_id, name)
   );
   alter table public.sharkfin_user_data enable row level security;
   grant select, insert, update on public.sharkfin_user_data to service_role;
   ```

   When creating the project: keep **Enable Data API** on, turn **Automatically expose new tables** off, and turn
   **Enable automatic RLS** on. The `grant` line gives only SharkFin's server key access to this one table.
   Row level security is on with no policies, so the public ("anon" / "publishable") key can't read or write
   anything. Only the secret key, which stays in SharkFin's server secrets, can reach the table.
3. Go to **Project Settings → API Keys**. Copy the **Project URL** and a **secret** key (starts with `sb_secret_`).
   On older projects this is the `service_role` key. Never put this key in the repo or in browser code.

Free projects pause after about a week with no activity. Normal use keeps the project awake, and the daily alerts
job we're building next will also ping it.

## 2. Google sign-in (about 5 minutes)

1. Go to https://console.cloud.google.com and create a project (e.g. "SharkFin").
2. Open **APIs & Services → OAuth consent screen** (also called **Google Auth Platform**). Choose **External**,
   enter the app name and your support email, and save. Only the default scopes are needed: `openid`, `email`
   and `profile`.
3. Open **Clients** (or **Credentials → Create credentials → OAuth client ID**) and pick **Web application**.
   Under **Authorized redirect URIs**, add:
   - `https://sharkfin.streamlit.app/oauth2callback`
   - `http://localhost:8501/oauth2callback` (for running it on your computer)
   - later, when you move to your own domain: `https://YOUR-DOMAIN/oauth2callback`
4. Copy the **Client ID** and **Client secret**.
5. Open **Audience** and, under **Test users**, add the Gmail addresses that should be able to sign in (up to 100).
   The app stays in **Testing** for now. Google won't let you publish until the **Branding** page has a home page
   and privacy policy link on a domain you've verified, which isn't possible on `streamlit.app`. Everyone not on the
   list can still use SharkFin as a guest.
6. Once you have your own domain: put a home page and a short privacy policy on it, verify the domain in Google
   Search Console, add both links and the domain on **Branding**, then click **Audience → Publish app**. Apps that
   ask only for name and email don't need Google's review.

## 3. Streamlit secrets

On Streamlit Cloud, open the app's **Settings → Secrets** and add these lines, keeping any keys already there.
Locally, put the same lines in `.streamlit/secrets.toml`, which git ignores, and use the localhost `redirect_uri`.

```toml
[auth]
redirect_uri = "https://sharkfin.streamlit.app/oauth2callback"
cookie_secret = "PASTE-A-LONG-RANDOM-STRING"   # e.g. run: python -c "import secrets; print(secrets.token_urlsafe(48))"
client_id = "PASTE.apps.googleusercontent.com"
client_secret = "PASTE"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[supabase]
url = "https://PASTE.supabase.co"
key = "sb_secret_PASTE"
```

Save. The app restarts, and a **Sign in with Google** button appears in the sidebar.

## Moving to your own domain later

Nothing about sign-in or storage is tied to Streamlit Cloud. On a new host (Render, Railway, Fly.io, ...), set the
same secrets, change `redirect_uri` to `https://YOUR-DOMAIN/oauth2callback`, and add that address in Google
(step 2.3). Users and their data carry over because the data lives in Supabase.

## Code

- `sharkfin/store.py`: picks the storage mode and reads and writes each list (local JSON or the Supabase REST API).
- `sharkfin/ui.py`: `init_state` / `save_state` / `save_list` call the store; `account_box` draws the sidebar
  sign-in; `guest_notice` shows the guest banner on Portfolio.
- `tests/test_store.py`: guest, per-account, cloud round-trip and outage tests.
