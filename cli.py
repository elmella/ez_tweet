"""Simple local UI to post tweets via X API."""
from __future__ import annotations

import argparse
import json
import logging
import os
import threading
from dataclasses import dataclass
from typing import Dict, Optional

import tweepy
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)

CREDENTIAL_KEYS = (
    "X_BEARER_TOKEN",
    "X_CONSUMER_KEY",
    "X_CONSUMER_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
)


@dataclass
class Credentials:
    bearer_token: str
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_secret: str

    @classmethod
    def from_mapping(cls, mapping: Dict[str, str]) -> "Credentials":
        missing = [key for key in CREDENTIAL_KEYS if not mapping.get(key)]
        if missing:
            raise ValueError(f"Missing X credentials: {', '.join(missing)}")
        return cls(
            bearer_token=mapping["X_BEARER_TOKEN"],
            consumer_key=mapping["X_CONSUMER_KEY"],
            consumer_secret=mapping["X_CONSUMER_SECRET"],
            access_token=mapping["X_ACCESS_TOKEN"],
            access_secret=mapping["X_ACCESS_SECRET"],
        )


class XClient:
    """Thin wrapper around tweepy to create tweets."""

    def __init__(self, credentials: Credentials):
        self.client = tweepy.Client(
            bearer_token=credentials.bearer_token,
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
            access_token=credentials.access_token,
            access_token_secret=credentials.access_secret,
            wait_on_rate_limit=True,
        )

    def post(self, text: str, dry_run: bool = False) -> Optional[str]:
        """Post text to X.

        Returns the tweet ID when successful; returns None in dry-run mode.
        """
        if dry_run:
            logger.info("[dry-run] Would have posted: %s", text)
            return None

        response = self.client.create_tweet(text=text)
        tweet_id = response.data.get("id") if response and response.data else None
        logger.info("Published tweet with id %s", tweet_id)
        return tweet_id


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_config_file(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file {path} does not exist")

    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return {k: str(v) for k, v in data.items()}

    config: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def load_credentials(config_path: Optional[str]) -> Credentials:
    config = {}
    if config_path:
        config = parse_config_file(config_path)
        logger.debug("Loaded credentials from %s", config_path)

    merged = {key: os.environ.get(key) or config.get(key, "") for key in CREDENTIAL_KEYS}
    return Credentials.from_mapping(merged)


def validate_text(text: str, max_length: int) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Message is empty after trimming whitespace")
    if len(cleaned) > max_length:
        raise ValueError(f"Text exceeds maximum length of {max_length} characters")
    return cleaned


class TweetApp:
    def __init__(self, client: XClient, max_length: int, dry_run: bool):
        self.client = client
        self.max_length = max_length
        self.dry_run = dry_run

        self.root = tk.Tk()
        self.root.title("ez_tweet")

        self.text = tk.Text(self.root, height=8, width=60, wrap="word")
        self.text.pack(padx=10, pady=(10, 4))
        self.text.bind("<KeyRelease>", self.update_count)

        self.count_var = tk.StringVar(value=self._count_label(0))
        self.count_label = tk.Label(self.root, textvariable=self.count_var, anchor="e")
        self.count_label.pack(fill="x", padx=10)

        self.post_button = tk.Button(self.root, text="Post", command=self.post_message)
        self.post_button.pack(pady=(4, 2))

        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, fg="gray")
        self.status_label.pack(padx=10, pady=(2, 10))

    def _count_label(self, length: int) -> str:
        return f"Characters: {length}/{self.max_length}"

    def update_count(self, event=None) -> None:
        content = self.text.get("1.0", "end-1c")
        self.count_var.set(self._count_label(len(content)))

    def post_message(self) -> None:
        content = self.text.get("1.0", "end")
        try:
            validated = validate_text(content, self.max_length)
        except ValueError as exc:
            messagebox.showerror("Invalid text", str(exc))
            return

        self.post_button.config(state="disabled")
        self.status_var.set("Posting..." if not self.dry_run else "Logging (dry-run)...")

        def worker() -> None:
            try:
                tweet_id = self.client.post(validated, dry_run=self.dry_run)
                status = "Logged locally (dry-run)." if self.dry_run else f"Posted! Tweet ID: {tweet_id}"
                self.root.after(0, lambda: self.status_var.set(status))
            except Exception as exc:  # pragma: no cover - network/runtime errors
                logger.error("Failed to post update: %s", exc)
                self.root.after(0, lambda: messagebox.showerror("Post failed", str(exc)))
                self.root.after(0, lambda: self.status_var.set(""))
            finally:
                self.root.after(0, lambda: self.post_button.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple local UI to post to X.")
    parser.add_argument(
        "--config",
        help="Optional path to a config file (JSON or KEY=VALUE lines) with X credentials.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be posted without calling the X API.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=280,
        help="Maximum allowed characters for the post (default: 280).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    configure_logging(args.verbose)

    try:
        credentials = load_credentials(args.config)
    except Exception as exc:
        logger.error("Credential loading failed: %s", exc)
        raise SystemExit(1) from exc

    client = XClient(credentials)
    app = TweetApp(client=client, max_length=args.max_length, dry_run=args.dry_run)
    app.run()


if __name__ == "__main__":
    run(parse_args())
