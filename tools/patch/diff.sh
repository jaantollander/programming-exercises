#!/usr/bin/env bash
printf "\n" > a
printf "Hello\nWorld\n" > b
diff -u a b > a.patch
