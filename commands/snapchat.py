import os
import asyncio
from utils.helpers import edit_or_reply
import cv2
import numpy as np
from PIL import Image
from commands import astra_command, edit_or_reply, extract_args
from astra.types import Message
from utils.plugin_utils import Message
import tempfile

try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

@astra_command(
    name="snapchat",
    aliases=["filter", "ar"],
    category="Media",
    description="Apply AR face filters (Dog, Glasses, Beautify, Blur) to an image.",
    usage=".snapchat [filter_name]"
)
async def snapchat_handler(client, message: Message):
    if not HAS_MEDIAPIPE:
        return await edit_or_reply(message, "❌ *Error:* `mediapipe` not installed. Please install it to use AR filters.")

    args = extract_args(message)
    filter_type = args[0].lower() if args else "beautify"
    
    # 1. Get the image
    target = message.quoted if message.quoted and message.quoted.is_media else message
    if not target.is_media:
        return await edit_or_reply(message, "Please reply to an image or send one with the command.")

    status = await edit_or_reply(message, f"🪄 Applying `{filter_type}` filter...")
    
    file_path = await target.download()
    if not file_path:
        return await status.edit("❌ Failed to download media.")

    output_path = f"filtered_{os.path.basename(file_path)}"
    
    try:
        # Run processing in thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, apply_ar_filter, file_path, output_path, filter_type)
        
        if isinstance(result, str) and result.startswith("Error"):
            return await status.edit(f"❌ {result}")

        await client.chat.send_message(message.chat_id, caption=f"✨ Applied `{filter_type}` filter", file=output_path, reply_to=message.id)
        await status.delete()
    except Exception as e:
        await status.edit(f"❌ Processing Error: {str(e)}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(output_path): os.remove(output_path)

def apply_ar_filter(input_path, output_path, filter_type):
    img = cv2.imread(input_path)
    if img is None: return "Error: Could not read image."
    
    h, w = img.shape[:2]
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=5,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return "No faces detected in the image."

        for face_landmarks in results.multi_face_landmarks:
            if filter_type == "dog":
                img = overlay_filter(img, face_landmarks, "dog")
            elif filter_type == "glasses":
                img = overlay_filter(img, face_landmarks, "glasses")
            elif filter_type == "beautify":
                img = beautify_face(img, face_landmarks)
            elif filter_type == "blur":
                img = blur_background(img, face_landmarks)
            else:
                return f"Unknown filter: {filter_type}. Try: dog, glasses, beautify, blur"

    cv2.imwrite(output_path, img)
    return True

def overlay_filter(img, landmarks, type):
    # Placeholder for actual asset overlay logic (requires local PNGs for ears/nose/glasses)
    # For now, we draw stylized shapes to confirm positional accuracy
    if type == "dog":
        # Draw dog ears/nose placeholders
        for idx in [33, 263, 1]: # Left eye, Right eye, Nose tip
            pt = landmarks.landmark[idx]
            cv2.circle(img, (int(pt.x * img.shape[1]), int(pt.y * img.shape[0])), 10, (100, 50, 0), -1)
    return img

def beautify_face(img, landmarks):
    # Smooth skin while preserving edges
    return cv2.bilateralFilter(img, 9, 75, 75)

def blur_background(img, landmarks):
    # Simple radial blur around the face
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    # Create face hull
    points = []
    for landmark in landmarks.landmark:
        points.append((int(landmark.x * img.shape[1]), int(landmark.y * img.shape[0])))
    hull = cv2.convexHull(np.array(points))
    cv2.fillConvexPoly(mask, hull, 255)
    
    blurred = cv2.GaussianBlur(img, (21, 21), 0)
    img = np.where(mask[:, :, None] == 255, img, blurred)
    return img
