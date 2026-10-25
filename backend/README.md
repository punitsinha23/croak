# Croak – Backend

The REST API behind [Croak](https://croak-green-shine.vercel.app), a small social app with posts ("ribbits"), follows, notifications and community group chats.

It's a Django + Django REST Framework project backed by PostgreSQL, with media on Cloudinary and outgoing email handled by a separate notifications service. I built it as a learning project, so this README covers how it works and also **why** it's built the way it is, including the shortcuts I took and what they cost.

> The React frontend lives in [`croak-green-shine`](https://github.com/punitsinha23/croak-green-shine).

---

## Contents

- [Architecture](#architecture)
- [Project layout](#project-layout)
- [How it works](#how-it-works)
  - [Accounts and authentication](#accounts-and-authentication)
  - [Posts, feed and interactions](#posts-feed-and-interactions)
  - [Communities and chat](#communities-and-chat)
  - [Email: queue, cron and the notifications service](#email-queue-cron-and-the-notifications-service)
  - [Media](#media)
- [API reference](#api-reference)
- [Running locally](#running-locally)
- [Tests](#tests)
- [Design tradeoffs](#design-tradeoffs)
- [Known issues and next steps](#known-issues-and-next-steps)

---

## Architecture

```mermaid
flowchart LR
    FE["React frontend<br/>(Vercel)"] -- "REST + JWT" --> API["Django API<br/>(Render, gunicorn)"]
    API --> DB[("PostgreSQL")]
    API -- "uploads" --> CL["Cloudinary<br/>(images, GIFs, voice notes)"]
    API -- "HTTP: OTPs, queued emails,<br/>announcements" --> NS["croak-notifications<br/>(Vercel)"]
    NS --> MAIL["Email inbox"]
    GH["GitHub Actions cron"] -- "POST with X-Cron-Secret" --> API
```

| Piece | Role |
|---|---|
| **Django API** (this folder) | All business logic: users, posts, follows, communities, notifications, email queue. Deployed on Render behind gunicorn, static files served by WhiteNoise. |
| **PostgreSQL** | Single source of truth, configured via `DATABASE_URL`. |
| **Cloudinary** | Stores and serves every uploaded file (avatars, banners, post media, community icons, voice notes). |
| **croak-notifications** | A small separate service that actually sends email. The API never talks SMTP in the request path; it POSTs to this service. |
| **GitHub Actions** | Acts as the scheduler. [`email-cron.yml`](../.github/workflows/email-cron.yml) calls the API's cron endpoints every 5 minutes, daily, and weekly. |

---

## Project layout

```text
backend/
├── croak/            # Project settings, root URLs, WSGI
├── users/            # Custom User model, OTP, signup/login/Google, profile, follow
├── ribbits/          # Posts, likes, comments, replies, reposts, search,
│   │                 # in-app notifications, email queue + cron endpoints
│   ├── signals.py        # Queues "new post" emails for followers
│   ├── email_queue.py    # Queue helpers, retry logic, sending via the service
│   ├── email_templates.py
│   ├── cron_views.py     # Endpoints hit by GitHub Actions
│   └── management/commands/  # Same jobs, runnable by hand
├── communities/      # Communities, memberships/roles, chat messages
├── test_api/         # Manual script for poking a running server
└── requirements.txt
```

Each app follows the usual Django split: `models.py` → `serializers.py` → `views.py` → `urls.py`, plus `tests.py`.

---

## How it works

### Accounts and authentication

**Custom user model.** `users.User` extends `AbstractUser`, logs in with **email** (`USERNAME_FIELD = "email"`), and adds `bio`, `location`, `profile_pic`, `banner` and a self-referential `following` many-to-many (asymmetric, so "followers" is the reverse relation).

**Email signup with OTP.** An account isn't created until the email is verified:

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant N as Notifications service
    C->>A: POST /api/users/register/ {email, password, ...}
    A->>A: validate, create/refresh OTP row (expires in 5 min)
    A->>A: save PendingSignup row (password already hashed)
    A--)N: send OTP email (background thread)
    A-->>C: 200 "OTP sent"
    C->>A: POST /api/users/verify-otp/ {email, otp}
    A->>A: check OTP + expiry, read PendingSignup
    A->>A: create User, delete PendingSignup
    A-->>C: 201 created + {access, refresh}
```

Pending signups live in the `PendingSignup` table rather than in memory, so verification works no matter which server process handles it and survives restarts. The password is hashed before it's stored there. Verifying also logs the user in: the response carries a JWT pair, so the frontend goes straight to the feed.

Usernames are optional at signup; if missing, one is generated from the email's local part with a numeric suffix on collision (`frog`, `frog1`, …).

**Login** returns a JWT pair from SimpleJWT: a 30-minute access token and a 30-day refresh token. The frontend sends `Authorization: Bearer <access>` and calls `/api/users/token/refresh/` when it gets a 401. Refresh tokens **rotate**: every refresh returns a new 30-day refresh token, so anyone who opens the app at least once a month stays signed in, and the frontend sends them straight to the feed instead of the landing page.

**Google sign-in** (`/api/users/google/`) verifies the Google ID token server-side with `google-auth` against `GOOGLE_CLIENT_ID`, then finds or creates the user (with an unusable password) and returns the same JWT pair.

**Password reset** reuses the OTP table: request an OTP, then confirm with OTP + new password. The request endpoint answers the same way whether or not the email exists, so it can't be used to discover accounts, and an OTP can only be used once.

### Posts, feed and interactions

A **Ribbit** has up to 500 characters of text and optional media. The same model represents three things:

| Kind | How it's stored |
|---|---|
| Original post | `parent = null`, `is_reribbit = false` |
| Repost with your own take | `is_reribbit = true`, `reribbit_of` → original (always the root, never a repost of a repost) |
| Reply-style child | `parent` → the post it hangs off |

Comments on a post are a separate `Comment` model, and replies to a comment are `Reply`, giving one level of threading.

**The feed** (`/api/ribbit/feed/`) is **reverse-chronological with no ranking**, and includes every post (optionally filtered with `?username=`). It uses **cursor pagination** (10 per page, ordered by `-created_at`). Each query does the joins and counts in one go: `select_related` for authors and originals, and `annotate` for like/comment counts plus an `Exists` subquery for "did I like this".

**Likes** toggle: the same `POST` likes or unlikes. A `unique_together` constraint stops double likes.

**In-app notifications** are plain `Notification` rows created inside the views: like, comment, reply, and so on. Unliking deletes the matching notification, and you never get notified about your own actions. The frontend reads them from `/api/ribbit/notifications/`.

**Search** is a case-insensitive substring match (`icontains`) over post text, usernames and bios.

### Communities and chat

- Anyone logged in can **create** a community. The creator automatically gets an `admin` membership, and the slug is generated from the name.
- **Memberships** carry a role (`admin`, `moderator`, `member`). Users join and leave by slug. The creator can't leave and can't be removed, and admins can remove members.
- `member_count` is a stored counter, updated with `F()` expressions on join, leave and remove so concurrent updates don't clobber each other.
- **Messages** support text plus one media file (voice notes and GIFs go to Cloudinary). Only members can read or post. Senders can delete their own messages, and admins can delete any.
- **Chat is polling, not websockets.** The frontend calls `GET /api/communities/messages/?community_slug=…&since=<last timestamp>` every 3 seconds and appends whatever is newer. An index on `(community, -created_at)` keeps that query cheap.

### Email: queue, cron and the notifications service

Email is deliberately kept **out of the request path**:

1. **Something worth emailing happens.** Right now that's:
   - a new original post, which emails **everyone** except the author via a `post_save` signal in `signals.py`. Followers get a "someone you follow" version. To avoid floods, nobody gets a second new-post email while one is still waiting to be sent
   - the 8 PM check-in (IST): a rotating fun question, the day's most-loved posts, and a "Croak about your day" button, or a "be the first croak tonight" version on quiet days
   - the daily digest or "you're missing out" reminder
   - the weekly nudge, with post reminders and suggested people to follow
2. **A row goes into `EmailQueue`** (status `pending`, a priority and a `scheduled_for` time), but only if the recipient's `EmailPreferences` allow it. There's a master switch plus per-type toggles, and preferences are created with defaults on first access.
3. **GitHub Actions calls the cron endpoints** with an `X-Cron-Secret` header:
   - `process-emails` every 5 minutes, which takes up to 100 due emails in priority order and POSTs each to the notifications service
   - `daily-digest` at 09:00 UTC
   - `weekly-nudges` on Mondays at 10:00 UTC
   - `evening-checkin` at 14:00 UTC (7:30 PM IST), which queues emails timed for 8:00 PM IST so that GitHub's late scheduled runs don't make them late
4. **Results are written back.** Success sets `sent` and `sent_at`. Failure stores the error and retries on later runs. After 3 failed attempts the email is marked `failed` and left alone.

`/api/ribbit/cron/stats/` reports pending, failed and sent-today counts. The same jobs exist as management commands (`process_email_queue`, `send_daily_digests`, …) for running by hand.

OTP emails and admin announcements (`/api/ribbit/announce-update/`, admin-only) skip the queue and go straight to the notifications service, because they're either urgent or one-offs.

### Media

`DEFAULT_FILE_STORAGE` is Cloudinary, so every `FileField`/`CloudinaryField` uploads straight there and the database stores only the reference. Voice notes use Cloudinary's video storage, since audio is handled as a "video" resource type. The frontend asks Cloudinary for resized, auto-format variants (`w_…,q_auto,f_auto`) instead of the backend making thumbnails.

---

## API reference

All routes are under `/api/`. Unless noted, they need `Authorization: Bearer <access token>`.

<details>
<summary><strong>Users</strong> — <code>/api/users/</code></summary>

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `register/` | – | Start signup, emails an OTP |
| POST | `verify-otp/` | – | Verify OTP and create the account |
| POST | `login/` | – | Email + password → `{access, refresh}` |
| POST | `google/` | – | Google ID token → `{access, refresh, user}` |
| POST | `token/refresh/` | – | Refresh token → new access token |
| POST | `token/verify/` | – | Check a token |
| POST | `password-reset-request/` | – | Email a reset OTP |
| POST | `password-reset-confirm/` | – | OTP + new password |
| GET | `me/` | ✓ | Current user's profile |
| PATCH | `update/` | ✓ | Edit profile (multipart for images) |
| GET | `users/` | ✓ | List users |
| POST | `<username>/follow/` | ✓ | Toggle follow |

</details>

<details>
<summary><strong>Ribbits</strong> — <code>/api/ribbit/</code></summary>

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `feed/` | optional | Chronological feed, cursor-paginated, `?username=` filter |
| POST | `post/` | ✓ | Create a post (multipart for media) |
| PATCH | `update/<id>/` | ✓ owner | Edit a post |
| DELETE | `delete/<id>/` | ✓ owner | Delete a post |
| GET | `my-ribbits/` | ✓ | Your posts |
| GET | `liked/` | ✓ | Posts you liked |
| POST | `ribbits/<id>/like/` | ✓ | Toggle like |
| GET/POST | `ribbits/<id>/comment/` | ✓ | List / add comments |
| DELETE | `ribbits/<id>/comment/<comment_id>/` | ✓ comment or post author | Delete a comment |
| GET/POST | `comments/<comment_id>/replies/` | ✓ | List / add replies |
| POST | `<id>/repost/` | ✓ | Repost with optional `repost_text` |
| GET | `search/?q=` | ✓ | Search posts and users |
| GET | `search/<username>/` | ✓ | Public profile with posts |
| GET | `notifications/` | ✓ | Your notifications |
| GET/PATCH | `email-preferences/` | ✓ | Your email settings |
| POST | `announce-update/` | admin | Email all users |
| POST | `cron/process-emails/` | cron secret | Send due queued emails |
| POST | `cron/daily-digest/` | cron secret | Queue daily digests |
| POST | `cron/weekly-nudges/` | cron secret | Queue weekly nudges |
| POST | `cron/evening-checkin/` | cron secret | Queue 8 PM check-in emails |
| GET | `cron/stats/` | cron secret | Queue statistics |

</details>

<details>
<summary><strong>Communities</strong> — <code>/api/communities/</code></summary>

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | optional | List communities |
| POST | `/` | ✓ | Create (creator becomes admin) |
| GET | `<slug>/` | optional | Community detail |
| GET | `<slug>/members/` | optional | Members and roles |
| POST | `membership/join/` | ✓ | `{community_slug}` |
| POST | `membership/leave/` | ✓ | `{community_slug}` |
| POST | `membership/remove_member/` | ✓ admin | `{community_slug, user_id}` |
| GET | `messages/?community_slug=&since=` | ✓ member | Messages, newest first |
| POST | `messages/` | ✓ member | `{community, content}` or multipart `media` |
| DELETE | `messages/<id>/` | ✓ sender/admin | Delete a message |

</details>

---

## Running locally

**Requirements:** Python 3.10+, and PostgreSQL (or SQLite for quick local work).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (it's loaded with `python-dotenv`):

```dotenv
# Local development only. Leave DEBUG unset (off) in production
DEBUG=true

# Required in production. Generate one with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=...

# Database. SQLite is fine for local development
DATABASE_URL=sqlite:///db.sqlite3
# DATABASE_URL=postgres://user:pass@localhost:5432/croak

# Media uploads
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Google sign-in (same client ID as the frontend's VITE_GOOGLE_CLIENT_ID)
GOOGLE_CLIENT_ID=...

# Email sending
NOTIFICATIONS_SERVICE_URL=https://croak-notifications.vercel.app
APP_PASSWORD=...

# Protects the cron endpoints. Always set this to a long random value
CRON_SECRET=...
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin and announcements
python manage.py runserver         # http://127.0.0.1:8000
```

Point the frontend at it with `VITE_MODE=development` and `VITE_DEV_URL=http://127.0.0.1:8000/api/`. `http://localhost:8080` is already in the CORS allow-list.

To run the email jobs by hand instead of waiting for GitHub Actions:

```bash
python manage.py process_email_queue
python manage.py send_daily_digests
```

---

## Tests

```bash
python manage.py test            # all apps
python manage.py test ribbits    # one app
```

Tests run against an **in-memory SQLite** database (switched automatically in `settings.py` when the command is `test`), so no Postgres, Cloudinary or network access is needed. Outgoing calls to Google and the notifications service are mocked.

What's covered (159 tests):

- **users:**
  - signup → OTP verify (wrong and expired codes, pending signups stored in the database, auto-login)
  - login, 30-day rotating refresh tokens
  - password reset, including no account discovery and no OTP reuse
  - Google sign-in (new user, username collision, invalid token)
  - profile, follow and unfollow
- **ribbits:**
  - create, edit and delete with owner checks
  - feed order and cursor pagination
  - likes and notifications (no self-notify, unlike cleans up)
  - comments, replies, reposts and search
  - the new-post broadcast (everyone but the author, opt-outs, flood guard, HTML escaping)
  - the 8 PM check-in (timing, no double sends, top posts, quiet days, opt-outs)
  - cron endpoints: secret check, send, retry three times then fail, scheduled emails
  - email preferences
- **communities:**
  - create, join and leave
  - roles and removing members
  - message read and write permissions
  - the `since` polling filter
  - message deletion rules

---

## Design tradeoffs

These are the decisions that shaped the code, and what each one costs.

**One Django monolith, with email split out.**
Users, posts and communities share one codebase and one database, so features that cut across them (feed annotations, notifications) are plain ORM queries, and deploying is simple. Sending email is the one thing moved out, into its own service, so slow SMTP calls and email provider quirks can't block or crash the API. *Cost:* two deployments to keep in sync, and if the service is down, OTP emails are silently lost.

**JWT instead of sessions, with long-lived rotating refresh tokens.**
Stateless tokens fit a separate frontend on a different domain without cookie and CSRF setup, and the API doesn't store sessions. A 30-day rotating refresh token means people don't have to log in again every time they open the app. *Cost:* access tokens can't be revoked before they expire (kept short at 30 minutes to limit that), and without SimpleJWT's blacklist app, an old refresh token stays valid until it expires even after rotation. The frontend keeps tokens in `localStorage`, which any XSS bug could read, and a stolen refresh token is now useful for up to a month.

**A separate `PendingSignup` table until the OTP is verified.**
No half-created, unverified accounts ever reach the `User` table, and any server process can finish a signup. (An earlier version kept this in Django's per-process memory cache, which broke with multiple workers and lost signups on restart.) *Cost:* a profile picture is uploaded to Cloudinary at registration, so abandoned signups can leave orphaned images, and stale rows need occasional cleanup.

**Chronological, global feed with cursor pagination.**
No ranking means behaviour is predictable and easy to test, and it matches the product idea that no algorithm decides what you see. Cursor pagination keeps pages stable while new posts arrive and avoids slow `OFFSET` scans. *Cost:* you can't jump to page N, and showing *every* post to everyone doesn't scale. A following-only feed or fan-out would be the next step.

**Mixed counting strategy.**
Likes and comments are counted per request with `annotate(Count(...))`, which is always correct but repeats work. Reposts and community members use stored counters (`reribbit_count`, `member_count`) updated with `F()`, which is cheap to read but can drift if a row is deleted without going through the view. *Cost:* two mental models in one codebase.

**HTTP polling for chat instead of websockets.**
Polling every 3 seconds with a `since` cursor needs no Django Channels, Redis or a long-lived connection, and runs fine on Render's basic tier. *Cost:* messages can take up to 3 seconds to appear, and an open chat makes about 20 requests a minute even when nobody is talking.

**A database table as the email queue, with GitHub Actions as the scheduler.**
No Celery, no broker and no worker process to pay for or babysit. The queue is just rows you can inspect in the admin, and retries are a counter. *Cost:* sends happen at most every 5 minutes (GitHub's scheduled runs are often late), each run sends up to 100 emails one after another inside a single HTTP request, and the cron endpoints are only as safe as `CRON_SECRET`.

**Fire-and-forget threads for OTP email.**
Signup responds instantly instead of waiting on the email service. *Cost:* if the send fails, nobody is told. The thread just logs and exits.

**Cloudinary for all media.**
Render's disk is temporary, so local uploads would vanish on every deploy. Cloudinary also gives a CDN and on-the-fly resizing for free. *Cost:* tied to one vendor, and uploads add a network round trip to the request.

**Simple `icontains` search.**
No extra infrastructure, and it works on SQLite and Postgres alike. *Cost:* a full table scan on every search, with no relevance ranking. Postgres full-text search or trigram indexes would be the upgrade.

**SQLite for tests, Postgres in production.**
The suite runs in seconds with zero setup. *Cost:* Postgres-specific behaviour (case sensitivity, constraint timing, SSL) isn't exercised.

---

## Known issues and next steps

Things I know are wrong or unfinished, roughly in priority order:

- [x] ~~**`SECRET_KEY` and `DEBUG` were hard-coded.**~~ Both come from environment variables now. `DEBUG` defaults to off, and the server refuses to start in production without a `SECRET_KEY`.
- [ ] **`CRON_SECRET` has a placeholder default.** If the variable isn't set, the cron endpoints accept a guessable value. The app should refuse to serve them without a real secret.
- [x] ~~**Comment deletion had no owner check.**~~ Now only the comment's author or the post's author can delete it.
- [x] ~~**Community edit and delete returned `200`/`204` for non-admins.**~~ They now return `403`.
- [x] ~~**Pending signups lived in per-process memory.**~~ Moved to the `PendingSignup` table.
- [ ] Enable SimpleJWT's token blacklist so rotated and logged-out refresh tokens are revoked immediately.
- [ ] Clean up `PendingSignup` rows older than a day.
- [ ] **Daily digest "new followers"** counts followers who *created their account* yesterday, not follows made yesterday, because the `following` relation has no timestamp. That needs a through model with `created_at`.
- [ ] **Instant emails for likes, comments and follows** have templates and preference toggles (`queue_notification_email`), but nothing calls them yet. Today those events only create in-app notifications.
- [ ] Remove the `scratch_*.py` debugging scripts from the repo root.
