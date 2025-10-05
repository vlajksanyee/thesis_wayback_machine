from dataclasses import dataclass
from waybackpy import WaybackMachineCDXServerAPI
import requests
import os

@dataclass
class Config:
    url: str
    start_year: int
    end_year: int
    user_agent: str = "Mozilla/5.0 (compatible; WaybackScraper/1.0; +https://example.com)"
    save_folder: str = "snapshots"

def setup() -> Config:
    return Config(
        url = str(input('URL: ')),
        start_year = int(input('Start year: ')),
        end_year = int(input('End year: '))
    )   

def get_snapshots(cfg: Config):
    os.makedirs(cfg.save_folder, exist_ok=True)
    for year in range(cfg.start_year, cfg.end_year + 1):
        print(f'=== {year} ===')
        cdx = WaybackMachineCDXServerAPI(url=cfg.url, user_agent=cfg.user_agent)
        
        try:
            snapshot = cdx.near(year=int(f'{year}0101'))
            snapshot_url = snapshot.archive_url
            print(f'Snapshot: {snapshot_url}')

            response = requests.get(snapshot_url)
            snapshot_id = snapshot_url.split("/web/")[1].split("/")[0]
            
            # Insert base tag to make the browser load images from Wayback Machine
            html_content = response.text.replace(
                "<head>",
                f'<head><base href="https://web.archive.org/web/{snapshot_id}/">'
            )

            filename = os.path.join(cfg.save_folder, f'{year}.html')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f'Saved: {filename}\n')

        except Exception as e:
            print(f'Error at year {year}: {e}\n')

if __name__ == '__main__':
    config = setup()
    get_snapshots(cfg=config)
