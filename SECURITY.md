# Security

Never commit:

- API keys or registration tokens
- GitHub runner credentials
- Tailscale credentials
- `.env` files
- private keys
- local memory or vector databases
- audit logs containing personal paths
- model weights
- personal documents

Repository examples must use placeholders. Runtime access is granted using
local configuration that remains outside Git.
