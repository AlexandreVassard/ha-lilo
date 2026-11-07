#!/usr/bin/env bash
# Dump every vendor characteristic of a Lilo (c9d9bfe1 firmware) via bluetoothctl.
# Usage: ssh ha 'bash -s' < tools/snapshot.sh [MAC]
MAC="${1:-ED:E7:3E:59:7D:D6}"
DEV="/org/bluez/hci0/dev_${MAC//:/_}/service000e"
{
  echo "connect $MAC"; sleep 10
  echo "menu gatt"
  for h in 000f 0012 0014 0016 0018 001a 001c 001e 0020 0022 0024; do
    echo "select-attribute $DEV/char$h"; echo read; sleep 1.5
  done
  echo back; echo "disconnect $MAC"; sleep 2; echo quit
} | bluetoothctl 2>&1 | sed "s/\x1b\[[0-9;]*m//g; s/\r/\n/g" | awk '
  function hexval(s,  i, r) { r = 0; for (i = 1; i <= length(s); i++) r = r * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1; return r }
  BEGIN { split("000f:e2 0012:e3 0014:e4 0016:e5 0018:e6 001a:e7 001c:e8 001e:e9 0020:ea 0022:eb 0024:ec", m, " ")
          for (i in m) { split(m[i], kv, ":"); name["char" kv[1]] = kv[2] } }
  /Failed|not available/ { print }
  /Attribute .*Value:/ {
    match($0, /char[0-9a-f]+/); c = substr($0, RSTART, RLENGTH)
    getline; while ($0 ~ /^\[Lilo/ || $0 ~ /^ *$/) getline
    hex = substr($0, 3, 48); gsub(/ +$/, "", hex)
    n = split(hex, b, " "); v = 0
    for (i = n; i >= 1; i--) v = v * 256 + hexval(b[i])
    extra = (n == 4) ? sprintf("  (%02d:%02d:%02d)", int(v/3600), int(v%3600/60), v%60) : ""
    printf "%s  %-12s = %6d%s\n", name[c], hex, v, extra
  }'
