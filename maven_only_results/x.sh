for file in jhy*.json; do
  # Replace 'jhy' with 'butterfly-lab' in each filename
  newname="${file//jhy/butterfly-lab}"
  mv "$file" "$newname"
done

