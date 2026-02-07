import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/144.0.0.0 Safari/537.36"
}

with open("docs/spec/missing_spec_files.md", "r", encoding="utf-8") as f:
    for line in f:
        category, name = line.strip().split(",")
        url = f"https://wiki.ポケモン.com/wiki/{name}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTPエラーがあれば例外を発生
            html = response.text
        except requests.exceptions.RequestException as e:
            print(f"{name} HTML取得に失敗:", e)
            continue

        dst = f"docs/html/{category}/{name}.html"
        with open(dst, "w", encoding="utf-8") as f:
            f.write(html)

        print(dst)
