import csv

import requests

def main():
    update_list()

def update_list():
    r = requests.get("https://latinwordnet.exeter.ac.uk/api/index/v").json()
    count = int(r["count"])
    r = requests.get(f"https://latinwordnet.exeter.ac.uk/api/index/v/?limit={count}").json()

    with open("uri.csv", "w") as file:
        writer = csv.DictWriter(file, fieldnames=["lemma", "uri"])
        writer.writeheader()
        for word in range(count):
            writer.writerow({"lemma": r["results"][word]["lemma"], "uri": r["results"][word]["uri"]})

if __name__ == "__main__":
    main()
