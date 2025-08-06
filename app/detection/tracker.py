# app/detection/tracker.py
try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError:
    try:
        from deep_sort_realtime import DeepSort
    except ImportError:
        print("⚠️  DeepSort not available, using simple tracker")
        DeepSort = None

import numpy as np
import cv2

class Tracker:  # Changed from PersonTracker to Tracker
    def __init__(self, max_age=50, n_init=3, max_cosine_distance=0.4):
        """
        Initialize the DeepSort tracker or fallback to simple tracker
        """
        if DeepSort is not None:
            try:
                self.tracker = DeepSort(
                    max_age=max_age,
                    n_init=n_init,
                    max_cosine_distance=max_cosine_distance,
                    embedder="mobilenet",
                    half=False,  # Changed to False for stability
                    bgr=True,
                    embedder_gpu=False,  # Changed to False for stability
                    embedder_model_name=None,
                    embedder_wts=None,
                    polygon=False,
                    today=None
                )
                self.use_deepsort = True
                print("✅ Using DeepSort tracker")
            except Exception as e:
                print(f"⚠️  DeepSort failed to initialize: {e}")
                self.use_deepsort = False
                self._init_simple_tracker()
        else:
            self.use_deepsort = False
            self._init_simple_tracker()
    
    def _init_simple_tracker(self):
        """Initialize simple tracking system"""
        self.tracks = {}
        self.next_id = 1
        self.max_age = 30
        self.track_ages = {}
        self.track_positions = {}
        print("✅ Using Simple tracker (fallback)")
    
    def update(self, frame, bbox_xywh, confidences):
        """
        Update tracker with new detections
        """
        if self.use_deepsort:
            return self._update_deepsort(frame, bbox_xywh, confidences)
        else:
            return self._update_simple(frame, bbox_xywh, confidences)
    
    def _update_deepsort(self, frame, bbox_xywh, confidences):
        """Update using DeepSort with proper format"""
        if len(bbox_xywh) == 0:
            return self.tracker.update_tracks([], frame=frame)
        
        # Convert detections to the format DeepSort expects
        # Format: list of (bbox, confidence, detection_class) tuples
        # where bbox is [left, top, width, height]
        raw_detections = []
        
        try:
            for i, (bbox, conf) in enumerate(zip(bbox_xywh, confidences)):
                # bbox is in [center_x, center_y, width, height] format
                # Convert to [left, top, width, height] format
                if len(bbox) == 4:
                    center_x, center_y, w, h = bbox
                    left = center_x - w/2
                    top = center_y - h/2
                    
                    # Ensure all values are floats
                    detection_bbox = [float(left), float(top), float(w), float(h)]
                    detection_conf = float(conf)
                    
                    raw_detections.append((detection_bbox, detection_conf, 'person'))
            
            if not raw_detections:
                return self.tracker.update_tracks([], frame=frame)
            
            # Update tracker
            return self.tracker.update_tracks(raw_detections, frame=frame)
            
        except Exception as e:
            print(f"⚠️  DeepSort error: {e}")
            print("Switching to simple tracker...")
            self.use_deepsort = False
            self._init_simple_tracker()
            return self._update_simple(frame, bbox_xywh, confidences)
    
    def _update_simple(self, frame, bbox_xywh, confidences):
        """Simple tracking implementation with better matching"""
        # Age existing tracks
        for track_id in list(self.track_ages.keys()):
            self.track_ages[track_id] += 1
            if self.track_ages[track_id] > self.max_age:
                if track_id in self.tracks:
                    del self.tracks[track_id]
                del self.track_ages[track_id]
                if track_id in self.track_positions:
                    del self.track_positions[track_id]
        
        # Process current detections
        current_detections = []
        for bbox, conf in zip(bbox_xywh, confidences):
            if conf > 0.5 and len(bbox) == 4:
                center_x, center_y, w, h = bbox
                current_detections.append({
                    'center': (center_x, center_y),
                    'bbox': [center_x - w/2, center_y - h/2, center_x + w/2, center_y + h/2],
                    'conf': conf
                })
        
        # Match detections to existing tracks
        matched_tracks = []
        used_track_ids = set()
        
        for detection in current_detections:
            best_match = None
            min_distance = float('inf')
            
            # Try to match with existing tracks
            for track_id in self.track_positions:
                if track_id in used_track_ids:
                    continue
                
                # Get previous center
                prev_bbox = self.track_positions[track_id]
                prev_center_x = (prev_bbox[0] + prev_bbox[2]) / 2
                prev_center_y = (prev_bbox[1] + prev_bbox[3]) / 2
                
                # Calculate distance
                dx = detection['center'][0] - prev_center_x
                dy = detection['center'][1] - prev_center_y
                distance = (dx*dx + dy*dy)**0.5
                
                if distance < min_distance and distance < 100:  # 100 pixels threshold
                    min_distance = distance
                    best_match = track_id
            
            if best_match is not None:
                # Update existing track
                self.track_positions[best_match] = detection['bbox']
                self.track_ages[best_match] = 0
                used_track_ids.add(best_match)
                track = SimpleTrack(best_match, detection['bbox'])
                matched_tracks.append(track)
            else:
                # Create new track
                track_id = self.next_id
                self.next_id += 1
                self.track_positions[track_id] = detection['bbox']
                self.track_ages[track_id] = 0
                track = SimpleTrack(track_id, detection['bbox'])
                matched_tracks.append(track)
        
        return matched_tracks


class SimpleTrack:
    """Simple track object to mimic DeepSort interface"""
    
    def __init__(self, track_id, ltrb):
        self.track_id = track_id
        self.ltrb = ltrb
        self.confirmed = True
    
    def to_ltrb(self):
        return self.ltrb
    
    def is_confirmed(self):
        return self.confirmed