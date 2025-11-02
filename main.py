from dataclasses import dataclass
from playwright.async_api import async_playwright
from waybackpy import WaybackMachineCDXServerAPI
import asyncio
import requests
import os

@dataclass
class Config:
    url: str
    filename: str
    start_year: int
    end_year: int
    user_agent: str = "Mozilla/5.0 (compatible; WaybackScraper/1.0; +https://example.com)"
    save_folder: str = "snapshots"

def setup() -> Config:
    return Config(
        url = str(input('URL: ')),
        filename = str(input('Filename: ')),
        start_year = int(input('Start year: ')),
        end_year = int(input('End year: '))
    )

async def make_screenshot_playwright(url: str, filename: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch() 
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=120000)
            await page.wait_for_selector('body', state='visible', timeout=30000)
            await page.screenshot(path=os.path.join("snapshots", filename), full_page=True)
            print(f"Screenshot saved: {filename}")
        except Exception as e:
            print(f"Error saving screenshot: {filename}: {e}")
        finally:
            await browser.close()

async def get_snapshots(cfg: Config):
    os.makedirs(cfg.save_folder, exist_ok=True)
    screenshot_tasks = []
    for year in range(cfg.start_year, cfg.end_year + 1):
        print(f'=== {year} ===')
        cdx = WaybackMachineCDXServerAPI(url=cfg.url, user_agent=cfg.user_agent)
        
        try:
            snapshot = cdx.near(year=int(f'{year}0205'))
            snapshot_url = snapshot.archive_url[:-3] if snapshot.archive_url.endswith("id_") else snapshot.archive_url
            filename = f'{cfg.filename}_{year}.png'
            print(f'Snapshot: {snapshot_url}')

            task = make_screenshot_playwright(url=snapshot_url, filename=filename)
            screenshot_tasks.append(task)

        except Exception as e:
            print(f'Error at year {year}: {e}\n')

    if screenshot_tasks:
        print("\nCreating screenshots\n")
        await asyncio.gather(*screenshot_tasks)
    else:
        print("No screenshots to create")

if __name__ == '__main__':
    config = setup()
    asyncio.run(get_snapshots(cfg=config))
