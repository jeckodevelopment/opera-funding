#!/usr/bin/env python3
"""Upload built static site over pinned-host-key SFTP (no remote deletions)."""
import os
from pathlib import Path, PurePosixPath
import paramiko

def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing secret {name}")
    return value

def main():
    host = required("SFTP_HOST")
    user = required("SFTP_USERNAME")
    destination = required("SFTP_REMOTE_DIR")
    known_hosts = required("SFTP_KNOWN_HOSTS")
    if not destination.startswith("/") or ".." in PurePosixPath(destination).parts:
        raise ValueError("SFTP_REMOTE_DIR must be an absolute safe path")
    build_dir = Path(__file__).resolve().parents[1] / "dist"
    if not build_dir.is_dir():
        raise ValueError("Build output missing")
    client = paramiko.SSHClient()
    # Host key must be supplied explicitly; never accept unknown keys.
    hostkeys = paramiko.HostKeys()
    known_file = Path("/tmp/opera_funding_known_hosts")
    known_file.write_text(known_hosts + "\n", encoding="utf-8")
    known_file.chmod(0o600)
    client.load_host_keys(str(known_file))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    password = os.environ.get("SFTP_PASSWORD") or None
    key_file = os.environ.get("SFTP_PRIVATE_KEY_FILE") or None
    if not password and not key_file:
        raise ValueError("Set SFTP_PASSWORD or SFTP_PRIVATE_KEY_FILE")
    try:
        client.connect(hostname=host, port=int(os.environ.get("SFTP_PORT") or "22"),
                       username=user, password=password, key_filename=key_file,
                       look_for_keys=False, allow_agent=False, timeout=20)
        with client.open_sftp() as sftp:
            def mkdirs(remote):
                parts = PurePosixPath(remote).parts
                current = ""
                for part in parts:
                    if part == "/":
                        current = "/"
                        continue
                    current = str(PurePosixPath(current) / part)
                    try:
                        sftp.stat(current)
                    except FileNotFoundError:
                        sftp.mkdir(current)
            mkdirs(destination)
            for file in sorted(build_dir.rglob("*")):
                if not file.is_file():
                    continue
                relative = file.relative_to(build_dir)
                remote = str(PurePosixPath(destination).joinpath(*relative.parts))
                mkdirs(str(PurePosixPath(remote).parent))
                sftp.put(str(file), remote, confirm=True)
                print(f"Uploaded {relative}")
    finally:
        client.close()
        known_file.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
