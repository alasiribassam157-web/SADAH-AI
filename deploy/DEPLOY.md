# Permanent 24/7 link

The local tunnel (`launch_platform.bat`) only works while your laptop is on, and
its `trycloudflare.com` address changes on every launch. For a fixed `https://`
address that stays up with the laptop closed, deploy the GitHub repo with the
`Dockerfile`.

## Render (free, sleeps after 15 min idle, 512 MB RAM)

1. Sign in at https://render.com with GitHub.
2. **New → Blueprint** and pick the `SADAH-AI` repo. `render.yaml` is detected.
3. Fill `SADAH_ACCESS_TOKEN` with any long random value. It is a private service key,
   not a visitor password.
4. Your permanent link: `https://sadah-app.vercel.app`.
   After pushing changes, use **Manual Deploy → Deploy latest commit** if auto-deploy
   does not trigger.

## Hugging Face Spaces

Docker Spaces now require a PRO subscription. The YAML header in `README.md`
already configures a Space (docker, port 7860) if you subscribe.

## Safe mode in the cloud

The Docker image sets `SADAH_SAFE_MODE=1`, which disables the Python-executor and
system-command tools on a public server. File management (inside the container's
`workspace/`), web research and safe math keep working.
