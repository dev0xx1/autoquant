# AutoQuant Install

1. Work with the user to setup the following environment variables (https://docs.openclaw.ai/help/environment)

MASSIVE_API_KEY=<your_massive_api_key>
AUTOQUANT_WORKSPACE=$HOME/Documents/autoquant


2. Create a virtual environment in the workspace.
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/venv"
   python3 -m venv "$AUTOQUANT_WORKSPACE/venv/autoquant"
   ```

3. Install AutoQuant CLI
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install "git+https://github.com/dev0xx1/autoquant.git@main"
   ```

4. Verify env setup with status.
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/autoquant" status
   ```
