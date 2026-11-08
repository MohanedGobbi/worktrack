# University of Ghardaia version

The University of Ghardaia (Faculty of Law and Political Science) install of WorkTrack Pro. Same code as `main`;
this folder holds everything specific to the university, applied as data (Site Settings), never by editing templates.

| File | Use |
|---|---|
| `institution.json` | `manage.py new_institution --config institutions/ghardaia/institution.json`: name EN/AR, colours (green #116333 from the logo, light green accent), Arabic default, the 22 units of the faculty structure, 7 roles, partner, first admin. |
| `university-logo.png` | Site logo (sidebar, sign-in, landing). |
| `faculty-building.jpg` | Banner image behind page heads (under a green overlay). |
| `partner-afak.jpg` | Partner logo, shown as "In partnership with" next to the ROWD credit. |
| `campus-poster.jpg` | Spare: campus photo with the logo, for a future sign-in background. |

## Run it on this computer

Double-click `run_ghardaia.bat` (project folder). It uses its own database (`db_ghardaia.sqlite3`) and uploads
folder (`media_ghardaia/`), so the ROWD demo version is not touched. The first run sets the university up and
writes the first administrator's password to `ghardaia_setup.log` (shown in the window too). It serves on
http://127.0.0.1:8001/ so both versions can run side by side.

## Still to settle with the faculty

Official English unit names, partner website, the real administrator account, contact details and domain,
the staff list (bulk import command still to build), and the vocabulary (see HANDOFF.md section 2c).
The ROWD credit stays on every page; do not remove `templates/includes/rowd_credit.html` or `tests/test_credit.py`.
