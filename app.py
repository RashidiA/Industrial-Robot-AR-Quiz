import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR Hand Gesture Matching Quiz", layout="wide")

st.title("🧩 Interactive AR Matching Quiz")
st.caption("Edge-Computed Hand Tracking via WebAssembly & MediaPipe")

# Definition of quiz items
quiz_data = [
    {
        "id": "q1",
        "question": "How many Axes in industrial robot ?",
        "answer": "6 Axes",
        "q_y": 120,
        "a_y": 120
    },
    {
        "id": "q2",
        "question": "How do you control an industrial robot ?",
        "answer": "Using robot controller",
        "q_y": 280,
        "a_y": 280
    }
]

# Client-Side HTML/JS Edge Processing Component
html_code = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
  <style>
    body { margin: 0; padding: 0; background-color: #000; overflow: hidden; font-family: Arial, sans-serif; }
    #container { position: relative; width: 1000px; height: 500px; margin: 0 auto; }
    video { transform: scaleX(-1); display: none; }
    canvas { position: absolute; top: 0; left: 0; transform: scaleX(-1); }
    #overlay { position: absolute; top: 0; left: 0; width: 1000px; height: 500px; pointer-events: none; }
    
    .card {
      position: absolute;
      width: 320px;
      height: 90px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      font-size: 18px;
      font-weight: bold;
      color: #fff;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      transition: background-color 0.3s ease;
      box-sizing: border-box;
      padding: 10px;
    }
    
    .question { background-color: #4a90e2; border: 2px solid #2e6bba; left: 80px; }
    .answer { background-color: #f5a623; border: 2px solid #d48806; left: 580px; cursor: pointer; color: #000; }
    .matched { background-color: #2ec4b6 !important; border-color: #1b9aaa !important; color: #fff !important; }
  </style>
</head>
<body>

<div id="container">
  <video id="webcam" playsinline></video>
  <canvas id="canvas" width="1000" height="500"></canvas>
  <div id="overlay">
    <!-- Questions -->
    <div id="q1" class="card question" style="top: 100px;">How many Axes in industrial robot ?</div>
    <div id="q2" class="card question" style="top: 260px;">How do you control an industrial robot ?</div>
    
    <!-- Answers -->
    <div id="a1" class="card answer" style="top: 100px;" data-match="q1">6 Axes</div>
    <div id="a2" class="card answer" style="top: 260px;" data-match="q2">Using robot controller</div>
  </div>
</div>

<script>
  const videoElement = document.getElementById('webcam');
  const canvasElement = document.getElementById('canvas');
  const canvasCtx = canvasElement.getContext('2d');
  
  let draggedCard = null;
  let offsetX = 0, offsetY = 0;

  const answers = Array.from(document.querySelectorAll('.answer'));
  const questions = Array.from(document.querySelectorAll('.question'));

  function getDistance(p1, p2) {
    return Math.hypot((p1.x - p2.x) * 1000, (p1.y - p2.y) * 500);
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
    
    // Render local webcam frame (AR View)
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const landmarks = results.multiHandLandmarks[0];
      
      // Index Tip (8) and Thumb Tip (4)
      const indexTip = landmarks[8];
      const thumbTip = landmarks[4];

      // Mirror X coordinates to match canvas mirroring
      const cursorX = (1 - indexTip.x) * 1000;
      const cursorY = indexTip.y * 500;

      // Draw Cursor Indicator
      canvasCtx.fillStyle = '#ff0055';
      canvasCtx.beginPath();
      canvasCtx.arc(cursorX, cursorY, 12, 0, 2 * Math.PI);
      canvasCtx.fill();

      const pinchDistance = getDistance(indexTip, thumbTip);
      const isPinching = pinchDistance < 45;

      if (isPinching) {
        canvasCtx.strokeStyle = '#00ff00';
        canvasCtx.lineWidth = 4;
        canvasCtx.stroke();

        if (!draggedCard) {
          // Check if pinch is over an unmatched answer card
          answers.forEach(card => {
            if (!card.classList.contains('matched')) {
              const rect = card.getBoundingClientRect();
              const containerRect = document.getElementById('container').getBoundingClientRect();
              const cardX = rect.left - containerRect.left;
              const cardY = rect.top - containerRect.top;

              if (cursorX >= cardX && cursorX <= cardX + rect.width &&
                  cursorY >= cardY && cursorY <= cardY + rect.height) {
                draggedCard = card;
                offsetX = cursorX - cardX;
                offsetY = cursorY - cardY;
              }
            }
          });
        } else {
          // Move dragged card relative to pinched cursor
          let newX = cursorX - offsetX;
          let newY = cursorY - offsetY;
          draggedCard.style.left = `${newX}px`;
          draggedCard.style.top = `${newY}px`;
        }
      } else {
        // Pinch released -> Drop card & evaluate match
        if (draggedCard) {
          const targetId = draggedCard.getAttribute('data-match');
          const targetQuestion = document.getElementById(targetId);
          
          const dragRect = draggedCard.getBoundingClientRect();
          const targetRect = targetQuestion.getBoundingClientRect();

          if (checkOverlap(dragRect, targetRect)) {
            // Correct match sequence
            draggedCard.classList.add('matched');
            targetQuestion.classList.add('matched');
            
            // Snap position to question box
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
    height: 500
  });

  camera.start();
</script>

</body>
</html>
"""

components.html(html_code, height=520, width=1020)