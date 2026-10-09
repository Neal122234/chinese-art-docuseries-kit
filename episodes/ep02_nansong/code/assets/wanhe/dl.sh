#!/bin/zsh
cd "$(dirname $0)"
while read lab w h svc; do
  [ -s full/$lab.jpg ] && continue
  curl -s -m 120 --retry 3 -o full/$lab.jpg "$svc/full/full/0/default.jpg"
  echo "$lab $(stat -f %z full/$lab.jpg)"
done < canvases.tsv
echo DONE
