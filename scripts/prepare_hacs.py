"""Set repository metadata before publishing to HACS."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("repository", help="GitHub owner/repository, e.g. yourname/wattwanneer")
args = parser.parse_args()
parts = args.repository.split("/")
if (
    len(parts) != 2
    or not all(parts)
    or any(not all(c.isalnum() or c in "-_." for c in part) for part in parts)
):
    parser.error("Expected GitHub owner/repository")
root = Path(__file__).resolve().parents[1]
path = root / "custom_components/wattwanneer_public/manifest.json"
manifest = json.loads(path.read_text())
manifest.update(
    codeowners=["@" + parts[0]],
    documentation="https://github.com/" + args.repository,
    issue_tracker="https://github.com/" + args.repository + "/issues",
)
path.write_text(json.dumps(manifest, indent=2) + "\n")
print("HACS publishing metadata configured for " + args.repository)
