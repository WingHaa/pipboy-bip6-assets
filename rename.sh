#!/bin/bash

# Use current directory if no argument is given
target_dir="${1:-.}"

if [ ! -d "$target_dir" ]; then
  echo "❌ Error: '$target_dir' is not a valid directory."
  exit 1
fi

i=0
for file in "$target_dir"/*.png; do
  # Skip if no PNG files found
  [ -e "$file" ] || continue

  newname=$(printf "anim_%d.png" "$i")
  mv -- "$file" "$target_dir/$newname"
  ((i++))
done

echo "✅ Renamed $i file(s) in '$target_dir'."
