# Equivalente en PowerShell de scripts/install-hooks.sh
Set-Location (git rev-parse --show-toplevel)
git config core.hooksPath hooks
git config alias.pushp '!f() { git push "$@" && sh hooks/post-push; }; f'
Write-Host "Hooks activados (core.hooksPath=hooks). Usa 'git pushp' para ejecutar tambien post-push."
