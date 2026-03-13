# AutoQuant Install

1. Persist environment variables in ~/.openclaw/.env (add or create)

MASSIVE_API_KEY=<your_massive_api_key>
AUTOQUANT_WORKSPACE=$HOME/Documents/autoquant


2. Create a virtual environment in the workspace.
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/venv"
   python3 -m venv "$AUTOQUANT_WORKSPACE/venv/autoquant"
   ```

3. Install AutoQuant CLI
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install "git+https://github.com/dev0xx1/autoquant-cli.git@main"
   ```

4. Create a persistent shell launcher (one-time) so `autoquant` works in every new bash session without venv activation.
   ```bash
   mkdir -p "$HOME/.local/bin"
   cat > "$HOME/.local/bin/autoquant" << 'EOF'
   #!/usr/bin/env bash
   exec "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/autoquant" "$@"
   EOF
   chmod +x "$HOME/.local/bin/autoquant"
   grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
   source "$HOME/.bashrc"
   ```

5. Pull docs to ensure local docs clone is present and up to date.
   ```bash
   autoquant pull-docs
   ```

6. Verify env setup with status.
   ```bash
   autoquant status
   ```

7. Read the README.md and bootstrap yourself as Autoquant then delete bootstrap.md