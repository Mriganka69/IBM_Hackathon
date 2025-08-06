import numpy as np
import cv2
import time
from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict, deque

class TailgatingDetector:
    def __init__(self, 
                 entry_zone_threshold: float = 0.3,
                 time_window: float = 5.0,
                 min_persons_for_tailgating: int = 2,
                 confidence_threshold: float = 0.7):
        """
        Initialize tailgating detector
        
        Args:
            entry_zone_threshold: Fraction of frame height that defines entry zone
            time_window: Time window in seconds to consider for tailgating detection
            min_persons_for_tailgating: Minimum number of persons to trigger tailgating alert
            confidence_threshold: Confidence threshold for tailgating detection
        """
        self.entry_zone_threshold = entry_zone_threshold
        self.time_window = time_window
        self.min_persons_for_tailgating = min_persons_for_tailgating
        self.confidence_threshold = confidence_threshold
        
        # Tracking state
        self.track_history = defaultdict(lambda: deque(maxlen=30))  # Track last 30 positions
        self.entry_events = deque(maxlen=100)  # Track last 100 entry events
        self.active_tracks = set()
        self.entry_zone_persons = set()
        
        # Tailgating detection state
        self.last_card_swipe_time = None
        self.persons_entering_with_card = set()
        self.tailgating_alerts = []
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Tailgating detector initialized")
    
    def update_tracks(self, tracks: List, frame_shape: Tuple[int, int]) -> Dict:
        """
        Update tracking information and detect tailgating
        
        Args:
            tracks: List of track objects from DeepSort
            frame_shape: Frame dimensions (height, width)
            
        Returns:
            Dictionary containing tailgating detection results
        """
        try:
            frame_height, frame_width = frame_shape
            entry_zone_y = int(frame_height * self.entry_zone_threshold)
            
            current_time = time.time()
            current_tracks = set()
            persons_in_entry_zone = set()
            
            # Process current tracks
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                current_tracks.add(track_id)
                
                # Get track bounding box
                bbox = track.to_ltrb()
                x1, y1, x2, y2 = bbox
                
                # Calculate center point
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Update track history
                self.track_history[track_id].append({
                    'time': current_time,
                    'center': (center_x, center_y),
                    'bbox': bbox
                })
                
                # Check if person is in entry zone
                if center_y < entry_zone_y:
                    persons_in_entry_zone.add(track_id)
            
            # Update active tracks
            self.active_tracks = current_tracks
            
            # Detect entry events
            entry_events = self._detect_entry_events(persons_in_entry_zone, current_time)
            
            # Update entry zone persons
            self.entry_zone_persons = persons_in_entry_zone
            
            # Detect tailgating
            tailgating_result = self._detect_tailgating(entry_events, current_time)
            
            return {
                'tailgating_detected': tailgating_result['detected'],
                'tailgating_confidence': tailgating_result['confidence'],
                'persons_in_entry_zone': len(persons_in_entry_zone),
                'entry_events': entry_events,
                'tailgating_details': tailgating_result['details']
            }
            
        except Exception as e:
            self.logger.error(f"Error updating tracks: {e}")
            return {
                'tailgating_detected': False,
                'tailgating_confidence': 0.0,
                'persons_in_entry_zone': 0,
                'entry_events': [],
                'tailgating_details': {}
            }
    
    def _detect_entry_events(self, persons_in_entry_zone: set, current_time: float) -> List[Dict]:
        """
        Detect when persons enter the entry zone
        
        Args:
            persons_in_entry_zone: Set of track IDs currently in entry zone
            current_time: Current timestamp
            
        Returns:
            List of entry events
        """
        entry_events = []
        
        # Find new persons entering the zone
        new_entries = persons_in_entry_zone - self.entry_zone_persons
        
        for track_id in new_entries:
            # Get track history
            history = self.track_history[track_id]
            if len(history) < 2:
                continue
            
            # Check if person moved from outside to inside entry zone
            prev_pos = history[-2]['center']
            curr_pos = history[-1]['center']
            
            # Entry zone is at the top of the frame
            if prev_pos[1] >= self.entry_zone_threshold and curr_pos[1] < self.entry_zone_threshold:
                entry_events.append({
                    'track_id': track_id,
                    'time': current_time,
                    'position': curr_pos
                })
        
        return entry_events
    
    def _detect_tailgating(self, entry_events: List[Dict], current_time: float) -> Dict:
        """
        Detect tailgating based on entry events and card swipe timing
        
        Args:
            entry_events: List of recent entry events
            current_time: Current timestamp
            
        Returns:
            Tailgating detection result
        """
        # If no card swipe recently, no tailgating
        if self.last_card_swipe_time is None:
            return {
                'detected': False,
                'confidence': 0.0,
                'details': {}
            }
        
        # Check if we're within the time window of the last card swipe
        time_since_swipe = current_time - self.last_card_swipe_time
        if time_since_swipe > self.time_window:
            return {
                'detected': False,
                'confidence': 0.0,
                'details': {}
            }
        
        # Count persons entering during the time window
        persons_entering = set()
        for event in entry_events:
            if event['time'] >= self.last_card_swipe_time:
                persons_entering.add(event['track_id'])
        
        # Add persons already in entry zone
        persons_entering.update(self.entry_zone_persons)
        
        # Check for tailgating
        if len(persons_entering) >= self.min_persons_for_tailgating:
            # Calculate confidence based on number of persons and timing
            confidence = min(1.0, len(persons_entering) / 3.0)  # Max confidence at 3+ persons
            
            # Adjust confidence based on timing
            time_factor = max(0.0, 1.0 - (time_since_swipe / self.time_window))
            confidence *= time_factor
            
            if confidence >= self.confidence_threshold:
                return {
                    'detected': True,
                    'confidence': confidence,
                    'details': {
                        'persons_count': len(persons_entering),
                        'time_since_swipe': time_since_swipe,
                        'persons_entering': list(persons_entering)
                    }
                }
        
        return {
            'detected': False,
            'confidence': 0.0,
            'details': {}
        }
    
    def register_card_swipe(self, card_id: str, person_id: str, timestamp: float):
        """
        Register a card swipe event
        
        Args:
            card_id: ID of the swiped card
            person_id: ID of the person who swiped the card
            timestamp: Timestamp of the swipe
        """
        self.last_card_swipe_time = timestamp
        self.persons_entering_with_card.add(person_id)
        
        self.logger.info(f"Card swipe registered: {card_id} by {person_id}")
    
    def get_tailgating_statistics(self) -> Dict:
        """
        Get tailgating detection statistics
        
        Returns:
            Dictionary with tailgating statistics
        """
        return {
            'total_alerts': len(self.tailgating_alerts),
            'active_tracks': len(self.active_tracks),
            'persons_in_entry_zone': len(self.entry_zone_persons),
            'last_card_swipe_time': self.last_card_swipe_time,
            'recent_alerts': self.tailgating_alerts[-10:] if self.tailgating_alerts else []
        }
    
    def draw_tailgating_visualization(self, frame: np.ndarray, 
                                    tailgating_result: Dict) -> np.ndarray:
        """
        Draw tailgating detection visualization on frame
        
        Args:
            frame: Input frame
            tailgating_result: Result from update_tracks method
            
        Returns:
            Frame with visualization drawn
        """
        try:
            result_frame = frame.copy()
            height, width = frame.shape[:2]
            
            # Draw entry zone
            entry_zone_y = int(height * self.entry_zone_threshold)
            cv2.line(result_frame, (0, entry_zone_y), (width, entry_zone_y), (0, 255, 255), 2)
            cv2.putText(result_frame, "Entry Zone", (10, entry_zone_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Draw tailgating alert if detected
            if tailgating_result['tailgating_detected']:
                # Draw red overlay
                overlay = result_frame.copy()
                cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 255), -1)
                cv2.addWeighted(overlay, 0.3, result_frame, 0.7, 0, result_frame)
                
                # Draw alert text
                alert_text = f"TAILGATING DETECTED! ({tailgating_result['tailgating_confidence']:.2f})"
                cv2.putText(result_frame, alert_text, (width//2 - 200, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                
                # Draw details
                details = tailgating_result['tailgating_details']
                if details:
                    detail_text = f"Persons: {details.get('persons_count', 0)}"
                    cv2.putText(result_frame, detail_text, (10, height - 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Draw statistics
            stats_text = f"Entry Zone: {tailgating_result['persons_in_entry_zone']} persons"
            cv2.putText(result_frame, stats_text, (10, height - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return result_frame
            
        except Exception as e:
            self.logger.error(f"Error drawing tailgating visualization: {e}")
            return frame
    
    def reset(self):
        """Reset tailgating detector state"""
        self.track_history.clear()
        self.entry_events.clear()
        self.active_tracks.clear()
        self.entry_zone_persons.clear()
        self.last_card_swipe_time = None
        self.persons_entering_with_card.clear()
        self.tailgating_alerts.clear()
        
        self.logger.info("Tailgating detector reset") 