# Local SEO Workbench

A private, local dashboard for the Students Time and Learner's Link SEO workflow. It reads the saved Search Console, Analytics, AdSense, indexing, competitor and action-queue reports; can refresh the reporting pipeline; connects Google OAuth; and offers an optional Gemini SEO copilot.

## Start the app

1. Install Python 3.10 or newer.
2. Run `START-SEO-APP.sh` on Linux/macOS, or double-click `START-SEO-APP.bat` on Windows.
3. The first launch creates a local `.venv` and installs the Python packages. The app opens at <http://127.0.0.1:5000>.
4. Keep the terminal window open while using the app. Press Ctrl+C there to stop it.

The server listens only on your computer (`127.0.0.1`). It is not published to the internet.

## Connect Google

The dashboard's **Connect Google** button uses the project's existing Installed App OAuth flow. Add a Google OAuth **Desktop app** client JSON file named `client_secret.json` to this project folder, then use the button and open the sign-in link it provides. Google API credentials are stored under your user configuration folder; the Blogger token remains in the ignored local project file for existing Blogger scripts. Do not commit OAuth files.

Enable the Google APIs used by the reporting workflow in the OAuth project's Google Cloud configuration and add your account as a test user if the consent screen is in testing mode. The app reports Google/API authorization errors in the dashboard.

## Gemini copilot

Create an API key in [Google AI Studio](https://aistudio.google.com/apikey), paste it into **Gemini SEO copilot**, and save it. The key is stored outside this repository at `~/.config/seo-workbench/gemini-api-key` on Linux/macOS, with owner-only file permissions. The copilot sends your question, selected site, saved Search Console query summary, and a few open action items to Google's Gemini API. It only returns suggestions; it does not edit or publish Blogger content.

The copilot currently uses `gemini-3.5-flash-lite`. Change `GEMINI_MODEL` in `dashboard/app.py` if you choose another model enabled for your API key. Google controls model availability, limits and billing; check the [Gemini API model list](https://ai.google.dev/gemini-api/docs/models) and [API key guidance](https://ai.google.dev/gemini-api/docs/api-key).

## Refresh reports

Use **Run full SEO refresh** in the dashboard. It runs weekly Google metrics, 90-day Search Console keyword clusters, and the saved SEO workbench refresh. This is a read-only reporting workflow: it does not edit or publish Blogger posts. A valid Google OAuth connection and network access are needed for fresh data. **Reload saved** only reloads reports already on disk.

Some older dashboard tools (such as PageSpeed CLI and Bing submission) still depend on their configured local API keys or optional external CLI. The main report, queue, Google connection and Gemini copilot do not require `claude-seo`.

## Keep credentials private

OAuth clients, access tokens and API keys belong in local configuration only. Review `.gitignore` before adding any new credential file; never paste a key into source code, reports, or a public commit.
