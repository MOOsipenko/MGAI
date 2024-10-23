import openshape
from huggingface_hub import hf_hub_download
import torch
import json
import numpy as np
import transformers
import threading
import multiprocessing
import sys, os, shutil
import objaverse
from torch.nn import functional as F
import re

# Print device information
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

# Load the Pointcloud Encoder from OpenShape
pc_encoder = openshape.load_pc_encoder('openshape-pointbert-vitg14-rgb')

# Download pre-computed embeddings from the HuggingFace Hub
meta = json.load(
    open(hf_hub_download("OpenShape/openshape-objaverse-embeddings", "objaverse_meta.json", token=True, repo_type='dataset', local_dir="OpenShape-Embeddings"))
)

meta = {x['u']: x for x in meta['entries']}
deser = torch.load(
    hf_hub_download("OpenShape/openshape-objaverse-embeddings", "objaverse.pt", token=True, repo_type='dataset', local_dir="OpenShape-Embeddings"), map_location='cpu'
)
us = deser['us']
feats = deser['feats']

def move_files(file_dict, destination_folder, obj_id):
    os.makedirs(destination_folder, exist_ok=True)
    for item_id, file_path in file_dict.items():
        destination_path = f"{destination_folder}{obj_id}.glb"
        shutil.move(file_path, destination_path)
        print(f"File {item_id} moved from {file_path} to {destination_path}")

def load_openclip():
    """Load CLIP model and processor from Hugging Face"""
    print("Locking model loading...")
    sys.clip_move_lock = threading.Lock()
    print("Locked.")
    
    clip_model, clip_prep = transformers.CLIPModel.from_pretrained(
        "laion/CLIP-ViT-bigG-14-laion2B-39B-b160k",
        low_cpu_mem_usage=True,
        torch_dtype=half,
        offload_state_dict=True
    ), transformers.CLIPProcessor.from_pretrained("laion/CLIP-ViT-bigG-14-laion2B-39B-b160k")
    
    if torch.cuda.is_available():
        with sys.clip_move_lock:
            clip_model = clip_model.to(device)
    return clip_model, clip_prep

def retrieve(embedding, top, sim_th=0.0, filter_fn=None):
    """Retrieve the most similar objects based on the embedding."""
    sims = []
    embedding = F.normalize(embedding.detach().cpu(), dim=-1).squeeze()
    
    for chunk in torch.split(feats, 10240):
        sims.append(embedding @ F.normalize(chunk.float(), dim=-1).T)
    
    sims = torch.cat(sims)
    sims, idx = torch.sort(sims, descending=True)
    sim_mask = sims > sim_th
    sims = sims[sim_mask]
    idx = idx[sim_mask]
    
    results = []
    for i, sim in zip(idx, sims):
        if us[i] in meta:
            if filter_fn is None or filter_fn(meta[us[i]]):
                results.append(dict(meta[us[i]], sim=sim))
                if len(results) >= top:
                    break
    return results

def get_filter_fn():
    """Define a filtering function for objects based on attributes like faces and animations."""
    face_min, face_max = 0, 34985808
    anim_min, anim_max = 0, 563
    anim_n = not (anim_min > 0 or anim_max < 563)
    face_n = not (face_min > 0 or face_max < 34985808)
    
    return lambda x: (
        (anim_n or anim_min <= x['anims'] <= anim_max)
        and (face_n or face_min <= x['faces'] <= face_max)
    )

def preprocess(input_string):
    """Preprocess the input string to remove numericals and underscores."""
    wo_numericals = re.sub(r'\d', '', input_string)
    output = wo_numericals.replace("_", " ")
    return output

# Set float precision for processing
f32 = np.float32
half = torch.float16 if torch.cuda.is_available() else torch.bfloat16

# Load CLIP model and processor
clip_model, clip_prep = load_openclip()

# Disable gradient computation for evaluation
torch.set_grad_enabled(False)

# Load the scene graph
file_path = "scene_graph.json"
with open(file_path, "r") as file:
    objects_in_room = json.load(file)

# Process each object in the room and retrieve similar objects
for obj_in_room in objects_in_room:
    if "style" in obj_in_room and "material" in obj_in_room:
        style, material = obj_in_room['style'], obj_in_room["material"]
    else:
        continue
    
    # Create the text prompt for CLIP
    text = preprocess(f"A high-poly {obj_in_room['new_object_id']} with {material} material and in {style} style, high quality")
    
    # Process text and retrieve the most similar object
    tn = clip_prep(text=[text], return_tensors='pt', truncation=True, max_length=76).to(device)
    enc = clip_model.get_text_features(**tn).float().cpu()
    
    # Retrieve similar objects based on embeddings
    retrieved_obj = retrieve(enc, top=1, sim_th=0.1, filter_fn=get_filter_fn())[0]
    print("Retrieved object:", retrieved_obj["u"])
    
    # Load and move the retrieved object to the destination folder
    processes = multiprocessing.cpu_count()
    objaverse_objects = objaverse.load_objects(uids=[retrieved_obj['u']], download_processes=processes)
    
    destination_folder = os.path.join(os.getcwd(), "Assets/")
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    move_files(objaverse_objects, destination_folder, obj_in_room['new_object_id'])
