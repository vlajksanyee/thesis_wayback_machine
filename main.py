from dataclasses import dataclass
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
from playwright.async_api import async_playwright
from waybackpy import WaybackMachineCDXServerAPI
import asyncio
import glob
import os


@dataclass
class Config:
    url: str
    filename: str
    start_year: int
    end_year: int
    user_agent: str = (
        "Mozilla/5.0 (compatible; WaybackScraper/1.0; +https://example.com)"
    )
    save_folder: str = "snapshots"


def setup() -> Config:
    return Config(
        url=str(input("URL: ")),
        filename=str(input("Filename: ")),
        start_year=int(input("Start year: ")),
        end_year=int(input("End year: ")),
    )


async def make_screenshot_playwright(url: str, filename: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        try:
            await page.goto(url, timeout=120000)
            await page.wait_for_selector("body", state="visible", timeout=30000)
            await page.screenshot(
                path=os.path.join("snapshots", filename)
            )
            print(f"Screenshot saved: {filename}")
        except Exception as e:
            print(f"Error saving screenshot: {filename}: {e}")
        finally:
            await browser.close()


async def get_snapshots(cfg: Config):
    os.makedirs(cfg.save_folder, exist_ok=True)
    screenshot_tasks = []
    for year in range(cfg.start_year, cfg.end_year + 1):
        print(f"=== {year} ===")
        cdx = WaybackMachineCDXServerAPI(url=cfg.url, user_agent=cfg.user_agent)

        try:
            snapshot = cdx.near(year=int(f"{year}0203"))
            snapshot_url = (
                snapshot.archive_url[:-3]
                if snapshot.archive_url.endswith("id_")
                else snapshot.archive_url
            )
            filename = f"{year}_{cfg.filename}.png"
            print(f"Snapshot: {snapshot_url}")

            task = make_screenshot_playwright(url=snapshot_url, filename=filename)
            screenshot_tasks.append(task)

        except Exception as e:
            print(f"Error at year {year}: {e}\n")

    if screenshot_tasks:
        print("\nCreating screenshots")
        await asyncio.gather(*screenshot_tasks)
    else:
        print("ERROR: No screenshots to create")


def create_video_from_snapshots(
    input_folder: str, output_filename: str = "web_history.mp4"
):

    search_path = os.path.join(input_folder, "*.png")
    image_files = sorted(glob.glob(search_path))

    if not image_files:
        print("ERROR: No screenshots found")
        return

    print(f"\nCreating video")

    clips = []
    for filename in image_files:
        year = os.path.basename(filename).split("_")[0]

        base_clip = ImageClip(filename, duration=3)

        text = TextClip(
            text=f"{year}\n",
            font_size=40,
            color="white",
            stroke_color="black",
            stroke_width=2,
        )

        text = text.with_duration(3)
        text = text.with_position(("center", 980))

        final = CompositeVideoClip([base_clip, text])
        clips.append(final)

    final_clip = concatenate_videoclips(clips, method="compose")

    final_clip.write_videofile(
        output_filename,
        fps=24,
        codec="mpeg4",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )

    print(f"Created video: {output_filename}")


if __name__ == "__main__":
    config = setup()

    asyncio.run(get_snapshots(cfg=config))

    create_video_from_snapshots(
        input_folder=config.save_folder,
        output_filename=f"history_{config.start_year}_to_{config.end_year}.mp4",
    )
