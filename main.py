from dataclasses import dataclass
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
from playwright.sync_api import sync_playwright
from pydantic import BaseModel
from waybackpy import WaybackMachineCDXServerAPI
import glob
import os
import re
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("snapshots", exist_ok=True)
app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")

@dataclass
class Config:
    url: str
    filename: str
    start_year: int
    end_year: int
    user_agent: str = (
        "Mozilla/5.0 (compatible; SandorVlajkThesisProject/1.0; +mailto:vlajksanyi@gmail.com)"
    )
    save_folder: str = "snapshots"

class VideoRequest(BaseModel):
    url: str
    start_year: int
    end_year: int


def get_filename_from_url(url: str):
    name = url.replace("https://", "").replace("http://", "").replace("www.", "")
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return clean_name[:50]


def get_snapshots(cfg: Config):
    os.makedirs(cfg.save_folder, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        for year in range(cfg.start_year, cfg.end_year + 1):
            print(f"= {year} =")

            if year > cfg.start_year:
                time.sleep(2)

            try:
                cdx = WaybackMachineCDXServerAPI(url=cfg.url, user_agent=cfg.user_agent)
                snapshot = cdx.near(year=int(f"{year}0203"))
                snapshot_url = (
                    snapshot.archive_url[:-3]
                    if snapshot.archive_url.endswith("id_")
                    else snapshot.archive_url
                )
                filename = f"{year}_{cfg.filename}.png"
                full_path = os.path.join(cfg.save_folder, filename)
                print(f"Snapshot: {snapshot_url}")

                try:
                    page.goto(snapshot_url, timeout=30000, wait_until="domcontentloaded")
                    time.sleep(2)
                    page.screenshot(path=full_path)
                    print(f"Screenshot saved: {filename}")
                except Exception as page_err:
                    print(f"  Error: Timeout - ({page_err})")
                    
                    try:
                        page.screenshot(path=full_path)
                        print(f"  Saving partial screenshot...")
                    except Exception as e:
                        print(f"  Error saving partial screenshot: {e}")

            except Exception as e:
                print(f"Error at year {year}: {e}\n")

        browser.close()


def create_video_from_snapshots(
    input_folder: str, output_filename: str, project_name: str
):
    search_pattern = f"*_{project_name}.png"
    search_path = os.path.join(input_folder, search_pattern)
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

    print("--- Deleting saved screenshots... ---")
    for img_path in image_files:
        try:
            os.remove(img_path)
        except Exception as e:
            print(f"Failed to delete: {img_path}")
    print("--- Saved screenshots deleted ---")


def make_video(config: Config):
    print("--- Video creation started ---")

    get_snapshots(cfg=config)

    output_name = f"video_{config.start_year}_{config.end_year}.mp4"

    create_video_from_snapshots(
        input_folder=config.save_folder,
        output_filename=os.path.join("snapshots", output_name),
        project_name=config.filename
    )

    print(f"--- Video created: {output_name} ---")


@app.post("/create-video")
async def create_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    config = Config(
        url=request.url,
        filename=get_filename_from_url(request.url),
        start_year=request.start_year,
        end_year=request.end_year
    )

    background_tasks.add_task(make_video, config)

    return {
        "status": "Video creation started in background",
        "details": f"URL: {request.url} - Start year: {request.start_year} - End year: {request.end_year}"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
