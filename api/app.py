# ============================================================
# VIDEOLITE.COM
# LOW-RAM VIDEO CONVERTER BACKEND
# FastAPI + FFmpeg + FFprobe
#
# FEATURES
# ------------------------------------------------------------
# VIDEO + AUDIO
# 144p -> 4K OPTIONS
# NO UPSCALING
# HIGH QUALITY -> LOW QUALITY
# LIVE FFMPEG PROGRESS
# PLAYABLE MP4
# LOW CPU/RAM MODE
# VIDEO DETAILS
# ============================================================

import os
import uuid
import json
import subprocess
import threading

from pathlib import Path
from typing import Dict

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Videolite.com",
    version="5.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PROGRAMS
# ============================================================

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


# ============================================================
# JOBS
# ============================================================

jobs: Dict[str, dict] = {}

jobs_lock = threading.Lock()


# ============================================================
# SUPPORTED INPUT FORMATS
# ============================================================

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
    ".mpeg",
    ".mpg",
    ".ogv",
    ".m4v"
}


# ============================================================
# RESOLUTIONS
# ============================================================

RESOLUTIONS = {
    "144": 144,
    "240": 240,
    "360": 360,
    "480": 480,
    "720": 720,
    "1080": 1080,
    "1440": 1440,
    "2160": 2160
}


# ============================================================
# OUTPUT FORMATS
# ============================================================

FORMATS = {

    "mp4": {
        "extension": ".mp4",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "media_type": "video/mp4"
    },

    "mkv": {
        "extension": ".mkv",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "media_type": "video/x-matroska"
    },

    "webm": {
        "extension": ".webm",
        "video_codec": "libvpx-vp9",
        "audio_codec": "libopus",
        "media_type": "video/webm"
    }

}


# ============================================================
# WINDOWS
# ============================================================

def creation_flags():

    if os.name == "nt":
        return subprocess.CREATE_NO_WINDOW

    return 0


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(
    command,
    timeout=60
):

    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creation_flags(),
        timeout=timeout
    )


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():

    try:

        result = run_command(
            [
                FFMPEG,
                "-version"
            ],
            10
        )

        return result.returncode == 0

    except Exception:

        return False


# ============================================================
# CHECK FFPROBE
# ============================================================

def check_ffprobe():

    try:

        result = run_command(
            [
                FFPROBE,
                "-version"
            ],
            10
        )

        return result.returncode == 0

    except Exception:

        return False


# ============================================================
# FORMAT FILE SIZE
# ============================================================

def format_file_size(size):

    try:

        size = int(size)

    except Exception:

        size = 0

    if size >= 1024 * 1024 * 1024:

        return (
            f"{size / (1024 * 1024 * 1024):.2f} GB"
        )

    if size >= 1024 * 1024:

        return (
            f"{size / (1024 * 1024):.2f} MB"
        )

    if size >= 1024:

        return (
            f"{size / 1024:.2f} KB"
        )

    return f"{size} Bytes"


# ============================================================
# FPS
# ============================================================

def get_fps(stream):

    fps_text = stream.get(
        "r_frame_rate",
        "0/1"
    )

    try:

        parts = fps_text.split("/")

        numerator = float(
            parts[0]
        )

        denominator = float(
            parts[1]
        )

        if denominator != 0:

            return (
                numerator /
                denominator
            )

    except Exception:

        pass

    return 0


# ============================================================
# GET VIDEO DETAILS
# ============================================================

def get_video_details(
    input_file: str
):

    command = [

        FFPROBE,

        "-v",
        "error",

        "-show_entries",

        (
            "format=duration,size,"
            "format_name,bit_rate"
        ),

        "-show_entries",

        (
            "stream=index,"
            "codec_name,"
            "codec_type,"
            "width,"
            "height,"
            "r_frame_rate,"
            "bit_rate,"
            "sample_rate,"
            "channels,"
            "pix_fmt"
        ),

        "-of",
        "json",

        input_file
    ]

    try:

        result = run_command(
            command,
            60
        )

        if result.returncode != 0:

            return None

        data = json.loads(
            result.stdout
        )

        streams = data.get(
            "streams",
            []
        )

        format_data = data.get(
            "format",
            {}
        )

        video_stream = None
        audio_stream = None

        for stream in streams:

            if stream.get(
                "codec_type"
            ) == "video":

                if video_stream is None:

                    video_stream = stream

            elif stream.get(
                "codec_type"
            ) == "audio":

                if audio_stream is None:

                    audio_stream = stream

        if video_stream is None:

            return None

        # ====================================================
        # VIDEO SIZE
        # ====================================================

        width = int(
            video_stream.get(
                "width",
                0
            ) or 0
        )

        height = int(
            video_stream.get(
                "height",
                0
            ) or 0
        )

        # ====================================================
        # FPS
        # ====================================================

        fps_value = get_fps(
            video_stream
        )

        if fps_value > 0:

            fps_text = (
                f"{fps_value:.2f} FPS"
            )

        else:

            fps_text = "Unknown"

        # ====================================================
        # DURATION
        # ====================================================

        try:

            duration_seconds = float(
                format_data.get(
                    "duration",
                    0
                ) or 0
            )

        except Exception:

            duration_seconds = 0

        hours = int(
            duration_seconds // 3600
        )

        minutes = int(
            (duration_seconds % 3600) // 60
        )

        seconds = int(
            duration_seconds % 60
        )

        if hours > 0:

            duration_text = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        else:

            duration_text = (
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        # ====================================================
        # FILE SIZE
        # ====================================================

        try:

            file_size = int(
                format_data.get(
                    "size",
                    0
                ) or 0
            )

        except Exception:

            file_size = 0

        size_text = format_file_size(
            file_size
        )

        # ====================================================
        # QUALITY
        # ====================================================

        max_dimension = max(
            width,
            height
        )

        if max_dimension >= 2160:

            quality = "4K"

        elif max_dimension >= 1440:

            quality = "1440p / 2K"

        elif max_dimension >= 1080:

            quality = "1080p / Full HD"

        elif max_dimension >= 720:

            quality = "720p / HD"

        elif max_dimension >= 480:

            quality = "480p"

        elif max_dimension >= 360:

            quality = "360p"

        elif max_dimension >= 240:

            quality = "240p"

        else:

            quality = "144p"

        # ====================================================
        # ASPECT RATIO
        # ====================================================

        if width and height:

            ratio = width / height

            if abs(
                ratio - (16 / 9)
            ) < 0.05:

                aspect_ratio = "16:9"

            elif abs(
                ratio - (4 / 3)
            ) < 0.05:

                aspect_ratio = "4:3"

            elif abs(
                ratio - (9 / 16)
            ) < 0.05:

                aspect_ratio = "9:16"

            else:

                aspect_ratio = (
                    f"{width}:{height}"
                )

        else:

            aspect_ratio = "Unknown"

        # ====================================================
        # VIDEO
        # ====================================================

        video_codec = video_stream.get(
            "codec_name",
            "Unknown"
        )

        video_bitrate = video_stream.get(
            "bit_rate",
            "Unknown"
        )

        pixel_format = video_stream.get(
            "pix_fmt",
            "Unknown"
        )

        # ====================================================
        # AUDIO
        # ====================================================

        if audio_stream:

            audio_codec = audio_stream.get(
                "codec_name",
                "Unknown"
            )

            audio_bitrate = audio_stream.get(
                "bit_rate",
                "Unknown"
            )

            sample_rate = audio_stream.get(
                "sample_rate",
                "Unknown"
            )

            channel_count = int(
                audio_stream.get(
                    "channels",
                    0
                ) or 0
            )

            if channel_count == 1:

                channels = "Mono"

            elif channel_count == 2:

                channels = "Stereo"

            elif channel_count > 2:

                channels = (
                    f"{channel_count} Channels"
                )

            else:

                channels = "Unknown"

        else:

            audio_codec = "No Audio"
            audio_bitrate = "None"
            sample_rate = "None"
            channels = "No Audio"

        # ====================================================
        # RETURN
        # ====================================================

        return {

            "width": width,

            "height": height,

            "resolution": (
                f"{width} × {height}"
            ),

            "quality": quality,

            "fps": fps_text,

            "fps_value": fps_value,

            "duration": duration_text,

            "duration_seconds": duration_seconds,

            "file_size": file_size,

            "file_size_text": size_text,

            "format": format_data.get(
                "format_name",
                "Unknown"
            ),

            "video_codec": video_codec,

            "video_bitrate": video_bitrate,

            "audio_codec": audio_codec,

            "audio_bitrate": audio_bitrate,

            "sample_rate": sample_rate,

            "channels": channels,

            "aspect_ratio": aspect_ratio,

            "pixel_format": pixel_format

        }

    except Exception:

        return None


# ============================================================
# SAVE UPLOAD
# ============================================================

async def save_upload(
    upload_file: UploadFile,
    destination: Path
):

    with open(
        destination,
        "wb"
    ) as output_file:

        while True:

            chunk = await upload_file.read(
                1024 * 1024
            )

            if not chunk:

                break

            output_file.write(
                chunk
            )

    await upload_file.close()


# ============================================================
# UPDATE JOB
# ============================================================

def update_job(
    job_id: str,
    **values
):

    with jobs_lock:

        if job_id in jobs:

            jobs[job_id].update(
                values
            )


# ============================================================
# GET JOB
# ============================================================

def get_job(
    job_id: str
):

    with jobs_lock:

        job = jobs.get(
            job_id
        )

        if job is None:

            return None

        return job.copy()


# ============================================================
# CALCULATE TARGET SIZE
# ============================================================

def get_target_dimensions(
    original_width,
    original_height,
    target_height
):

    if original_width <= 0 or original_height <= 0:

        return None

    # --------------------------------------------------------
    # NEVER UPSCALE
    # --------------------------------------------------------

    if original_height <= target_height:

        return {
            "width": original_width,
            "height": original_height,
            "resize": False
        }

    # --------------------------------------------------------
    # PRESERVE ORIGINAL ASPECT RATIO
    # --------------------------------------------------------

    new_height = target_height

    new_width = round(
        original_width *
        (
            new_height /
            original_height
        )
    )

    # --------------------------------------------------------
    # EVEN DIMENSIONS
    # --------------------------------------------------------

    new_width = max(
        2,
        new_width
    )

    new_height = max(
        2,
        new_height
    )

    if new_width % 2 != 0:

        new_width -= 1

    if new_height % 2 != 0:

        new_height -= 1

    return {

        "width": new_width,

        "height": new_height,

        "resize": True

    }


# ============================================================
# CONVERT VIDEO
# ============================================================

def convert_video(

    job_id: str,

    input_path: str,

    output_path: str,

    resolution: str,

    output_format: str

):

    process = None

    stderr_lines = []

    try:

        # ====================================================
        # INPUT DETAILS
        # ====================================================

        details = get_video_details(
            input_path
        )

        if not details:

            raise RuntimeError(
                "Could not read input video."
            )

        duration = details[
            "duration_seconds"
        ]

        if duration <= 0:

            raise RuntimeError(
                "Video duration could not be read."
            )

        original_width = details[
            "width"
        ]

        original_height = details[
            "height"
        ]

        target_height = RESOLUTIONS[
            resolution
        ]

        # ====================================================
        # TARGET DIMENSIONS
        # ====================================================

        target = get_target_dimensions(

            original_width,

            original_height,

            target_height

        )

        if target is None:

            raise RuntimeError(
                "Could not calculate target resolution."
            )

        target_width = target[
            "width"
        ]

        target_height_real = target[
            "height"
        ]

        resize_required = target[
            "resize"
        ]

        # ====================================================
        # UPDATE JOB
        # ====================================================

        update_job(

            job_id,

            status="processing",

            progress=0,

            message="Starting conversion...",

            duration=duration,

            video_details=details,

            original_resolution=(
                f"{original_width}x{original_height}"
            ),

            target_resolution=(
                f"{target_width}x{target_height_real}"
            ),

            resize_required=resize_required

        )

        # ====================================================
        # CONFIG
        # ====================================================

        config = FORMATS[
            output_format
        ]

        # ====================================================
        # BUILD COMMAND
        # ====================================================

        command = [

            FFMPEG,

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            "-progress",
            "pipe:1",

            "-nostats",

            "-stats_period",
            "0.25",

            "-i",
            input_path,

            # VIDEO
            "-map",
            "0:v:0",

            # AUDIO
            "-map",
            "0:a:0?",

        ]

        # ====================================================
        # SCALE ONLY WHEN NEEDED
        # ====================================================

        if resize_required:

            scale_filter = (

                f"scale="
                f"{target_width}:"
                f"{target_height_real}:"
                f"flags=fast_bilinear"

            )

            command.extend([

                "-vf",
                scale_filter

            ])

        # ====================================================
        # VIDEO CODEC
        # ====================================================

        command.extend([

            "-c:v",
            config["video_codec"]

        ])

        # ====================================================
        # LOW RAM / CPU
        # ====================================================

        if output_format in (
            "mp4",
            "mkv"
        ):

            command.extend([

                "-preset",
                "veryfast",

                "-crf",
                "23",

                "-threads",
                "2"

            ])

        # ====================================================
        # MP4
        # ====================================================

        if output_format == "mp4":

            command.extend([

                "-pix_fmt",
                "yuv420p",

                "-profile:v",
                "main",

                "-level",
                "4.0",

                "-c:a",
                "aac",

                "-b:a",
                "128k",

                "-ar",
                "48000",

                "-ac",
                "2",

                "-movflags",
                "+faststart"

            ])

        # ====================================================
        # MKV
        # ====================================================

        elif output_format == "mkv":

            command.extend([

                "-pix_fmt",
                "yuv420p",

                "-c:a",
                "aac",

                "-b:a",
                "128k",

                "-ar",
                "48000",

                "-ac",
                "2"

            ])

        # ====================================================
        # WEBM
        # ====================================================

        elif output_format == "webm":

            command.extend([

                "-c:v",
                "libvpx-vp9",

                "-b:v",
                "0",

                "-crf",
                "32",

                "-deadline",
                "realtime",

                "-cpu-used",
                "6",

                "-threads",
                "2",

                "-c:a",
                "libopus",

                "-b:a",
                "96k"

            ])

        # ====================================================
        # OUTPUT
        # ====================================================

        command.append(
            output_path
        )

        # ====================================================
        # START FFMPEG
        # ====================================================

        process = subprocess.Popen(

            command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            bufsize=1,

            creationflags=creation_flags()

        )

        # ====================================================
        # ERROR READER
        # ====================================================

        def read_errors():

            try:

                for line in process.stderr:

                    if line:

                        stderr_lines.append(
                            line.strip()
                        )

            except Exception:

                pass

        error_thread = threading.Thread(

            target=read_errors,

            daemon=True

        )

        error_thread.start()

        # ====================================================
        # LIVE PROGRESS
        # ====================================================

        last_progress = -1

        while True:

            line = process.stdout.readline()

            if not line:

                if process.poll() is not None:

                    break

                continue

            line = line.strip()

            if "=" not in line:

                continue

            key, value = line.split(
                "=",
                1
            )

            if key == "out_time_us":

                try:

                    current_time = (
                        int(value) /
                        1_000_000
                    )

                except Exception:

                    current_time = 0

                if duration > 0:

                    progress = (

                        current_time /
                        duration

                    ) * 100

                else:

                    progress = 0

                progress = max(
                    0,
                    min(
                        99,
                        progress
                    )
                )

                progress = round(
                    progress,
                    1
                )

                if progress != last_progress:

                    last_progress = progress

                    update_job(

                        job_id,

                        status="processing",

                        progress=progress,

                        current_time=current_time,

                        message=(

                            "Converting video... "

                            f"{progress:.1f}%"

                        )

                    )

        # ====================================================
        # WAIT
        # ====================================================

        return_code = process.wait()

        error_thread.join(
            timeout=2
        )

        # ====================================================
        # FFMPEG ERROR
        # ====================================================

        if return_code != 0:

            error_text = "\n".join(
                stderr_lines
            ).strip()

            raise RuntimeError(

                error_text or
                "FFmpeg conversion failed."

            )

        # ====================================================
        # OUTPUT EXISTS
        # ====================================================

        if not os.path.exists(
            output_path
        ):

            raise RuntimeError(
                "Output video was not created."
            )

        # ====================================================
        # OUTPUT SIZE
        # ====================================================

        output_size = os.path.getsize(
            output_path
        )

        if output_size <= 0:

            raise RuntimeError(
                "Output video is empty."
            )

        # ====================================================
        # VERIFY OUTPUT
        # ====================================================

        output_details = get_video_details(
            output_path
        )

        if not output_details:

            raise RuntimeError(
                "Converted video could not be verified."
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        update_job(

            job_id,

            status="completed",

            progress=100,

            current_time=duration,

            duration=duration,

            message="Conversion completed!",

            download_url=(
                f"/download/{job_id}"
            ),

            output_size=output_size,

            output_size_text=(
                format_file_size(
                    output_size
                )
            ),

            output_details=output_details,

            error=None

        )

    except Exception as error:

        # ====================================================
        # KILL PROCESS
        # ====================================================

        if process is not None:

            try:

                if process.poll() is None:

                    process.kill()

                    process.wait(
                        timeout=5
                    )

            except Exception:

                pass

        # ====================================================
        # ERROR
        # ====================================================

        update_job(

            job_id,

            status="error",

            progress=0,

            message="Conversion failed.",

            error=str(error)

        )

    finally:

        # ====================================================
        # CLOSE STDOUT
        # ====================================================

        try:

            if process and process.stdout:

                process.stdout.close()

        except Exception:

            pass

        # ====================================================
        # CLOSE STDERR
        # ====================================================

        try:

            if process and process.stderr:

                process.stderr.close()

        except Exception:

            pass

        # ====================================================
        # DELETE INPUT
        # ====================================================

        try:

            if os.path.exists(
                input_path
            ):

                os.remove(
                    input_path
                )

        except Exception:

            pass


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "name": "Videolite.com",

        "status": "online",

        "version": "5.0.0",

        "mode": "low_ram",

        "upscaling": False

    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "ok",

        "ffmpeg": check_ffmpeg(),

        "ffprobe": check_ffprobe()

    }


# ============================================================
# CONVERT
# ============================================================

@app.post("/convert")
async def convert(

    background_tasks: BackgroundTasks,

    file: UploadFile = File(...),

    resolution: str = Form("1080"),

    format: str = Form("mp4")

):

    # ========================================================
    # FFMPEG
    # ========================================================

    if not check_ffmpeg():

        raise HTTPException(

            status_code=500,

            detail=(

                "FFmpeg was not found. "
                "Please install FFmpeg and add it to PATH."

            )

        )

    # ========================================================
    # FFPROBE
    # ========================================================

    if not check_ffprobe():

        raise HTTPException(

            status_code=500,

            detail="FFprobe was not found."

        )

    # ========================================================
    # FILE
    # ========================================================

    if not file.filename:

        raise HTTPException(

            status_code=400,

            detail="Please select a video."

        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(

            status_code=400,

            detail="Unsupported video format."

        )

    # ========================================================
    # RESOLUTION
    # ========================================================

    resolution = str(
        resolution
    )

    if resolution not in RESOLUTIONS:

        raise HTTPException(

            status_code=400,

            detail="Invalid resolution."

        )

    # ========================================================
    # FORMAT
    # ========================================================

    format = str(
        format
    ).lower()

    if format not in FORMATS:

        raise HTTPException(

            status_code=400,

            detail="Invalid output format."

        )

    # ========================================================
    # JOB ID
    # ========================================================

    job_id = uuid.uuid4().hex

    # ========================================================
    # INPUT PATH
    # ========================================================

    input_path = (

        UPLOAD_DIR /

        f"{job_id}_input{extension}"

    )

    # ========================================================
    # OUTPUT
    # ========================================================

    output_extension = FORMATS[
        format
    ]["extension"]

    output_filename = (

        f"Videolite_"
        f"{job_id}"
        f"{output_extension}"

    )

    output_path = (

        OUTPUT_DIR /
        output_filename

    )

    # ========================================================
    # CREATE JOB
    # ========================================================

    with jobs_lock:

        jobs[job_id] = {

            "job_id": job_id,

            "status": "uploading",

            "progress": 0,

            "message": "Uploading video...",

            "filename": file.filename,

            "resolution": resolution,

            "format": format,

            "output": output_filename,

            "download_url": None,

            "error": None,

            "current_time": 0,

            "duration": 0,

            "output_size": 0,

            "output_size_text": "0 Bytes",

            "video_details": None,

            "output_details": None,

            "resize_required": None,

            "original_resolution": None,

            "target_resolution": None

        }

    # ========================================================
    # SAVE FILE
    # ========================================================

    try:

        await save_upload(

            file,

            input_path

        )

    except Exception as error:

        update_job(

            job_id,

            status="error",

            message="Upload failed.",

            error=str(error)

        )

        raise HTTPException(

            status_code=500,

            detail="Could not save uploaded video."

        )

    # ========================================================
    # CHECK FILE
    # ========================================================

    if not input_path.exists():

        raise HTTPException(

            status_code=500,

            detail="Uploaded file was not found."

        )

    if input_path.stat().st_size <= 0:

        raise HTTPException(

            status_code=400,

            detail="Uploaded video is empty."

        )

    # ========================================================
    # VIDEO DETAILS
    # ========================================================

    video_details = get_video_details(

        str(input_path)

    )

    if not video_details:

        try:

            input_path.unlink()

        except Exception:

            pass

        raise HTTPException(

            status_code=400,

            detail="Could not read video information."

        )

    # ========================================================
    # NO UPSCALING CHECK
    # ========================================================

    original_height = video_details.get(
        "height",
        0
    )

    target_height = RESOLUTIONS[
        resolution
    ]

    if original_height <= target_height:

        actual_target_message = (

            "Selected quality is higher than "
            "or equal to original quality. "
            "Upscaling is disabled."

        )

    else:

        actual_target_message = (

            f"Video will be converted to "
            f"{resolution}p."

        )

    # ========================================================
    # UPDATE JOB
    # ========================================================

    update_job(

        job_id,

        status="queued",

        progress=0,

        message=actual_target_message,

        upload_size=(
            input_path.stat().st_size
        ),

        upload_size_text=(
            format_file_size(
                input_path.stat().st_size
            )
        ),

        video_details=video_details

    )

    # ========================================================
    # START CONVERSION
    # ========================================================

    background_tasks.add_task(

        convert_video,

        job_id,

        str(input_path),

        str(output_path),

        resolution,

        format

    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "job_id": job_id,

        "status": "queued",

        "progress": 0,

        "message": actual_target_message,

        "video_details": video_details,

        "upscaling": False

    }


# ============================================================
# PROGRESS
# ============================================================

@app.get("/progress/{job_id}")
def progress(
    job_id: str
):

    job = get_job(
        job_id
    )

    if job is None:

        raise HTTPException(

            status_code=404,

            detail="Conversion job not found."

        )

    return {

        "success": True,

        "job_id": job_id,

        "status": job.get(
            "status"
        ),

        "progress": job.get(
            "progress",
            0
        ),

        "message": job.get(
            "message",
            ""
        ),

        "download_url": job.get(
            "download_url"
        ),

        "error": job.get(
            "error"
        ),

        "filename": job.get(
            "filename"
        ),

        "resolution": job.get(
            "resolution"
        ),

        "format": job.get(
            "format"
        ),

        "current_time": job.get(
            "current_time",
            0
        ),

        "duration": job.get(
            "duration",
            0
        ),

        "video_details": job.get(
            "video_details"
        ),

        "output_details": job.get(
            "output_details"
        ),

        "output_size": job.get(
            "output_size",
            0
        ),

        "output_size_text": job.get(
            "output_size_text",
            "0 Bytes"
        ),

        "resize_required": job.get(
            "resize_required"
        ),

        "original_resolution": job.get(
            "original_resolution"
        ),

        "target_resolution": job.get(
            "target_resolution"
        )

    }


# ============================================================
# DOWNLOAD
# ============================================================

@app.get("/download/{job_id}")
def download(
    job_id: str
):

    job = get_job(
        job_id
    )

    if job is None:

        raise HTTPException(

            status_code=404,

            detail="Conversion job not found."

        )

    if job.get(
        "status"
    ) != "completed":

        raise HTTPException(

            status_code=400,

            detail="Conversion is not complete."

        )

    filename = job.get(
        "output"
    )

    if not filename:

        raise HTTPException(

            status_code=404,

            detail="Output file not found."

        )

    output_path = (

        OUTPUT_DIR /
        filename

    )

    if not output_path.exists():

        raise HTTPException(

            status_code=404,

            detail="Converted video does not exist."

        )

    output_format = job.get(
        "format",
        "mp4"
    )

    media_type = FORMATS.get(
        output_format,
        {}
    ).get(
        "media_type",
        "application/octet-stream"
    )

    return FileResponse(

        path=str(
            output_path
        ),

        filename=filename,

        media_type=media_type,

        headers={

            "Content-Disposition":
                f'attachment; filename="{filename}"',

            "Accept-Ranges":
                "bytes"

        }

    )


# ============================================================
# JOB INFORMATION
# ============================================================

@app.get("/job/{job_id}")
def job_info(
    job_id: str
):

    job = get_job(
        job_id
    )

    if job is None:

        raise HTTPException(

            status_code=404,

            detail="Job not found."

        )

    return {

        "success": True,

        "job": job

    }


# ============================================================
# DELETE JOB
# ============================================================

@app.delete("/job/{job_id}")
def delete_job(
    job_id: str
):

    job = get_job(
        job_id
    )

    if job is None:

        raise HTTPException(

            status_code=404,

            detail="Job not found."

        )

    filename = job.get(
        "output"
    )

    if filename:

        output_path = (

            OUTPUT_DIR /
            filename

        )

        try:

            if output_path.exists():

                output_path.unlink()

        except Exception:

            pass

    with jobs_lock:

        jobs.pop(
            job_id,
            None
        )

    return {

        "success": True,

        "message": "Job deleted."

    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()

    print("=" * 60)

    print("VIDEOLITE.COM")

    print("LOW RAM VIDEO CONVERTER")

    print("VIDEO + AUDIO + LIVE PROGRESS")

    print("NO UPSCALING")

    print("=" * 60)

    print()

    print(

        "FFmpeg:",

        "OK"
        if check_ffmpeg()
        else "NOT FOUND"

    )

    print(

        "FFprobe:",

        "OK"
        if check_ffprobe()
        else "NOT FOUND"

    )

    print()

    print("Server:")

    print(
        "http://127.0.0.1:8000"
    )

    print()

    print("API Docs:")

    print(
        "http://127.0.0.1:8000/docs"
    )

    print()

    print("=" * 60)

    print()

    uvicorn.run(

        app,

        host="127.0.0.1",

        port=8000,

        reload=False

    )
