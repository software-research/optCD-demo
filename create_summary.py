import json
import os
from collections import defaultdict

repos = defaultdict(list)

with open("repos-with-commit-counts.csv", "r") as f:
    for line in f:
        html_url, owner_repo, yaml_files, commit_count = line.strip().split(";")
        owner, repo = owner_repo.split("/")
        yaml_files = yaml_files.split(",")
        repos[(owner, repo)] = [y for y in yaml_files]

# repos with _ in their yaml file name
# zxing/zxing - 2 _'s in all
# openzipkin/zipkin - 1 _
# questdb/questdb - 1 _
# OpenRefine/OpenRefine - 2 _'s
# jetlinks/jetlinks-community - 1 _
# javaparser/javaparser - 1 _'s in both
# apache/maven - 2 _'s
# knowm/XChange - 3 _'s
# Tencent/spring-cloud-tencent - 1 _ in both

result = defaultdict(defaultdict)
project_all_unnecessary_directories = defaultdict(int)
project_maven_unnecessary_directories = defaultdict(int)

for f in os.listdir("all_results"):
    with open(f"all_results/{f}", "r") as f_json:
        owner, repo, rest = f.split("_", 2)
        yaml_filename, job = "", ""
        if owner == "zxing" and repo == "zxing":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-1])
        elif owner == "openzipkin" and repo == "zipkin":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-1])
        elif owner == "questdb" and repo == "questdb":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-1])
        elif owner == "OpenRefine" and repo == "OpenRefine":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-1])
        elif owner == "jetlinks" and repo == "jetlinks-community":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-1])
        elif owner == "javaparser" and repo == "javaparser":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-1])
        elif owner == "apache" and repo == "maven":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-1])
        elif owner == "knowm" and repo == "XChange":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:4])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[4:-1])
        elif owner == "Tencent" and repo == "spring-cloud-tencent":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-1])
        else:
            rest = rest.split("_")
            yaml_filename = rest[0]
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[1:-1])

        print(owner, repo, yaml_filename, job)
        data = json.load(f_json)

        result[(owner, repo, yaml_filename, job)]["Number of unnecessary directories (all)"] = len(data)
        if owner == "apache" and repo == "zeppelin":
            print("HERE: all", yaml_filename, job, len(data))


for f in os.listdir("maven_only_results"):
    with open(f"maven_only_results/{f}", "r") as f_json:
        owner, repo, rest = f.split("_", 2)
        yaml_filename, job = "", ""
        if owner == "zxing" and repo == "zxing":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-2])
        elif owner == "openzipkin" and repo == "zipkin":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-2])
        elif owner == "questdb" and repo == "questdb":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-2])
        elif owner == "OpenRefine" and repo == "OpenRefine":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-2])
        elif owner == "jetlinks" and repo == "jetlinks-community":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-2])
        elif owner == "javaparser" and repo == "javaparser":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-2])
        elif owner == "apache" and repo == "maven":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:3])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[3:-2])
        elif owner == "knowm" and repo == "XChange":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:4])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[4:-2])
        elif owner == "Tencent" and repo == "spring-cloud-tencent":
            rest = rest.split("_")
            yaml_filename = '_'.join(rest[:2])
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[2:-2])
        else:
            rest = rest.split("_")
            yaml_filename = rest[0]
            extension = ""
            for yaml_file in repos[(owner, repo)]:
                if yaml_file.startswith(yaml_filename):
                    extension = yaml_file.split(".")[-1]
            yaml_filename += "." + extension
            job = '_'.join(rest[1:-2])

        print(owner, repo, yaml_filename, job)
        data = json.load(f_json)

        result[(owner, repo, yaml_filename, job)]["Number of unnecessary directories (maven)"] = len(data)
        if owner == "apache" and repo == "zeppelin":
            print("HERE: maven", yaml_filename, job, len(data))

with open("job-based-results.csv", "w") as f:
    for key, value in result.items():
        row = ';'.join(key) + ";" + str(value.get("Number of unnecessary directories (all)", 0)) + ";" + str(value.get("Number of unnecessary directories (maven)", 0)) + "\n";
        f.write(row)
        owner, repo, _, _ = key
        project_all_unnecessary_directories[(owner, repo)] += value.get("Number of unnecessary directories (all)", 0)
        project_maven_unnecessary_directories[(owner, repo)] += value.get("Number of unnecessary directories (maven)", 0)

with open("project-based-results.csv", "w") as f:
    for key, value in project_all_unnecessary_directories.items():
        row = ';'.join(key) + ";" + str(value) + ";" + str(project_maven_unnecessary_directories[key]) + "\n"
        f.write(row)