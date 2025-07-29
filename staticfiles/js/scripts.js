const startCameraBtn = document.getElementById("startCameraBtn")
const video = document.getElementById("video")
const captureBtn = document.getElementById("captureBtn")
const canvas = document.getElementById("canvas")
const cameraForm = document.getElementById("cameraForm")
const capturedPhotoInput = document.getElementById("capturedPhoto")
const uploadForm = document.getElementById("uploadForm")
const fileInput = document.getElementById("fileInput")
const photoPreview = document.getElementById("photoPreview")
const loadingSection = document.getElementById("loadingSection")
const ajaxResults = document.getElementById("ajaxResults")
let stream

// File input preview
fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      photoPreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`
      photoPreview.style.display = "block"
    }
    reader.readAsDataURL(file)
  }
})

// AJAX form submission
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault()
  const formData = new FormData(uploadForm)
  showLoading()
  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
    const data = await response.json()
    hideLoading()
    if (data.error) {
      alert("Error: " + data.error)
      return
    }
    showResults(data)
  } catch (err) {
    hideLoading()
    alert("Something went wrong: " + err.message)
  }
})

function showLoading() {
  loadingSection.style.display = "block"
  document.querySelector(".upload-section").style.display = "none"
  document.querySelector(".camera-section").style.display = "none"
  document.querySelector(".divider").style.display = "none"
}

function hideLoading() {
  loadingSection.style.display = "none"
}

function createProbBars(containerId, labels, probs, colors) {
  const container = document.getElementById(containerId)
  container.innerHTML = ""
  probs.forEach((p, i) => {
    const barWrapper = document.createElement("div")
    barWrapper.classList.add("prob-bar-wrapper")

    const barInfo = document.createElement("div")
    barInfo.classList.add("prob-bar-info")

    const label = document.createElement("span")
    label.classList.add("prob-bar-label")
    label.textContent = labels[i]

    const value = document.createElement("span")
    value.classList.add("prob-bar-value")
    value.textContent = (p * 100).toFixed(1) + "%"

    barInfo.appendChild(label)
    barInfo.appendChild(value)

    const barContainer = document.createElement("div")
    barContainer.classList.add("prob-bar")

    const fill = document.createElement("div")
    fill.classList.add("prob-bar-fill")
    fill.style.width = p * 100 + "%"
    fill.style.backgroundColor = colors[i] || colors[0]

    barContainer.appendChild(fill)
    barWrapper.appendChild(barInfo)
    barWrapper.appendChild(barContainer)
    container.appendChild(barWrapper)
  })
}

// Segmentation tab functionality
function initializeSegmentationTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn")
  const containers = {
    original: document.getElementById("originalContainer"),
    segmented: document.getElementById("segmentedContainer"),
    overlay: document.getElementById("overlayContainer"),
  }

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetTab = button.dataset.tab

      // Update active tab
      tabButtons.forEach((btn) => btn.classList.remove("active"))
      button.classList.add("active")

      // Show/hide containers
      Object.keys(containers).forEach((key) => {
        if (key === targetTab) {
          containers[key].style.display = "block"
        } else {
          containers[key].style.display = "none"
        }
      })
    })
  })
}

function showResults(data) {
  // Display skin type
  document.getElementById("skinType").textContent = data.skin_type || data.predicted_type || "Unknown"

  // Display eye colors
  document.getElementById("leftEyeColor").textContent = data.left_eye_color ? `Left Eye: ${data.left_eye_color}` : ""
  document.getElementById("rightEyeColor").textContent = data.right_eye_color
    ? `Right Eye: ${data.right_eye_color}`
    : ""

  // Display acne level and confidence with styling
  const acneLevelElement = document.getElementById("acneLevel")
  const acneConfidenceElement = document.getElementById("acneConfidence")

  acneLevelElement.textContent = data.acne_pred || "Unknown"

  if (data.acne_confidence) {
    const confidencePercent = data.acne_confidence * 100
    acneConfidenceElement.textContent = `Confidence: ${confidencePercent.toFixed(1)}%`

    // Add confidence level styling
    acneConfidenceElement.classList.remove("high-confidence", "medium-confidence", "low-confidence")
    if (confidencePercent >= 80) {
      acneConfidenceElement.classList.add("high-confidence")
    } else if (confidencePercent >= 60) {
      acneConfidenceElement.classList.add("medium-confidence")
    } else {
      acneConfidenceElement.classList.add("low-confidence")
    }
  } else {
    acneConfidenceElement.textContent = ""
  }

  // Show cropped face if available
  if (data.cropped_face) {
    const croppedFaceSection = document.getElementById("croppedFaceSection")
    const croppedFaceImage = document.getElementById("croppedFaceImage")
    croppedFaceImage.src = data.cropped_face
    croppedFaceSection.style.display = "block"

    // Show segmentation if available
    if (data.segmentation_overlay) {
      const segmentationSection = document.getElementById("segmentationSection")

      // Set up images for all tabs
      document.getElementById("originalImage").src = data.cropped_face
      document.getElementById("segmentedImage").src = data.segmentation_overlay
      document.getElementById("overlayOriginal").src = data.cropped_face
      document.getElementById("overlaySegmented").src = data.segmentation_overlay

      segmentationSection.style.display = "block"
      initializeSegmentationTabs()
    } else {
      document.getElementById("segmentationSection").style.display = "none"
    }

    // Show YOLO detection if available
    if (data.yolo_boxes && data.yolo_boxes.length > 0) {
      const yoloDetectionSection = document.getElementById("yoloDetectionSection")
      const yoloCanvas = document.getElementById("yoloCanvas")
      const ctx = yoloCanvas.getContext("2d")
      const image = new Image()

      image.onload = () => {
        // Set canvas size to match image
        yoloCanvas.width = image.width
        yoloCanvas.height = image.height

        // Draw the image
        ctx.drawImage(image, 0, 0)

        // Draw bounding boxes
        data.yolo_boxes.forEach((box) => {
          const [x1, y1, x2, y2] = box.bbox
          const label = box.label
          const confidence = box.confidence

          // Draw bounding box
          ctx.strokeStyle = "#00ff00"
          ctx.lineWidth = 3
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

          // Draw semi-transparent background for text
          ctx.fillStyle = "rgba(0, 255, 0, 0.8)"
          ctx.fillRect(x1, y1 - 25, (label.length + 10) * 8, 25)

          // Draw label text
          ctx.fillStyle = "#000000"
          ctx.font = "bold 14px Arial"
          ctx.fillText(`${label} ${(confidence * 100).toFixed(1)}%`, x1 + 5, y1 - 8)
        })
      }
      image.crossOrigin = "anonymous"
      image.src = data.cropped_face
      yoloDetectionSection.style.display = "block"
    } else {
      document.getElementById("yoloDetectionSection").style.display = "none"
    }
  }

  // Show skin type probabilities if available
  const skinTypeLabels = ["Dry", "Normal", "Oily"]
  const typeColors = ["#64b5f6", "#4fc3f7", "#4dd0e1"]

  if (data.type_probs && data.type_probs.length === skinTypeLabels.length) {
    document.getElementById("typeProbsSection").style.display = "block"
    createProbBars("typeProbsBars", skinTypeLabels, data.type_probs, typeColors)
  } else {
    document.getElementById("typeProbsSection").style.display = "none"
  }

  // Show acne analysis if available
  if (data.acne_pred && data.acne_confidence) {
    const acneAnalysisSection = document.getElementById("acneAnalysisSection")
    const acneConfidenceFill = document.getElementById("acneConfidenceFill")
    const acneConfidenceText = document.getElementById("acneConfidenceText")

    const confidencePercent = data.acne_confidence * 100

    acneConfidenceFill.style.width = confidencePercent + "%"
    acneConfidenceText.textContent = `${data.acne_pred} - ${confidencePercent.toFixed(1)}% Confidence`

    acneAnalysisSection.style.display = "block"
  } else {
    document.getElementById("acneAnalysisSection").style.display = "none"
  }

  // Generate recommendation based on available data
  generateRecommendation(data)

  ajaxResults.style.display = "block"
  ajaxResults.classList.add("active")
}

function generateRecommendation(data) {
  let recommendation = "Based on your comprehensive AI analysis: "

  if (data.skin_type) {
    recommendation += `Your ${data.skin_type.toLowerCase()} skin type `
  }

  if (data.acne_pred && data.acne_pred.toLowerCase() !== "unknown") {
    recommendation += `with ${data.acne_pred.toLowerCase()} acne level `
  }

  if (data.left_eye_color && data.right_eye_color) {
    recommendation += `and your beautiful ${data.left_eye_color.toLowerCase()} eyes `
  }

  recommendation += "suggest specific makeup techniques that will enhance your natural beauty. "

  // Add segmentation-based recommendations
  if (data.segmentation_overlay) {
    recommendation +=
      "Our advanced skin mapping has identified specific areas that can benefit from targeted makeup application. "
  }

  // Add skin type specific recommendations
  if (data.skin_type) {
    const skinType = data.skin_type.toLowerCase()
    if (skinType === "dry") {
      recommendation += "For dry skin, use hydrating primers and cream-based foundations. "
    } else if (skinType === "oily") {
      recommendation += "For oily skin, use mattifying primers and long-lasting foundations. "
    } else if (skinType === "normal") {
      recommendation += "Your normal skin type gives you flexibility with most makeup products. "
    }
  }

  // Add acne-specific recommendations
  if (data.acne_pred) {
    const acneLevel = data.acne_pred.toLowerCase()
    if (acneLevel === "severe" || acneLevel === "high") {
      recommendation +=
        "For acne-prone skin, use non-comedogenic products and consider color-correcting concealers. Green concealer can neutralize redness. "
    } else if (acneLevel === "moderate" || acneLevel === "medium") {
      recommendation += "For moderate acne, use lightweight, buildable coverage and spot concealing techniques. "
    } else if (acneLevel === "mild" || acneLevel === "low") {
      recommendation += "With mild acne concerns, focus on gentle coverage and skin-friendly formulations. "
    } else if (acneLevel === "clear" || acneLevel === "none") {
      recommendation += "Your clear skin allows for versatile makeup looks and lighter coverage options. "
    }
  }

  // Add eye color specific recommendations
  if (data.left_eye_color) {
    const eyeColor = data.left_eye_color.toLowerCase()
    if (eyeColor.includes("brown")) {
      recommendation += "Brown eyes look stunning with warm golds, bronzes, and deep purples."
    } else if (eyeColor.includes("blue")) {
      recommendation += "Blue eyes pop with warm oranges, coppers, and complementary browns."
    } else if (eyeColor.includes("green")) {
      recommendation += "Green eyes are enhanced by purples, plums, and warm reddish tones."
    } else if (eyeColor.includes("hazel")) {
      recommendation += "Hazel eyes can be enhanced with both warm and cool tones depending on the lighting."
    }
  }

  document.getElementById("recommendationText").textContent = recommendation
}

function resetForm() {
  ajaxResults.style.display = "none"
  ajaxResults.classList.remove("active")
  document.querySelector(".upload-section").style.display = "block"
  document.querySelector(".camera-section").style.display = "block"
  document.querySelector(".divider").style.display = "block"
  uploadForm.reset()
  photoPreview.style.display = "none"
  photoPreview.innerHTML = ""
  document.getElementById("typeProbsSection").style.display = "none"
  document.getElementById("croppedFaceSection").style.display = "none"
  document.getElementById("yoloDetectionSection").style.display = "none"
  document.getElementById("acneAnalysisSection").style.display = "none"
  document.getElementById("segmentationSection").style.display = "none"
}

// Camera functionality
startCameraBtn.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user",
      },
    })
    video.srcObject = stream
    video.parentElement.style.display = "block"
    captureBtn.disabled = false
    startCameraBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Camera'
    startCameraBtn.onclick = stopCamera
  } catch (err) {
    alert("Could not access camera: " + err.message)
  }
})

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
    video.parentElement.style.display = "none"
    captureBtn.disabled = true
    startCameraBtn.innerHTML = '<i class="fas fa-video"></i> Start Camera'
    startCameraBtn.onclick = () => startCameraBtn.click()
  }
}

captureBtn.addEventListener("click", async () => {
  const context = canvas.getContext("2d")
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  context.drawImage(video, 0, 0, canvas.width, canvas.height)

  const dataUrl = canvas.toDataURL("image/jpeg", 0.8)
  capturedPhotoInput.value = dataUrl

  showLoading()
  captureBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...'
  captureBtn.disabled = true

  const formData = new FormData(cameraForm)

  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })

    const data = await response.json()
    hideLoading()

    if (data.error) {
      alert("Error: " + data.error)
      return
    }

    showResults(data)
  } catch (err) {
    hideLoading()
    alert("Something went wrong: " + err.message)
  }

  stopCamera()
  captureBtn.innerHTML = '<i class="fas fa-camera-retro"></i> Capture Photo'
  captureBtn.disabled = false
})
