#!/bin/bash

DATA_PATH="/home/exouser/2510"

cat $DATA_PATH/ghRepos202510.u.26 | while read r; do
  a=$(git ls-remote gh:$r | awk '{print ";"$1}'); echo gh:$r$a | sed 's/ //g';
done | gzip > $DATA_PATH/ghRepos202510.u.26.heads

cat $DATA_PATH/ghForks202510.u.26 | while read r; do
  a=$(git ls-remote gh:$r | awk '{print ";"$1}'); echo gh:$r$a | sed 's/ //g';
done | gzip > $DATA_PATH/ghForks202510.u.26.heads

