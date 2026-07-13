# Accounts & saved portfolios with Supabase

Hone ships with an **optional** authentication layer: users sign up / sign
in with email + password, and each user can save named portfolio snapshots
(their γ, tier, and views) and reload them later. It's powered by
[Supabase](https://supabase.com) (a hosted Postgres + auth service with a
generous free tier).

**It's off until you configure it.** With no Supabase keys, Hone runs
exactly as before — no login, nothing stored server-side, everything in the
browser. Turning it on is three steps and ~10 minutes.

---

## 1. Create a Supabase project

1. Sign up at [supabase.com](https://supabase.com) → **New project**.
2. Give it a name and a database password (you won't need the password for
   Hone). Wait ~2 minutes for it to provision.
3. In **Project Settings → API**, copy two values:
   - **Project URL** — e.g. `https://abcdefghijkl.supabase.co`
   - **anon public** key — a long JWT. This is safe to expose in the
     browser (it's the public key; Row-Level Security does the real
     protection). **Never** use the `service_role` key here.

## 2. Create the `portfolios` table (with Row-Level Security)

In the Supabase dashboard open **SQL Editor** and run this. It creates the
table and locks it down so every user can only ever see and modify their
**own** rows:

```sql
create table public.portfolios (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade,
  name       text not null,
  data       jsonb not null,
  created_at timestamptz not null default now()
);

alter table public.portfolios enable row level security;

create policy "own rows: select" on public.portfolios
  for select using (auth.uid() = user_id);
create policy "own rows: insert" on public.portfolios
  for insert with check (auth.uid() = user_id);
create policy "own rows: delete" on public.portfolios
  for delete using (auth.uid() = user_id);

create index portfolios_user_idx on public.portfolios (user_id, created_at desc);
```

Row-Level Security is the whole security model here: even though the anon
key is public, these policies mean the database itself refuses to return
or modify a row unless the request's authenticated user owns it.

## 3. Configure email auth

In **Authentication → Providers → Email**, make sure Email is enabled.
For a smooth first run you may want to turn **"Confirm email" off** (under
Authentication → Providers → Email → *Confirm email*) so sign-ups work
without a verification round-trip; turn it back on for production and
configure the email templates/SMTP.

Add your site to the allowed redirect/site URLs under
**Authentication → URL Configuration** (e.g. `https://studiohone.com` and
`http://localhost:8000` for local dev).

## 4. Point Hone at your project

Edit `hone/web/static/config.js` and fill in the two values from step 1:

```js
window.HONE_CONFIG = {
  supabaseUrl: "https://abcdefghijkl.supabase.co",
  supabaseAnonKey: "eyJhbGciOi...your-anon-key...",
};
```

Redeploy (or restart `python -m hone serve`). That's it — a **Sign in /
Sign up** control now appears at the top of the app, and finishing a run
shows a **Save this portfolio** button. Saved portfolios are listed under
**Saved portfolios**, and loading one drops you back into the flow with its
γ and views restored.

### Keeping keys out of the repo (optional, for production)

`config.js` holds only public values, so committing it is acceptable. If
you'd rather not, add `hone/web/static/config.js` to `.gitignore` and write
it at deploy time from environment variables — for example a small entry in
your Docker start command:

```sh
cat > hone/web/static/config.js <<EOF
window.HONE_CONFIG = { supabaseUrl: "$SUPABASE_URL", supabaseAnonKey: "$SUPABASE_ANON_KEY" };
EOF
```

then set `SUPABASE_URL` / `SUPABASE_ANON_KEY` in your host's environment
(Render → Environment, Fly → secrets).

---

## How it works (for the curious)

- The browser talks to Supabase's REST/GoTrue HTTP APIs directly — no SDK,
  no CDN script, so it stays within Hone's self-contained model.
- `signUp` / `signIn` hit `/auth/v1/signup` and
  `/auth/v1/token?grant_type=password`; the returned session (a JWT) is kept
  in `localStorage` and sent as a Bearer token on every data call.
- Saving a portfolio `POST`s to `/rest/v1/portfolios`; listing/deleting use
  the same PostgREST endpoint. RLS scopes every call to the signed-in user.
- **What's saved:** γ, tier, the demo/live flag, and your views — never your
  Alpaca keys (those stay only in your browser and are never persisted).

## Security notes

- The anon key is *designed* to be public; your data is protected by the
  RLS policies above, not by hiding the key. Do not paste the
  `service_role` key into `config.js`.
- Hone stores no brokerage credentials in Supabase. Alpaca keys live only
  in the browser session and are sent only to Alpaca via your own requests.
- If you enabled `HONE_ACCESS_PASSWORD` (the site-wide gate), that and
  Supabase auth are independent layers — you can use either or both.
