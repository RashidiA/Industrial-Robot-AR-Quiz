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
    
    /* Top Banner Notification */
    #feedback-banner {
      position: absolute;
      top: 15px;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(46, 196, 182, 0.95);
      color: #ffffff;
      padding: 10px 25px;
      border-radius: 20px;
      font-size: 20px;
      font-weight: bold;
      display: none;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
      z-index: 10;
      transition: opacity 0.3s ease;
    }

    /* Reset Button */
    #reset-btn {
      position: absolute;
      bottom: 15px;
      right: 20px;
      background-color: #e63946;
      color: #ffffff;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      pointer-events: auto;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      transition: background-color 0.2s ease;
      z-index: 10;
    }
    #reset-btn:hover {
      background-color: #c1121f;
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
    <div id="feedback-banner">You are correct !!</div>
    <button id="reset-btn" onclick="resetQuiz()">Reset</button>

    <!-- Questions (Blue Boxes) -->
    <div id="q1" class="card question" style="top: 100px;">How many Axes in industrial robot ?</div>
    <div id="q2" class="card question" style="top: 300px;">How do you control an industrial robot ?</div>
    
    <!-- Answers (Yellow Boxes) -->
    <div id="a1" class="card answer" style="top: 100px;" data-match="q1" data-initial-top="100px" data-initial-left="580px">6 Axes</div>
    <div id="a2" class="card answer" style="top: 300px;" data-match="q2" data-initial-top="300px" data-initial-left="580px">Using robot controller</div>
  </div>
</div>

<script>
  const videoElement = document.getElementById('webcam');
  const canvasElement = document.getElementById('canvas');
  const canvasCtx = canvasElement.getContext('2d');
  const feedbackBanner = document.getElementById('feedback-banner');
  
  let draggedCard = null;
  let offsetX = 0, offsetY = 0;
  let bannerTimeout = null;

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

  function showCorrectBanner() {
    feedbackBanner.style.display = 'block';
    if (bannerTimeout) clearTimeout(bannerTimeout);
    bannerTimeout = setTimeout(() => {
      feedbackBanner.style.display = 'none';
    }, 2500);
  }

  function resetQuiz() {
    answers.forEach(card => {
      const targetId = card.getAttribute('data-match');
      const targetQuestion = document.getElementById(targetId);
      
      card.classList.remove('matched');
      targetQuestion.classList.remove('matched');
      
      card.style.top = card.getAttribute('data-initial-top');
      card.style.left = card.getAttribute('data-initial-left');
    });
    feedbackBanner.style.display = 'none';
  }

  function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const landmarks = results.multiHandLandmarks[0];
      
      const thumbTip = landmarks[4];
      const indexTip = landmarks[8];
      const palmCenter = landmarks[9];

      const palmX = palmCenter.x * 1000;
      const palmY = palmCenter.y * 550;

      const cursorX = indexTip.x * 1000;
      const cursorY = indexTip.y * 550;

      const screenCursorX = (1 - indexTip.x) * 1000;
      const screenCursorY = indexTip.y * 550;

      // 1. Red Marker fixed at Palm Center
      canvasCtx.fillStyle = '#ff0055';
      canvasCtx.beginPath();
      canvasCtx.arc(palmX, palmY, 14, 0, 2 * Math.PI);
      canvasCtx.fill();

      const pinchDistance = getDistance(indexTip, thumbTip);
      const isPinching = pinchDistance < 65; 

      // 2. Interactive Cursor at Index Fingertip
      canvasCtx.fillStyle = isPinching ? '#00ff00' : '#00b4d8';
      canvasCtx.beginPath();
      canvasCtx.arc(cursorX, cursorY, 12, 0, 2 * Math.PI);
      canvasCtx.fill();

      if (isPinching) {
        if (!draggedCard) {
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
          let newX = screenCursorX - offsetX;
          let newY = screenCursorY - offsetY;
          draggedCard.style.left = `${newX}px`;
          draggedCard.style.top = `${newY}px`;
        }
      } else {
        if (draggedCard) {
          const targetId = draggedCard.getAttribute('data-match');
          const targetQuestion = document.getElementById(targetId);
          
          const dragRect = draggedCard.getBoundingClientRect();
          const targetRect = targetQuestion.getBoundingClientRect();

          if (checkOverlap(dragRect, targetRect)) {
            // Correct match
            draggedCard.classList.add('matched');
            targetQuestion.classList.add('matched');
            
            // Align answer over question
            const containerRect = document.getElementById('container').getBoundingClientRect();
            draggedCard.style.left = `${targetRect.left - containerRect.left}px`;
            draggedCard.style.top = `${targetRect.top - containerRect.top}px`;

            // Display "You are correct !!" message
            showCorrectBanner();
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
