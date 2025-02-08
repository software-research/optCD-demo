import json
import csv


# Load the JSON file
with open("updated_prompt_result.json", "r") as file:  # Replace "data.json" with the actual filename
    data = json.load(file)

## IDs to process
#ids_to_check = {"0", "1", "2", "5"}
#
## Dictionary to store results
#results = {}
#
#for id_key in ids_to_check:
#    if id_key in data:
#        unused_dirs_count = len(data[id_key].get("unused_dirs", []))
#        unused_dirs_w_fix_count = len(data[id_key].get("unused_dirs_w_fix", []))
#        results[id_key] = {
#            "unused_dirs_count": unused_dirs_count,
#            "unused_dirs_w_fix_count": unused_dirs_w_fix_count
#        }
#
## Print the results
#for id_key, counts in results.items():
#    print(f"ID: {id_key}")
#    print(f"  Unused Dirs: {counts['unused_dirs_count']}")
#    print(f"  Unused Dirs with Fix: {counts['unused_dirs_w_fix_count']}")
#    print("-")
#
max_id = 613

# Dictionary to store counts
counts = {}

csv_data = [["ID", "Unused Dirs Count", "Unused Dirs W Fix Count"]]
# Loop through IDs from 0 to max_id
for i in range(max_id + 1):
    str_id = str(i)  # JSON keys are strings
    if str_id in data:
        unused_dirs_count = len(data[str_id].get("unused_dirs", []))
        unused_dirs_w_fix_count = len(data[str_id].get("unused_dirs_w_fix", []))
        csv_data.append([str_id, unused_dirs_count, unused_dirs_w_fix_count])

        #unused_dirs_count = len(data[str_id].get("unused_dirs", []))
        #unused_dirs_w_fix_count = len(data[str_id].get("unused_dirs_w_fix", []))
        #counts[str_id] = {
        #    "unused_dirs": unused_dirs_count,
        #    "unused_dirs_w_fix": unused_dirs_w_fix_count,
        #}

## Print results
#for key, value in counts.items():
#    print(f"ID: {key}, Unused Dirs: {value['unused_dirs']}, Unused Dirs w/ Fix: {value['unused_dirs_w_fix']}")
# Write to CSV file
output_csv = "unused_dirs_counts.csv"

with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(csv_data)

print(f"CSV file saved: {output_csv}")
