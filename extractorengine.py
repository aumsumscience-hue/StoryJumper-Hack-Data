import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse, unquote

class ExtractEngine:
    def __init__(self, output_dir="storyjumper_output"):
        self.output_dir = output_dir

    def fetch_page(self, url):
        res = requests.get(url)
        res.raise_for_status()
        return res.text

    def parse_metadata(self, html):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("meta", property="og:title")['content']
        author = soup.find("meta", attrs={"name": "author"})
        author = author['content'] if author else "Unknown"
        cover_img = soup.find("meta", property="og:image")['content']
        scripts = soup.find_all("script")
        book_data = None
        for script in scripts:
            if "window.bookData" in script.text:
                js_txt = script.text
                idx = js_txt.find('window.bookData')
                js_txt = js_txt[idx:]
                start = js_txt.find('{')
                end = js_txt.rfind('}') + 1
                book_data_json = js_txt[start:end]
                book_data = json.loads(book_data_json)
                break
        images = []
        audio_map = {}  # {page_idx: [audio_url, ...]}
        if book_data:
            for idx, pg in enumerate(book_data.get("pages", [])):
                img = pg.get('img')
                if img:
                    images.append(img)
                # Find audio in objects
                page_audios = []
                for obj in pg.get("objects", []):
                    # Common fields: audio or sound
                    audio_url = obj.get("audio") or obj.get("sound")
                    if audio_url and audio_url not in page_audios:
                        page_audios.append(audio_url)
                if page_audios:
                    audio_map[idx + 1] = page_audios  # 1-based index for pages in files
        return {
            "title": title,
            "author": author,
            "cover_img": cover_img,
            "page_images": images,
            "page_audios": audio_map,
        }

    def save_files(self, file_map, prefix, ext):
        os.makedirs(self.output_dir, exist_ok=True)
        for idx, urls in file_map.items():
            for i, url in enumerate(urls):
                # Keep filename unique: page_{idx}_{i}.{ext}
                parsed = urlparse(url)
                # Try to preserve original filename if available
                fname = os.path.basename(unquote(parsed.path))
                if not fname or not fname.split(".")[-1] in ["mp3", "wav", "m4a", ext]:
                    # Fallback to generic name
                    fname = f"{prefix}_{idx}_{i+1}.{ext}"
                outname = os.path.join(self.output_dir, fname)
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        with open(outname, "wb") as f:
                            f.write(resp.content)
                        print(f"Saved {outname}")
                except Exception as e:
                    print(f"Error downloading {url}: {e}")

    def save_images(self, image_urls):
        os.makedirs(self.output_dir, exist_ok=True)
        for idx, url in enumerate(image_urls):
            fname = os.path.join(self.output_dir, f"page_{idx+1}.jpg")
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    with open(fname, "wb") as f:
                        f.write(resp.content)
                    print(f"Saved {fname}")
            except Exception as e:
                print(f"Error downloading {url}: {e}")

    def extract_book(self, url):
        html = self.fetch_page(url)
        meta = self.parse_metadata(html)
        os.makedirs(self.output_dir, exist_ok=True)
        # Save metadata
        with open(os.path.join(self.output_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"Metadata saved in {self.output_dir}/metadata.json")
        self.save_images(meta["page_images"])
        # Save audio per page
        self.save_files(meta["page_audios"], prefix="audio", ext="mp3")
        print("Extraction complete.")
