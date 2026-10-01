// ============================================================
// VIDEOLITE.COM
// COMPLETE SCRIPT.JS
// VIDEO CONVERTER FRONTEND
// VIDEO + AUDIO
// LIVE PROGRESS
// DOWNLOAD
// VIDEO DETAILS
// NO UPSCALING MESSAGE
// 144p -> 4K OPTIONS
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// ELEMENTS
// ============================================================

const videoInput =
    document.getElementById("videoInput");

const uploadBox =
    document.getElementById("uploadBox");

const fileInfo =
    document.getElementById("fileInfo");

const fileName =
    document.getElementById("fileName");

const fileSize =
    document.getElementById("fileSize");

const removeFile =
    document.getElementById("removeFile");

const convertButton =
    document.getElementById("convertButton");

const progressCard =
    document.getElementById("progressCard");

const progressFill =
    document.getElementById("progressFill");

const progressPercent =
    document.getElementById("progressPercent");

const progressStatus =
    document.getElementById("progressStatus");

const progressSpinner =
    document.getElementById("progressSpinner");

const errorCard =
    document.getElementById("errorCard");

const errorText =
    document.getElementById("errorText");

const resultCard =
    document.getElementById("resultCard");

const resultText =
    document.getElementById("resultText");

const originalSize =
    document.getElementById("originalSize");

const convertedSize =
    document.getElementById("convertedSize");

const savedPercent =
    document.getElementById("savedPercent");

const downloadButton =
    document.getElementById("downloadButton");

const convertAgainButton =
    document.getElementById("convertAgainButton");

const selectedQualityText =
    document.getElementById("selectedQualityText");


// ============================================================
// VARIABLES
// ============================================================

let selectedFile = null;

let currentJobId = null;

let progressTimer = null;

let displayedProgress = 0;

let progressRequestRunning = false;


// ============================================================
// NEW: ORIGINAL VIDEO DETAILS
// ============================================================

let originalVideoHeight = 0;

let originalVideoWidth = 0;


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        hideAllCards();

        setupQualitySelection();

        setupFileInput();

        setupDragDrop();

        setupButtons();

        updateSelectedQuality();

        checkBackend();

    }
);


// ============================================================
// HIDE ALL CARDS
// ============================================================

function hideAllCards() {

    if (fileInfo) {

        fileInfo.style.display =
            "none";

    }

    if (progressCard) {

        progressCard.style.display =
            "none";

    }

    if (errorCard) {

        errorCard.style.display =
            "none";

    }

    if (resultCard) {

        resultCard.style.display =
            "none";

    }

}


// ============================================================
// FILE INPUT
// ============================================================

function setupFileInput() {

    if (!videoInput) {
        return;
    }

    videoInput.addEventListener(
        "change",
        function () {

            if (
                !this.files ||
                this.files.length === 0
            ) {

                return;

            }

            selectVideo(
                this.files[0]
            );

        }
    );

}


// ============================================================
// SELECT VIDEO
// ============================================================

function selectVideo(file) {

    if (!file) {
        return;
    }


    const allowedExtensions = [

        ".mp4",
        ".mkv",
        ".mov",
        ".avi",
        ".webm",
        ".mpeg",
        ".mpg",
        ".ogv",
        ".m4v"

    ];


    const filename =
        file.name.toLowerCase();


    const valid =
        allowedExtensions.some(
            function (extension) {

                return filename.endsWith(
                    extension
                );

            }
        );


    if (!valid) {

        showError(
            "Unsupported video format. Please select MP4, MKV, MOV, AVI, WEBM, MPEG or M4V."
        );

        return;

    }


    selectedFile = file;

    currentJobId = null;


    originalVideoHeight = 0;

    originalVideoWidth = 0;


    stopProgressChecking();


    clearError();


    hideCard(
        progressCard
    );

    hideCard(
        resultCard
    );


    // --------------------------------------------------------
    // FILE NAME
    // --------------------------------------------------------

    if (fileName) {

        fileName.textContent =
            file.name;

    }


    // --------------------------------------------------------
    // FILE SIZE
    // --------------------------------------------------------

    if (fileSize) {

        fileSize.textContent =
            formatBytes(
                file.size
            );

    }


    // --------------------------------------------------------
    // SHOW FILE
    // --------------------------------------------------------

    if (fileInfo) {

        fileInfo.style.display =
            "block";

    }


    // --------------------------------------------------------
    // ENABLE BUTTON
    // --------------------------------------------------------

    if (convertButton) {

        convertButton.disabled =
            false;

        convertButton.innerHTML =
            "🚀 Convert Video";

    }


    updateSelectedQuality();


    // --------------------------------------------------------
    // GET LOCAL VIDEO DIMENSIONS
    // --------------------------------------------------------

    readLocalVideoDimensions(
        file
    );


    // --------------------------------------------------------
    // SCROLL
    // --------------------------------------------------------

    if (fileInfo) {

        fileInfo.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });

    }

}


// ============================================================
// READ LOCAL VIDEO DIMENSIONS
// ============================================================

function readLocalVideoDimensions(file) {

    try {

        const video =
            document.createElement("video");

        const objectUrl =
            URL.createObjectURL(file);

        video.preload =
            "metadata";

        video.onloadedmetadata =
            function () {

                originalVideoWidth =
                    video.videoWidth || 0;

                originalVideoHeight =
                    video.videoHeight || 0;


                URL.revokeObjectURL(
                    objectUrl
                );


                updateSelectedQuality();

            };


        video.onerror =
            function () {

                URL.revokeObjectURL(
                    objectUrl
                );

            };


        video.src =
            objectUrl;

    } catch (error) {

        console.warn(
            "Could not read local video dimensions:",
            error
        );

    }

}


// ============================================================
// DRAG & DROP
// ============================================================

function setupDragDrop() {

    if (!uploadBox) {
        return;
    }


    uploadBox.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadBox.classList.add(
                "dragging"
            );

        }
    );


    uploadBox.addEventListener(
        "dragleave",
        function () {

            uploadBox.classList.remove(
                "dragging"
            );

        }
    );


    uploadBox.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadBox.classList.remove(
                "dragging"
            );


            const files =
                event.dataTransfer.files;


            if (
                !files ||
                files.length === 0
            ) {

                return;

            }


            selectVideo(
                files[0]
            );

        }
    );

}


// ============================================================
// BUTTONS
// ============================================================

function setupButtons() {

    // --------------------------------------------------------
    // CONVERT
    // --------------------------------------------------------

    if (convertButton) {

        convertButton.addEventListener(
            "click",
            startConversion
        );

    }


    // --------------------------------------------------------
    // REMOVE
    // --------------------------------------------------------

    if (removeFile) {

        removeFile.addEventListener(
            "click",
            resetConverter
        );

    }


    // --------------------------------------------------------
    // CONVERT AGAIN
    // --------------------------------------------------------

    if (convertAgainButton) {

        convertAgainButton.addEventListener(
            "click",
            function () {

                resetConverter();

                if (uploadBox) {

                    uploadBox.scrollIntoView({
                        behavior: "smooth",
                        block: "center"
                    });

                }

            }
        );

    }

}


// ============================================================
// QUALITY SELECTION
// ============================================================

function setupQualitySelection() {

    const inputs =
        document.querySelectorAll(
            'input[name="quality"]'
        );


    inputs.forEach(
        function (input) {

            input.addEventListener(
                "change",
                updateSelectedQuality
            );

        }
    );

}


// ============================================================
// UPDATE QUALITY TEXT
// ============================================================

function updateSelectedQuality() {

    if (!selectedQualityText) {
        return;
    }


    const quality =
        getSelectedQuality();


    const qualityName =
        getQualityName(
            quality
        );


    // --------------------------------------------------------
    // NORMAL QUALITY TEXT
    // --------------------------------------------------------

    selectedQualityText.textContent =
        qualityName;


    // --------------------------------------------------------
    // NEW NO UPSCALING MESSAGE
    // --------------------------------------------------------

    showUpscalingMessage();

}


// ============================================================
// NEW: SHOW UPSCALING MESSAGE
// ============================================================

function showUpscalingMessage() {

    if (!selectedFile) {
        return;
    }


    if (!originalVideoHeight) {
        return;
    }


    const selectedQuality =
        Number(
            getSelectedQuality()
        );


    if (
        !Number.isFinite(
            selectedQuality
        )
    ) {

        return;

    }


    // --------------------------------------------------------
    // SELECTED QUALITY HIGHER THAN ORIGINAL
    // --------------------------------------------------------

    if (
        selectedQuality >
        originalVideoHeight
    ) {

        const selectedName =
            getQualityName(
                String(
                    selectedQuality
                )
            );


        const originalName =
            getOriginalQualityName(
                originalVideoHeight
            );


        if (selectedQualityText) {

            selectedQualityText.textContent =
                `${selectedName} — Upscaling Disabled`;

        }


        console.log(
            `ℹ️ Original video: ${originalName}. ` +
            `Selected: ${selectedName}. ` +
            `Upscaling is disabled.`
        );

    }

}


// ============================================================
// QUALITY NAME
// ============================================================

function getQualityName(
    value
) {

    const names = {

        "2160": "4K",

        "1440": "2K",

        "1080": "1080p",

        "720": "720p",

        "480": "480p",

        "360": "360p",

        "240": "240p",

        "144": "144p"

    };


    return (
        names[value] ||
        "1080p"
    );

}


// ============================================================
// ORIGINAL QUALITY NAME
// ============================================================

function getOriginalQualityName(
    height
) {

    if (height >= 2160) {

        return "4K";

    }

    if (height >= 1440) {

        return "2K / 1440p";

    }

    if (height >= 1080) {

        return "1080p";

    }

    if (height >= 720) {

        return "720p";

    }

    if (height >= 480) {

        return "480p";

    }

    if (height >= 360) {

        return "360p";

    }

    if (height >= 240) {

        return "240p";

    }

    return "144p";

}


// ============================================================
// GET QUALITY
// ============================================================

function getSelectedQuality() {

    const selected =
        document.querySelector(
            'input[name="quality"]:checked'
        );


    if (!selected) {

        return "1080";

    }


    return selected.value;

}


// ============================================================
// START CONVERSION
// ============================================================

async function startConversion() {

    if (!selectedFile) {

        showError(
            "Please select a video first."
        );

        return;

    }


    const quality =
        getSelectedQuality();


    console.log(
        "Starting conversion:",
        quality
    );


    // --------------------------------------------------------
    // RESET
    // --------------------------------------------------------

    clearError();

    hideCard(
        resultCard
    );


    displayedProgress = 0;

    progressRequestRunning = false;


    if (progressCard) {

        progressCard.style.display =
            "block";

    }


    if (convertButton) {

        convertButton.disabled =
            true;

        convertButton.innerHTML =
            "⏳ Uploading...";

    }


    // --------------------------------------------------------
    // NEW NO UPSCALING STATUS
    // --------------------------------------------------------

    let initialMessage =
        "Uploading video...";


    if (
        originalVideoHeight &&
        Number(quality) >
        originalVideoHeight
    ) {

        initialMessage =
            "Uploading... Upscaling is disabled.";

    }


    setProgress(
        0,
        initialMessage
    );


    // --------------------------------------------------------
    // FORM DATA
    // --------------------------------------------------------

    const formData =
        new FormData();


    formData.append(
        "file",
        selectedFile
    );


    formData.append(
        "resolution",
        quality
    );


    formData.append(
        "format",
        "mp4"
    );


    try {

        // ----------------------------------------------------
        // UPLOAD
        // ----------------------------------------------------

        const response =
            await fetch(
                `${API_URL}/convert`,
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            let message =
                "Video upload failed.";


            try {

                const errorData =
                    await response.json();


                if (
                    errorData.detail
                ) {

                    message =
                        errorData.detail;

                }

            } catch (
                parseError
            ) {

                console.warn(
                    parseError
                );

            }


            throw new Error(
                message
            );

        }


        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        if (!data.job_id) {

            throw new Error(
                "Backend did not return a conversion job ID."
            );

        }


        currentJobId =
            data.job_id;


        setProgress(
            1,
            data.message ||
            "Video uploaded. Analyzing video..."
        );


        if (convertButton) {

            convertButton.innerHTML =
                "⚙️ Converting...";

        }


        // ----------------------------------------------------
        // START POLLING
        // ----------------------------------------------------

        startProgressChecking();


    } catch (error) {

        console.error(
            "Start conversion error:",
            error
        );


        stopProgressChecking();


        showError(
            error.message ||
            "Could not start conversion."
        );


        enableConvertButton();

    }

}


// ============================================================
// START PROGRESS CHECK
// ============================================================

function startProgressChecking() {

    stopProgressChecking();


    progressTimer =
        setInterval(
            checkProgress,
            500
        );


    checkProgress();

}


// ============================================================
// STOP PROGRESS CHECK
// ============================================================

function stopProgressChecking() {

    if (progressTimer) {

        clearInterval(
            progressTimer
        );

        progressTimer = null;

    }

}


// ============================================================
// CHECK PROGRESS
// ============================================================

async function checkProgress() {

    if (!currentJobId) {
        return;
    }


    if (progressRequestRunning) {
        return;
    }


    progressRequestRunning = true;


    try {

        const response =
            await fetch(
                `${API_URL}/progress/${currentJobId}`,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Could not read conversion progress."
            );

        }


        const data =
            await response.json();


        console.log(
            "Progress:",
            data
        );


        const backendProgress =
            Number(
                data.progress || 0
            );


        // ====================================================
        // QUEUED
        // ====================================================

        if (
            data.status === "queued"
        ) {

            setProgress(
                Math.max(
                    1,
                    backendProgress
                ),
                data.message ||
                "Preparing video..."
            );

        }


        // ====================================================
        // UPLOADING
        // ====================================================

        else if (
            data.status === "uploading"
        ) {

            setProgress(
                Math.max(
                    1,
                    backendProgress
                ),
                data.message ||
                "Uploading video..."
            );

        }


        // ====================================================
        // PROCESSING
        // ====================================================

        else if (
            data.status === "processing"
        ) {

            updateConversionProgress(
                backendProgress,
                data
            );

        }


        // ====================================================
        // COMPLETED
        // ====================================================

        else if (
            data.status === "completed"
        ) {

            setProgress(
                100,
                "✅ Conversion completed!"
            );


            stopProgressChecking();


            await showResult(
                data
            );


            return;

        }


        // ====================================================
        // ERROR
        // ====================================================

        else if (
            data.status === "error"
        ) {

            stopProgressChecking();


            throw new Error(
                data.error ||
                data.message ||
                "FFmpeg conversion failed."
            );

        }

    } catch (error) {

        console.error(
            "Progress error:",
            error
        );


        if (
            error.message ===
            "Failed to fetch"
        ) {

            console.warn(
                "Backend connection temporarily unavailable."
            );

        } else {

            stopProgressChecking();

            showError(
                error.message ||
                "Conversion failed."
            );

            enableConvertButton();

        }

    } finally {

        progressRequestRunning =
            false;

    }

}


// ============================================================
// UPDATE CONVERSION PROGRESS
// ============================================================

function updateConversionProgress(
    backendProgress,
    data
) {

    let target =
        Number(
            backendProgress
        );


    if (
        !Number.isFinite(target)
    ) {

        target = 1;

    }


    // --------------------------------------------------------
    // NEVER GO BACKWARDS
    // --------------------------------------------------------

    if (
        target <
        displayedProgress
    ) {

        target =
            displayedProgress;

    }


    // --------------------------------------------------------
    // MINIMUM 1%
    // --------------------------------------------------------

    if (
        target < 1
    ) {

        target = 1;

    }


    displayedProgress =
        target;


    let message =
        data.message ||
        "Converting video with FFmpeg...";


    // --------------------------------------------------------
    // CURRENT TIME
    // --------------------------------------------------------

    if (
        data.current_time !== undefined &&
        data.duration
    ) {

        const current =
            formatTime(
                data.current_time
            );

        const total =
            formatTime(
                data.duration
            );


        message =
            `Converting video... ${current} / ${total}`;

    }


    setProgress(
        target,
        message
    );

}


// ============================================================
// SET PROGRESS
// ============================================================

function setProgress(
    percent,
    message
) {

    percent =
        Number(
            percent
        );


    if (
        !Number.isFinite(percent)
    ) {

        percent = 0;

    }


    percent =
        Math.max(
            0,
            Math.min(
                100,
                percent
            )
        );


    // --------------------------------------------------------
    // Progress bar
    // --------------------------------------------------------

    if (progressFill) {

        progressFill.style.width =
            `${percent}%`;

    }


    // --------------------------------------------------------
    // Number
    // --------------------------------------------------------

    if (progressPercent) {

        progressPercent.textContent =
            `${Math.round(percent)}%`;

    }


    // --------------------------------------------------------
    // Status
    // --------------------------------------------------------

    if (
        progressStatus &&
        message
    ) {

        progressStatus.textContent =
            message;

    }


    // --------------------------------------------------------
    // Spinner
    // --------------------------------------------------------

    if (progressSpinner) {

        if (
            percent >= 100
        ) {

            progressSpinner.textContent =
                "✅";

        } else {

            progressSpinner.textContent =
                "⚙️";

        }

    }

}


// ============================================================
// SHOW RESULT
// ============================================================

async function showResult(
    data
) {

    console.log(
        "Conversion completed:",
        data
    );


    // --------------------------------------------------------
    // SHOW RESULT CARD
    // --------------------------------------------------------

    if (resultCard) {

        resultCard.style.display =
            "block";

    }


    // --------------------------------------------------------
    // HIDE PROGRESS
    // --------------------------------------------------------

    if (progressCard) {

        progressCard.style.display =
            "none";

    }


    // --------------------------------------------------------
    // DOWNLOAD URL
    // --------------------------------------------------------

    let downloadUrl =
        data.download_url;


    if (!downloadUrl) {

        downloadUrl =
            `/download/${currentJobId}`;

    }


    if (
        downloadUrl.startsWith("/")
    ) {

        downloadUrl =
            API_URL +
            downloadUrl;

    }


    console.log(
        "Download URL:",
        downloadUrl
    );


    // --------------------------------------------------------
    // DOWNLOAD BUTTON
    // --------------------------------------------------------

    if (downloadButton) {

        downloadButton.href =
            downloadUrl;

        downloadButton.target =
            "_blank";

        downloadButton.rel =
            "noopener";

        downloadButton.removeAttribute(
            "disabled"
        );


        downloadButton.style.display =
            "inline-flex";


        downloadButton.textContent =
            "⬇️ Download Converted Video";

    }


    // --------------------------------------------------------
    // ORIGINAL SIZE
    // --------------------------------------------------------

    if (originalSize) {

        originalSize.textContent =
            formatBytes(
                selectedFile
                    ? selectedFile.size
                    : 0
            );

    }


    // --------------------------------------------------------
    // OUTPUT DETAILS
    // --------------------------------------------------------

    const outputDetails =
        data.output_details;


    if (
        outputDetails &&
        resultText
    ) {

        const resolution =
            outputDetails.resolution ||
            "Unknown";

        const quality =
            outputDetails.quality ||
            getQualityName(
                getSelectedQuality()
            );

        const audio =
            outputDetails.audio_codec ||
            "Unknown";


        resultText.textContent =
            `✅ ${quality} video ready — ${resolution} — Audio: ${audio}`;

    } else if (resultText) {

        resultText.textContent =
            "✅ Your converted video is ready to download.";

    }


    // --------------------------------------------------------
    // OUTPUT SIZE
    // --------------------------------------------------------

    let outputBytes =
        Number(
            data.output_size || 0
        );


    // --------------------------------------------------------
    // HEAD REQUEST
    // --------------------------------------------------------

    if (
        outputBytes <= 0
    ) {

        try {

            const headResponse =
                await fetch(
                    downloadUrl,
                    {
                        method: "HEAD",
                        cache: "no-store"
                    }
                );


            if (
                headResponse.ok
            ) {

                const length =
                    headResponse.headers.get(
                        "content-length"
                    );


                if (length) {

                    outputBytes =
                        Number(
                            length
                        );

                }

            }

        } catch (error) {

            console.warn(
                "Could not read output file size:",
                error
            );

        }

    }


    // --------------------------------------------------------
    // DISPLAY OUTPUT SIZE
    // --------------------------------------------------------

    if (convertedSize) {

        if (
            outputBytes > 0
        ) {

            convertedSize.textContent =
                formatBytes(
                    outputBytes
                );

        } else {

            convertedSize.textContent =
                "Ready";

        }

    }


    // --------------------------------------------------------
    // SAVED PERCENT
    // --------------------------------------------------------

    if (
        savedPercent &&
        selectedFile &&
        selectedFile.size > 0 &&
        outputBytes > 0
    ) {

        const saved =
            (
                1 -
                (
                    outputBytes /
                    selectedFile.size
                )
            ) * 100;


        savedPercent.textContent =
            `${saved.toFixed(1)}%`;

    }


    // --------------------------------------------------------
    // ENABLE CONVERT BUTTON
    // --------------------------------------------------------

    enableConvertButton();


    // --------------------------------------------------------
    // SCROLL TO RESULT
    // --------------------------------------------------------

    if (resultCard) {

        resultCard.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

    }

}


// ============================================================
// ENABLE CONVERT BUTTON
// ============================================================

function enableConvertButton() {

    if (!convertButton) {
        return;
    }


    convertButton.disabled =
        false;

    convertButton.innerHTML =
        "🚀 Convert Video";

}


// ============================================================
// RESET CONVERTER
// ============================================================

function resetConverter() {

    stopProgressChecking();


    selectedFile = null;

    currentJobId = null;

    displayedProgress = 0;

    progressRequestRunning = false;


    originalVideoHeight = 0;

    originalVideoWidth = 0;


    if (videoInput) {

        videoInput.value =
            "";

    }


    if (fileInfo) {

        fileInfo.style.display =
            "none";

    }


    if (progressCard) {

        progressCard.style.display =
            "none";

    }


    if (errorCard) {

        errorCard.style.display =
            "none";

    }


    if (resultCard) {

        resultCard.style.display =
            "none";

    }


    if (convertButton) {

        convertButton.disabled =
            true;

        convertButton.innerHTML =
            "🚀 Convert Video";

    }


    if (fileName) {

        fileName.textContent =
            "Video.mp4";

    }


    if (fileSize) {

        fileSize.textContent =
            "0 MB";

    }


    if (originalSize) {

        originalSize.textContent =
            "0 MB";

    }


    if (convertedSize) {

        convertedSize.textContent =
            "0 MB";

    }


    if (savedPercent) {

        savedPercent.textContent =
            "0%";

    }


    if (downloadButton) {

        downloadButton.removeAttribute(
            "href"
        );

    }


    setProgress(
        0,
        "Preparing video..."
    );


    clearError();

}


// ============================================================
// ERROR
// ============================================================

function showError(
    message
) {

    stopProgressChecking();


    if (progressCard) {

        progressCard.style.display =
            "none";

    }


    if (resultCard) {

        resultCard.style.display =
            "none";

    }


    if (errorCard) {

        errorCard.style.display =
            "flex";

    }


    if (errorText) {

        errorText.textContent =
            message;

    }


    if (errorCard) {

        errorCard.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

    }

}


// ============================================================
// CLEAR ERROR
// ============================================================

function clearError() {

    if (errorCard) {

        errorCard.style.display =
            "none";

    }


    if (errorText) {

        errorText.textContent =
            "";

    }

}


// ============================================================
// HIDE CARD
// ============================================================

function hideCard(
    element
) {

    if (element) {

        element.style.display =
            "none";

    }

}


// ============================================================
// FORMAT BYTES
// ============================================================

function formatBytes(
    bytes
) {

    bytes =
        Number(
            bytes
        );


    if (
        !Number.isFinite(bytes) ||
        bytes <= 0
    ) {

        return "0 MB";

    }


    const units = [

        "Bytes",
        "KB",
        "MB",
        "GB",
        "TB"

    ];


    let index = 0;

    let value =
        bytes;


    while (
        value >= 1024 &&
        index <
        units.length - 1
    ) {

        value /=
            1024;

        index++;

    }


    if (index === 0) {

        return (
            `${Math.round(value)} ${units[index]}`
        );

    }


    return (
        `${value.toFixed(2)} ${units[index]}`
    );

}


// ============================================================
// FORMAT TIME
// ============================================================

function formatTime(
    seconds
) {

    seconds =
        Number(
            seconds
        );


    if (
        !Number.isFinite(seconds) ||
        seconds < 0
    ) {

        return "00:00";

    }


    const hours =
        Math.floor(
            seconds / 3600
        );


    const minutes =
        Math.floor(
            (
                seconds % 3600
            ) / 60
        );


    const secs =
        Math.floor(
            seconds % 60
        );


    if (hours > 0) {

        return (
            `${String(hours).padStart(2, "0")}:` +
            `${String(minutes).padStart(2, "0")}:` +
            `${String(secs).padStart(2, "0")}`
        );

    }


    return (
        `${String(minutes).padStart(2, "0")}:` +
        `${String(secs).padStart(2, "0")}`
    );

}


// ============================================================
// BACKEND CHECK
// ============================================================

async function checkBackend() {

    try {

        const response =
            await fetch(
                `${API_URL}/health`,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Backend is not responding."
            );

        }


        const data =
            await response.json();


        console.log(
            "✅ Videolite Backend:",
            data
        );


        if (
            !data.ffmpeg
        ) {

            console.warn(
                "⚠️ FFmpeg was not detected."
            );

        }


        if (
            !data.ffprobe
        ) {

            console.warn(
                "⚠️ FFprobe was not detected."
            );

        }

    } catch (error) {

        console.warn(
            "⚠️ Videolite backend is not running.",
            error
        );

    }

}


// ============================================================
// PAGE CLOSE
// ============================================================

window.addEventListener(
    "beforeunload",
    function () {

        stopProgressChecking();

    }
);


// ============================================================
// GLOBAL API
// ============================================================

window.Videolite = {

    startConversion:
        startConversion,

    resetConverter:
        resetConverter,

    checkBackend:
        checkBackend

};


// ============================================================
// READY
// ============================================================

console.log(
    "🎬 Videolite.com script.js loaded."
);

console.log(
    "🚫 Upscaling disabled."
);