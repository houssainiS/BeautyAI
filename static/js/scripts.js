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

// New feedback elements
const feedbackSection = document.getElementById("feedbackSection")
const likeBtn = document.getElementById("likeBtn")
const dislikeBtn = document.getElementById("dislikeBtn")
const dislikeFeedbackArea = document.getElementById("dislikeFeedbackArea")
const dislikeReason = document.getElementById("dislikeReason")
const submitDislikeFeedbackBtn = document.getElementById("submitDislikeFeedbackBtn")
const feedbackMessage = document.getElementById("feedbackMessage")

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
      resetForm() // Re-show buttons on error
      return
    }
    showResults(data)
  } catch (err) {
    hideLoading()
    alert("Something went wrong: " + err.message)
    resetForm() // Re-show buttons on error
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
  const tabButtons = document.querySelectorAll(".segmentation-tabs .tab-btn")
  const containers = {
    original: document.getElementById("originalContainer"),
    segmented: document.getElementById("segmentedContainer"),
    overlay: document.getElementById("overlayContainer"),
  }

  // Set initial state: segmented tab active, segmented image visible
  tabButtons.forEach((button) => {
    if (button.dataset.tab === "segmented") {
      button.classList.add("active")
    } else {
      button.classList.remove("active")
    }
  })

  Object.keys(containers).forEach((key) => {
    if (key === "segmented") {
      containers[key].style.display = "block"
    } else {
      containers[key].style.display = "none"
    }
  })

  // Add event listeners for subsequent clicks
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
      initializeSegmentationTabs() // This function needs to be updated
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

  // Show feedback section and reset its state
  feedbackSection.style.display = "block"
  feedbackMessage.style.display = "none" // Hide any previous feedback message
  dislikeFeedbackArea.style.display = "none" // Hide dislike area initially
  dislikeReason.value = "" // Clear previous reason
  likeBtn.disabled = false // Enable buttons
  dislikeBtn.disabled = false
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
    } else if (eyeColor.includes("eyes closed")) {
      recommendation += "Please ensure your eyes are open in the photo for accurate eye color analysis."
    }
  }

  document.getElementById("recommendationText").textContent = recommendation
}

function resetForm() {
  stopCamera() // Ensure camera is stopped and capture button is disabled
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

  // Reset feedback section
  feedbackSection.style.display = "none"
  feedbackMessage.style.display = "none"
  dislikeFeedbackArea.style.display = "none"
  dislikeReason.value = ""
  likeBtn.disabled = false
  dislikeBtn.disabled = false
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
    resetForm() // Re-show buttons on camera access error
  }
})

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
    video.parentElement.style.display = "none"
    captureBtn.disabled = true
    startCameraBtn.innerHTML = '<i class="fas fa-video"></i> Start Camera'
    startCameraBtn.onclick = () => startCameraBtn.click() // Re-attach original click handler
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
      resetForm() // Re-show buttons on error
      return
    }

    showResults(data)
  } catch (err) {
    hideLoading()
    alert("Something went wrong: " + err.message)
    resetForm() // Re-show buttons on error
  }

  stopCamera()
  captureBtn.innerHTML = '<i class="fas fa-camera-retro"></i> Capture Photo'
  captureBtn.disabled = false
})

// Function to send feedback to the backend
async function sendFeedback(feedbackType, reason = "") {
  feedbackMessage.style.display = "none" // Hide previous messages
  likeBtn.disabled = true
  dislikeBtn.disabled = true
  submitDislikeFeedbackBtn.disabled = true // Disable submit button for dislike

  try {
    const response = await fetch("/submit-feedback/", {
      // Ensure this URL matches your Django urls.py
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Since your Django view is @csrf_exempt, we don't strictly need CSRF token here.
        // If you remove @csrf_exempt later, you'll need to add:
        // "X-CSRFToken": getCookie('csrftoken'),
      },
      body: JSON.stringify({
        feedback_type: feedbackType,
        dislike_reason: reason,
      }),
    })

    const data = await response.json()

    if (response.ok) {
      feedbackMessage.textContent = data.message || "Thank you for your feedback!"
      feedbackMessage.classList.remove("text-red-600", "bg-red-100", "border-red-200")
      feedbackMessage.classList.add("text-green-600", "bg-green-100", "border-green-200")
    } else {
      feedbackMessage.textContent = data.error || "Failed to submit feedback."
      feedbackMessage.classList.remove("text-green-600", "bg-green-100", "border-green-200")
      feedbackMessage.classList.add("text-red-600", "bg-red-100", "border-red-200")
      // Re-enable buttons if submission failed
      likeBtn.disabled = false
      dislikeBtn.disabled = false
      if (feedbackType === "dislike") {
        submitDislikeFeedbackBtn.disabled = false
      }
    }
  } catch (error) {
    feedbackMessage.textContent = "Network error: Could not submit feedback."
    feedbackMessage.classList.remove("text-green-600", "bg-green-100", "border-green-200")
    feedbackMessage.classList.add("text-red-600", "bg-red-100", "border-red-200")
    // Re-enable buttons on network error
    likeBtn.disabled = false
    dislikeBtn.disabled = false
    if (feedbackType === "dislike") {
      submitDislikeFeedbackBtn.disabled = false
    }
  } finally {
    feedbackMessage.style.display = "block"
    dislikeFeedbackArea.style.display = "none" // Hide dislike area after submission attempt
    dislikeReason.value = "" // Clear reason
  }
}

// Feedback functionality event listeners
likeBtn.addEventListener("click", () => {
  sendFeedback("like")
})

dislikeBtn.addEventListener("click", () => {
  dislikeFeedbackArea.style.display = "block"
  feedbackMessage.style.display = "none" // Hide any previous message
  likeBtn.disabled = true // Disable like button once dislike is chosen
  dislikeBtn.disabled = true // Disable dislike button to prevent multiple clicks
  submitDislikeFeedbackBtn.disabled = false // Enable submit button for dislike
})

submitDislikeFeedbackBtn.addEventListener("click", () => {
  const reason = dislikeReason.value.trim()
  if (reason) {
    sendFeedback("dislike", reason)
  } else {
    alert("Please provide a reason for disliking the analysis.")
  }
})

// Helper function to get CSRF token (if needed later)
// function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = cookies[i].trim();
//             // Does this cookie string begin with the name we want?
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }
