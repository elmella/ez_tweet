# ez_tweet

Post tweets from your account without needing to open the site.

## Installation

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The app expects standard X (Twitter) credentials. Supply them via environment
variables or a config file (JSON or simple `KEY=VALUE` lines):

- `X_BEARER_TOKEN`
- `X_CONSUMER_KEY`
- `X_CONSUMER_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_SECRET`

Example `.env`-style file:

```
X_BEARER_TOKEN=YOUR_BEARER_TOKEN
X_CONSUMER_KEY=YOUR_CONSUMER_KEY
X_CONSUMER_SECRET=YOUR_CONSUMER_SECRET
X_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
X_ACCESS_SECRET=YOUR_ACCESS_SECRET
```

Example JSON file:

```json
{
  "X_BEARER_TOKEN": "YOUR_BEARER_TOKEN",
  "X_CONSUMER_KEY": "YOUR_CONSUMER_KEY",
  "X_CONSUMER_SECRET": "YOUR_CONSUMER_SECRET",
  "X_ACCESS_TOKEN": "YOUR_ACCESS_TOKEN",
  "X_ACCESS_SECRET": "YOUR_ACCESS_SECRET"
}
```

## Usage

Launch the simple local window, type your post in the text box, and click
**Post**. A character counter helps stay within the default 280-character limit.

```bash
python cli.py --config ~/.config/ez_tweet.env
```

Key options:

- `--dry-run` logs what would be posted without calling the X API.
- `--max-length` sets the character limit (default 280).
- `--verbose` enables debug logging.

If you prefer environment variables, omit `--config` and set the credentials
before launching the app. Close the window to exit.
