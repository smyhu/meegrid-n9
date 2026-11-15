#!/bin/sh
# Builds meegrid-n9_<version>_all.deb: daemon + upstart job + app.
# Usage: sh packaging/build-deb.sh [output-dir]
# Needs: ar, tar, python3 (PIL), sha1sum, md5sum.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=$(sed -n 's/^APP_VERSION = .\(.*\).$/\1/p' "$ROOT/app/main.py")
DVERSION=$(sed -n 's/^VERSION = .\(.*\).$/\1/p' "$ROOT/daemon/meegridd.py")
CVERSION=$(sed -n 's/^VERSION = .\(.*\).$/\1/p' "$ROOT/app/core.py")
[ "$VERSION" = "$DVERSION" ] && [ "$VERSION" = "$CVERSION" ] || { echo "ERROR: app $VERSION != daemon $DVERSION" >&2; exit 1; }
OUT=${1:-$ROOT/dist}
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
D=$T/data/opt/meegrid-n9
mkdir -p "$D/qml" "$T/data/etc/init/apps" "$T/data/usr/share/applications" \
         "$T/data/usr/share/icons/hicolor/80x80/apps" "$T/ctl"
cp "$ROOT/daemon/meegridd.py" "$D/"
cp "$ROOT/app/main.py" "$ROOT/app/core.py" "$D/"; cp "$ROOT/app/qml/"* "$D/qml/"
cp "$ROOT/LICENSE" "$D/LICENSE"
cp "$ROOT/packaging/meegrid-n9.conf" "$T/data/etc/init/apps/"
cp "$ROOT/packaging/meegrid-n9.desktop" "$T/data/usr/share/applications/"
cp "$ROOT/art/meegrid-n9.png" "$T/data/usr/share/icons/hicolor/80x80/apps/"
chmod -R u+rwX,go+rX,go-w "$T/data"
chmod 755 "$D/meegridd.py" "$D/main.py" "$D/core.py"
SIZE=$(du -sk "$T/data" | cut -f1)
python3 - "$ROOT/packaging/control" "$T/ctl/control" "$VERSION" "$SIZE" "$ROOT/art/meegrid-n9.png" <<'P'
import sys, base64, io
from PIL import Image
src, dst, version, size, icon = sys.argv[1:]
buf = io.BytesIO(); Image.open(icon).resize((64, 64), Image.LANCZOS).save(buf, "PNG")
b = base64.b64encode(buf.getvalue()).decode("ascii")
lines = "\n".join(" " + b[i:i + 76] for i in range(0, len(b), 76))
t = open(src).read().replace("@VERSION@", version).replace("@SIZE@", size).replace("@ICON@", lines)
open(dst, "w").write(t)
P
for s in postinst prerm postrm; do cp "$ROOT/packaging/$s" "$T/ctl/$s"; done
echo /etc/init/apps/meegrid-n9.conf > "$T/ctl/conffiles"
(cd "$T/data" && find . -type f | sed 's#^\./##' | sort | xargs md5sum) > "$T/ctl/md5sums"
entry() { printf 'S 15 com.nokia.maemo H 40 %s R %d %s\n' "$1" "${#2}" "$2"; }
(cd "$T/data" && find . -type f | sed 's#^\./##' | sort | while read -r f; do
    entry "$(sha1sum "$f" | cut -d' ' -f1)" "$f"; done) > "$T/ctl/digsigsums"
chmod 644 "$T/ctl/"*; chmod 755 "$T/ctl/postinst" "$T/ctl/prerm" "$T/ctl/postrm"
(cd "$T/ctl" && tar czf ../control.tar.gz --owner=0 --group=0 --numeric-owner --format=gnu ./control ./conffiles ./md5sums ./digsigsums ./postinst ./prerm ./postrm)
# Aegis cannot read GNU long-name tar entries: every path must stay under 100 chars
long=$(cd "$T/data" && find . | awk 'length($0) > 95')
[ -z "$long" ] || { echo "ERROR: path too long for Aegis: $long" >&2; exit 1; }
(cd "$T/data" && tar czf ../data.tar.gz --owner=0 --group=0 --numeric-owner --format=gnu .)
echo 2.0 > "$T/debian-binary"
DEB="$OUT/meegrid-n9_${VERSION}_all.deb"
rm -f "$DEB"
(cd "$T" && ar rc "$DEB" debian-binary control.tar.gz data.tar.gz)
ls -l "$DEB"; md5sum "$DEB"
