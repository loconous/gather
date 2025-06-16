#!/bin/bash

DATA_PATH="/home/exouser/25q1"

cat $DATA_PATH/gh202504.u.26 | while read r; do
  a=$(git ls-remote gh:$r | awk '{print ";"$1}'); echo gh:$r$a | sed 's/ //g';
done | gzip > $DATA_PATH/gh202504.u.26.heads

