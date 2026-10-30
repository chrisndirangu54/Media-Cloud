# Media Cloud v0.6 source migration

The branch currently contains a **partial bootstrap**. Do not merge as a complete v0.6 import.

The full v0.6 package was verified locally (11 tests passing) and bundled with a GitHub Actions CI workflow plus `scripts/push-to-github.sh`. The bundle is available in the current ChatGPT conversation as `Media_Cloud_v0.6_GitHub_Ready.zip`.

## Import on a machine with authenticated GitHub access

1. Download and unzip the full package from the conversation.
2. Open a terminal in `media-cloud-github-ready`.
3. Install dependencies: `pip install -r requirements.txt pytest httpx`.
4. Execute `bash scripts/push-to-github.sh`.
5. Open a PR from `import/media-cloud-v0.6-complete` into `main` and review the CI tests.

Do not add secrets to the repository. The full archive is development code, and social OAuth, production billing, and completed BeatSync rendering remain unfinished.
