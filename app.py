import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR Hand Gesture Matching Quiz", layout="wide")

st.title("🧩 Interactive AR Matching Quiz")
st.caption("Edge-Computed Hand Tracking via WebAssembly & MediaPipe")

html_code = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #0d1117;
      overflow: hidden;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    #container {
      position: relative;
      width: 1000px;
      height: 550px;
      margin: 0 auto;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }
    video {
      display: none;
    }
    /* Mirror both video and canvas rendering together seamlessly */
    #canvas {
      position: absolute;
      top: 0;
      left: 0;
      transform: scaleX(-1);
    }
    #overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 1000px;
      height: 550px;
      pointer-events: none;
    }
    
    .card {
      position: absolute;
      width: 340px;
      height: 90px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      font-size: 18px;
      font-weight: bold;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      transition: background-color 0.3s ease, border-color 0.3s ease;
      box-sizing: border-box;
      padding: 15px;
      user-select: none;
    }
    
    /* Blue Question Boxes */
    .question {
      background-color: #4a90e2;
      border: 3px solid #2e6bba;
      color: #ffffff;
      left: 60px;
    }
    
    /* Yellow Answer Boxes */
    .answer {
      background-color: #f5a623;
      border: 3px solid #d48806;
      color: #000000;
      left: 580px;
    }
    
    /* Green Match State */
    .matched {
      background-color: #2ec4b6 !important;
      border-color: #1b9aaa !important;
      color: #ffffff !important;
    }
  </style>
</head>
<body>

<div id="container">
  <video id="webcam" playsinline></video>
  <canvas id="canvas" width="1000" height="550"></canvas>
  <div id="overlay">
    <!-- Questions (Blue Boxes) -->
    <div id="q1" class="card question" style="top: 100px;">How many Axes in industrial robot ?</div>
    <div id="q2" class="card question" style="top: 300px;">How do you control an industrial robot ?</div>
    
    <!-- Answers (Yellow Boxes) -->
    <div id="a1" class="card answer" style="top: 100px;" data-match="q1">6 Axes</div>
    <div id="a2" class="card answer" style="top: 300px;" data-match="q2">Using robot controller</div>
  </div>
</div>

<script>
  const videoElement = document.getElementById('webcam');
  const canvasElement = document.getElementById('canvas');
  const canvasCtx = canvasElement.getContext('2d');
  
  let draggedCard = null;
  let offsetX = 0, offsetY = 0;

  const answers = Array.from(document.querySelectorAll('.answer'));

  function getDistance(p1, p2) {
    return Math.hypot((p1.x - p2.x) * 1000, (p1.y - p2.y) * 550);
  }

  function checkOverlap(rect1, rect2) {
    return !(rect1.right < rect2.left || 
             rect1.left > rect2.right || 
             rect1.bottom < rect2.top || 
             rect1.top > rect2.bottom);
  }

  function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Render video frame on canvas
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const landmarks = results.multiHandLandmarks[0];
      
      const thumbTip = landmarks[4];     // Thumb Tip
      const indexTip = landmarks[8];     // Index Finger Tip
      const palmCenter = landmarks[9];   // Palm Center (Middle MCP)

      // Direct coordinate calculation (Matching canvas native coordinates)
      const palmX = palmCenter.x * 1000;
      const palmY = palmCenter.y * 550;

      const cursorX = indexTip.x * 1000;
      const cursorY = indexTip.y * 550;

      // Un-mirrored screen coordinates for DOM Box element detection
      const screenCursorX = (1 - indexTip.x) * 1000;
      const screenCursorY = indexTip.y * 550;

      // 1. Red Marker fixed at Center of Palm
      canvasCtx.fillStyle = '#ff0055';
      canvasCtx.beginPath();
      canvasCtx.arc(palmX, palmY, 14, 0, 2 * Math.PI);
      canvasCtx.fill();

      // Increased Pinch Distance threshold for easier picking
      const pinchDistance = getDistance(indexTip, thumbTip);
      const isPinching = pinchDistance < 65; 

      // 2. Interactive Cursor at Index Fingertip
      canvasCtx.fillStyle = isPinching ? '#00ff00' : '#00b4d8';
      canvasCtx.beginPath();
      canvasCtx.arc(cursorX, cursorY, 12, 0, 2 * Math.PI);
      canvasCtx.fill();

      if (isPinching) {
        if (!draggedCard) {
          // Check box collision with screen-mapped cursor coordinates
          answers.forEach(card => {
            if (!card.classList.contains('matched')) {
              const rect = card.getBoundingClientRect();
              const containerRect = document.getElementById('container').getBoundingClientRect();
              const cardX = rect.left - containerRect.left;
              const cardY = rect.top - containerRect.top;

              if (screenCursorX >= cardX && screenCursorX <= cardX + rect.width &&
                  screenCursorY >= cardY && screenCursorY <= cardY + rect.height) {
                draggedCard = card;
                offsetX = screenCursorX - cardX;
                offsetY = screenCursorY - cardY;
              }
            }
          });
        } else {
          // Drag card tracking index finger movement
          let newX = screenCursorX - offsetX;
          let newY = screenCursorY - offsetY;
          draggedCard.style.left = `${newX}px`;
          draggedCard.style.top = `${newY}px`;
        }
      } else {
        // Drop card & check match
        if (draggedCard) {
          const targetId = draggedCard.getAttribute('data-match');
          const targetQuestion = document.getElementById(targetId);
          
          const dragRect = draggedCard.getBoundingClientRect();
          const targetRect = targetQuestion.getBoundingClientRect();

          if (checkOverlap(dragRect, targetRect)) {
            // Correct match: Change color to Green
            draggedCard.classList.add('matched');
            targetQuestion.classList.add('matched');
            
            // Align answer over question
            const containerRect = document.getElementById('container').getBoundingClientRect();
            draggedCard.style.left = `${targetRect.left - containerRect.left}px`;
            draggedCard.style.top = `${targetRect.top - containerRect.top}px`;
          }
          draggedCard = null;
        }
      }
    }
    canvasCtx.restore();
  }

  const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
  });

  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.6,
    minTrackingConfidence: 0.6
  });

  hands.onResults(onResults);

  const camera = new Camera(videoElement, {
    onFrame: async () => {
      await hands.send({image: videoElement});
    },
    width: 1000,
    height: 550
  });

  camera.start();
</script>

</body>
</html>
"""

components.html(html_code, height=570, width=1020)
