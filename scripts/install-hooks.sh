#!/bin/sh
# Activa los hooks versionados en hooks/ y crea el alias 'git pushp' (push + post-push).
cd "$(git rev-parse --show-toplevel)" || exit 1
git config core.hooksPath hooks
git config alias.pushp '!f() { git push "$@" && sh hooks/post-push; }; f'
chmod +x hooks/* 2>/dev/null
echo "✅ Hooks activados (core.hooksPath=hooks). Usa 'git pushp' para ejecutar tambien post-push."
