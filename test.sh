#!/bin/bash

i=0
while [ $i -lt 10 ]; do
	echo output $i
	((i++))
	sleep 1
done
