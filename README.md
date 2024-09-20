# optCD-demo
Demo tool for OptCD

## Usage

```
gh auth login # if you are not already logged in to gh cli
./run.sh <path/to/input/yaml/file> <path/to/output/yaml/file> <owner> <repo> <github-api-token>

<path/to/input/yaml/file> must point to {local_repo_root}/.github/workflows/{your_workflow}.yml
<path/to/output/yaml/file> must point to {local_repo_root}/.github/workflows/{modified_workflow}.yml
<owner> is the owner of the repo of the remote repository
<repo> is the name of the remote repository
<github-api-token> is a GitHub API Token that has read and write access to the remote repository 

Example run:
./run.sh ../JSqlParser/.github/workflows/maven.yml ../JSqlParser/.github/workflows/modified-maven.yml ogul1 JSqlParser <github-api-token>

Example output:
Requirement already satisfied: requests==2.32.3 in ./venv/lib/python3.12/site-packages (from -r requirements.txt (line 1)) (2.32.3)
Requirement already satisfied: python-dateutil==2.9.0 in ./venv/lib/python3.12/site-packages (from -r requirements.txt (line 2)) (2.9.0)
Requirement already satisfied: inotify==0.2.10 in ./venv/lib/python3.12/site-packages (from -r requirements.txt (line 3)) (0.2.10)
Requirement already satisfied: pyyaml==6.0.2 in ./venv/lib/python3.12/site-packages (from -r requirements.txt (line 4)) (6.0.2)
Requirement already satisfied: charset-normalizer<4,>=2 in ./venv/lib/python3.12/site-packages (from requests==2.32.3->-r requirements.txt (line 1)) (3.3.2)
Requirement already satisfied: idna<4,>=2.5 in ./venv/lib/python3.12/site-packages (from requests==2.32.3->-r requirements.txt (line 1)) (3.7)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./venv/lib/python3.12/site-packages (from requests==2.32.3->-r requirements.txt (line 1)) (2.2.2)
Requirement already satisfied: certifi>=2017.4.17 in ./venv/lib/python3.12/site-packages (from requests==2.32.3->-r requirements.txt (line 1)) (2024.7.4)
Requirement already satisfied: six>=1.5 in ./venv/lib/python3.12/site-packages (from python-dateutil==2.9.0->-r requirements.txt (line 2)) (1.16.0)
Requirement already satisfied: nose in ./venv/lib/python3.12/site-packages (from inotify==0.2.10->-r requirements.txt (line 3)) (1.3.7)
name: Maven CI
on: [push, workflow_dispatch]
jobs:
  package:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        java: [11]
    name: Java ${{ matrix.java }} building ...
    steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pandas
        pip install numpy
        pip install inotify
    - name: Run inotifywait
      run: |
        python3 -c "
        import inotify.adapters
        from datetime import datetime, timezone
        with open('/home/runner/inotifywait-log-Java ${{ matrix.java }} building ....csv', 'w') as log_file:
          i = inotify.adapters.InotifyTree('/home/runner/work/JSqlParser/JSqlParser/')
          for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
            events = ','.join(type_names)
            log_file.write(f'{now};{path};{filename};{events}\n')
        " &
    - uses: actions/checkout@v3
    - name: Set up Java ${{ matrix.java }}
      uses: actions/setup-java@v3
      with:
        java-version: ${{ matrix.java }}
        distribution: 'temurin'
        cache: maven
        server-id: sonatype-nexus-snapshots
        server-username: MAVEN_USERNAME
        server-password: MAVEN_PASSWORD
    - name: Build with Maven
      run: mvn -B package --file pom.xml
      env:
        MAVEN_USERNAME: ${{ secrets.OSSRHUSERNAME }}
        MAVEN_PASSWORD: ${{ secrets.OSSRHPASSWORD }}
    - name: Upload inotifywait logs as artifact
      uses: actions/upload-artifact@v4
      with:
        name: 'inotifywait-Java ${{ matrix.java }} building ...'
        path: '/home/runner/inotifywait-log-Java ${{ matrix.java }} building ....csv'

Modified the original yaml file.
[master 0fd47181] add modified yaml file
 2 files changed, 52 insertions(+)
 create mode 100644 .github/workflows/maven.yml
 create mode 100644 .github/workflows/modified-maven.yml
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 8 threads
Compressing objects: 100% (5/5), done.
Writing objects: 100% (6/6), 1.23 KiB | 1.23 MiB/s, done.
Total 6 (delta 2), reused 1 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To github.com:ogul1/JSqlParser.git
   f5274e18..0fd47181  master -> master
Waiting until modified yaml workflow starts.
Waiting until modified yaml workflow starts.
Modified yaml workflow started.
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: queued
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: in_progress
Waiting until modified yaml workflow completes.
gh run view 10960520682 --repo ogul1/JSqlParser --json status -q '.status'
Run status of 10960520682 is: completed
Modified yaml workflow completed.
Unused directories and their responsible plugins in Java 11 building ...:
/home/runner/work/JSqlParser/JSqlParser/src/site/sphinx/_static/ Not responsible by any plugin
/home/runner/work/JSqlParser/JSqlParser/.github/workflows/ Not responsible by any plugin
/home/runner/work/JSqlParser/JSqlParser/.github/ISSUE_TEMPLATE/ Not responsible by any plugin
/home/runner/work/JSqlParser/JSqlParser/.git/hooks/ Not responsible by any plugin
/home/runner/work/JSqlParser/JSqlParser/target/site/ maven-pmd-plugin:3.21.2:pmd (pmd) @ jsqlparser
/home/runner/work/JSqlParser/JSqlParser/target/classes/rr/ Not responsible by any plugin
/home/runner/work/JSqlParser/JSqlParser/target/classes/META-INF/ maven-bundle-plugin:5.1.8:bundle (default-bundle) @ jsqlparser
/home/runner/work/JSqlParser/JSqlParser/target/surefire-reports/ maven-surefire-plugin:3.2.5:test (default-test) @ jsqlparser
-------------------------------------------------
```
