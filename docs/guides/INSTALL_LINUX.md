# Installing WorkTrack Pro on an Ubuntu/Debian server

This covers one institution on its own VPS. You need root, a domain name pointed at the server, and outbound internet.

## 1. Install

1. Download `worktrack-X.Y.Z.tar.gz` and `SHA256SUMS` from the latest GitHub release. Copy both to the server; a USB stick or scp is fine, since the server needs no git.
2. On the server:

   ```bash
   sha256sum -c SHA256SUMS
   tar -xzf worktrack-X.Y.Z.tar.gz
   sudo bash worktrack/deploy/linux/install.sh --domain tasks.example.edu --auto-update OWNER/REPO --token-file /root/gh-token
   ```

   Run without flags to be asked instead. The question "Install new versions automatically every night from GitHub?" defaults to yes.
3. Create the institution: `cd /opt/worktrack/app && sudo -u worktrack env $(cat /etc/worktrack/worktrack.env | xargs) /opt/worktrack/venv/bin/python manage.py new_institution --config FILE.json` (see `docs/institution.example.json`).
4. Create the vendor support account, a super admin you can always get back:

   ```bash
   sudo bash -c 'set -a; . /etc/worktrack/worktrack.env; cd /opt/worktrack/app; runuser -u worktrack -- /opt/worktrack/venv/bin/python manage.py support_admin --email you@example.com'
   ```

   The password is printed once. Running the same command again later re-activates the account and makes it super admin again, even if someone disabled or demoted it in the app. Add `--reset-password` if the password is lost. No password is stored in the code (the repository is public). The account shows in the user list as "ROWD Support", so tell the institution it exists.
5. Add HTTPS, for example `apt install certbot python3-certbot-nginx && certbot --nginx -d tasks.example.edu`, then set `SECURE_COOKIES=True` in `/etc/worktrack/worktrack.env` and run `systemctl restart worktrack`.

Re-running `install.sh` from a newer package upgrades by hand. It keeps the existing config, database and uploads.

### Where things live

| What | Where |
|---|---|
| Code (replaced on each update) | `/opt/worktrack/app` (the one before is `app.previous`, a failed one `app.failed`) |
| Python environment (kept) | `/opt/worktrack/venv` |
| Database and uploads (kept) | `/var/lib/worktrack/db.sqlite3`, `/var/lib/worktrack/media` |
| Settings (root only) | `/etc/worktrack/worktrack.env`, `updater.conf`, `install.conf` |
| Logs | `journalctl -u worktrack`, `/var/log/worktrack/` |
| Backups | `/var/backups/worktrack/` (nightly at 01:30, the newest 14 are kept) |

## 2. Automatic updates

### How a new version is published (developer machine)

```bash
python scripts/release.py patch     # or minor / major / 1.4.0
```

That bumps `VERSION`, commits, tags `vX.Y.Z` and pushes. GitHub Actions (`.github/workflows/release.yml`) then:

1. Checks that the tag matches `VERSION`.
2. Runs the lint, the Django deploy check and the full test suite. If anything fails, nothing is published.
3. Builds `worktrack-X.Y.Z.tar.gz` (static files prebuilt, `version.json` with version, commit and build date) and `SHA256SUMS`.
4. Publishes both as release assets.

Check the release appears under GitHub → Releases with both files.

### What the server does each night

`worktrack-update.timer` runs at about 03:00, after the 01:30 backup. It adds a random delay of up to 45 minutes and catches up after downtime. The updater (`deploy/linux/worktrack-update.sh`):

1. Asks GitHub for the latest release. Nothing happens if it isn't newer than the installed version.
2. Downloads the package and refuses it if the SHA256 checksum or the version inside doesn't match the tag.
3. Backs up the database and uploads, then swaps the code folders. The venv, data and settings stay where they are.
4. Installs dependencies, runs migrations, collects static files, re-applies the systemd and nginx templates and restarts.
5. Calls `/healthz/` for up to 60 seconds. It must answer with the new version.

If the update steps or the health check fail, it rolls back **both the code and the database** and restarts the old version. The broken copy is kept as `/opt/worktrack/app.failed`. It also records the version as failed, so it isn't retried until a newer release appears.

Two runs never overlap (`flock`). Progress goes to `/var/lib/worktrack/update/status.json`, which the admin panel reads.

### "Check for updates now"

Site settings → Software updates shows:

- installed version, latest version and last check
- the state, with an icon and text

**Check for updates now** asks for the admin's password again and is refused in demo mode (`DEMO_MODE=True`). The web app never runs the updater itself: it only drops a request file, and `worktrack-update.path` starts the updater as root. The page follows progress. When the app restarts it shows a "Reload page" button. Each check is written to the activity log.

### Commands

```bash
systemctl start worktrack-update.service           # run an update check now
systemctl list-timers worktrack-update.timer       # next nightly run
journalctl -u worktrack-update -n 100              # what the last runs did
cat /var/log/worktrack/update-history.log          # one line per update / failure / refusal
cat /var/lib/worktrack/update/status.json          # current state
rm /var/lib/worktrack/update/failed_version        # allow a failed version to be tried again
```

**Rolling back by hand** after an update that passed its check but misbehaves:

```bash
systemctl stop worktrack
bash /opt/worktrack/app/deploy/linux/backup.sh --restore /var/backups/worktrack/<date>-pre-update-<version>
mv /opt/worktrack/app /opt/worktrack/app.bad && mv /opt/worktrack/app.previous /opt/worktrack/app
systemctl start worktrack
echo <version> > /var/lib/worktrack/update/failed_version
```

### Switching it off (or on again)

```bash
sudo bash /opt/worktrack/app/deploy/linux/install.sh --no-auto-update
sudo bash /opt/worktrack/app/deploy/linux/install.sh --auto-update OWNER/REPO --token-file /root/gh-token
```

To pause it for a while without removing anything: `systemctl disable --now worktrack-update.timer worktrack-update.path`.

### Network requirements

The server must reach, over HTTPS (port 443):

- `api.github.com`, for release information
- `github.com` and `*.githubusercontent.com` (`objects.githubusercontent.com`, `release-assets.githubusercontent.com`), for the downloads
- `pypi.org` and `files.pythonhosted.org`, for Python dependencies when they change

For a proxy, set `HTTPS_PROXY=http://proxy:3128` in `/etc/worktrack/updater.conf`.

### Private repository: the token

A private repository needs a token on the server. Create a **fine-grained personal access token**:

1. GitHub → Settings → Developer settings → Fine-grained tokens.
2. Repository access: only this repository.
3. Permissions: *Contents: Read-only* (Metadata read-only is added automatically).
4. Expiry: one year, with a calendar reminder to renew it.

Put it in a root-only file and pass it with `--token-file`, or set `TOKEN=` in `/etc/worktrack/updater.conf` (mode 600). The token can read code, not change it.

> **Keep two-factor authentication on for every GitHub account that can push to this repository or create releases.** Anyone who can publish a release can put code on every server that auto-updates from it.

## 3. Settings added for this layout

All of these are in `/etc/worktrack/worktrack.env`; see also `.env.example`.

| Setting | Meaning |
|---|---|
| `LOG_DIR` | Folder for the application log (default `logs/` in the project) |
| `CACHE_DIR` | File cache folder (default `cache/` in the project) |
| `UPDATE_STATUS_FILE` | The status file the updater writes and the admin panel reads |
| `UPDATE_REQUEST_DIR` | Folder the "Check now" button drops its request into; the panel is off when it does not exist |
| `DEMO_MODE` | `True` on a public demo: the update button is refused |
