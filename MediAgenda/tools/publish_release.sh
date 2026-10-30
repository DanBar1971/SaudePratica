#!/usr/bin/env bash
# Only run on trusted master after successful build and ORIGINAL certificate check.
set -euo pipefail
TAG="${1:?expected version tag}"
CODE="${2:?expected numeric Android versionCode}"
SHA="${3:?expected signed APK sha256}"
REPO="${GITHUB_REPOSITORY:?repository is required}"
[[ "$REPO" == 'DanBar1971/SaudePratica' ]] || { echo 'Unexpected repository' >&2; exit 1; }
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
[[ "$CODE" =~ ^[0-9]+$ ]] || exit 1
[[ "$SHA" =~ ^[a-f0-9]{64}$ ]] || exit 1
printf '%s  SaudePratica.apk\n' "$SHA" | sha256sum -c -

# Releases are immutable. A later source change must bump the Android version.
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo "::notice title=Release já publicada::$TAG existe. Para publicar outra APK, aumenta versionName e versionCode."
    exit 0
fi

NOTES="MediAgenda/v$((CODE+10))_overrides/RELEASE_NOTES.md"
if [ ! -s "$NOTES" ]; then
    NOTES="$(mktemp)"
    printf 'SaúdePrática %s — atualização verificada e assinada com o certificado Android original.\n' "$TAG" > "$NOTES"
fi
SOURCE="SaudePratica-${TAG}-CODIGO-FONTE.zip"
HASHES="SaudePratica-${TAG}-SHA256SUMS.txt"
git archive --format=zip --output="$SOURCE" HEAD
sha256sum SaudePratica.apk "$SOURCE" > "$HASHES"

# Do not include keystore, original private ZIP, recovery key, passwords or clinical data.
gh release create "$TAG" SaudePratica.apk "$SOURCE" "$HASHES" \
    --repo "$REPO" --target "$GITHUB_SHA" \
    --title "SaúdePrática ${TAG} — APK assinada" \
    --notes-file "$NOTES" --latest

gh release view "$TAG" --repo "$REPO" --json tagName,isDraft,isPrerelease,assets |
  jq -e --arg tag "$TAG" '.tagName == $tag and (.isDraft|not) and (.isPrerelease|not) and any(.assets[]; .name=="SaudePratica.apk")' >/dev/null
# GitHub Pages dynamically uses releases/latest; still redeploy after each release.
gh workflow run pages.yml --repo "$REPO" --ref main
echo "::notice title=Release publicada::https://github.com/${REPO}/releases/tag/${TAG}"
echo "::notice title=Website atualizado::https://danbar1971.github.io/SaudePratica/"