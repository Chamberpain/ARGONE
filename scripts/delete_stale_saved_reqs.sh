#!/bin/bash

cache_path="$1"
numtosave="$2"

# we can store around 15k requests, under-estimate

ls -t $cache_path/closest_index* | tail -n+$numtosave | xargs rm 2> /dev/null
