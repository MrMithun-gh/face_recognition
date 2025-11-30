import face_recognition
import numpy as np
import os
import pickle


class FaceRecognitionModel:
    def __init__(self, data_file='known_faces.dat'):
        """
        Model to store and match encodings of known identities.
        Each person stores multiple encodings to handle glasses, lighting, angles, etc.
        """
        self.data_file = data_file

        # known_encodings is now a list of lists (multiple encodings per person)
        self.known_encodings = []  # [[enc1, enc2, ...], [encA, encB, ...], ...]
        self.known_ids = []        # ["person_0001", "person_0002", ...]

        self.load_model()

    def load_model(self):
        """Load model from file if exists."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    self.known_encodings, self.known_ids = pickle.load(f)
                print(f"--- [ML MODEL] Loaded {len(self.known_ids)} known faces. ---")
            except Exception as e:
                print(f"--- [ML MODEL] Error loading model: {e}. Starting fresh. ---")

    def save_model(self):
        """Save model persistently."""
        with open(self.data_file, 'wb') as f:
            pickle.dump((self.known_encodings, self.known_ids), f)
        print(f"--- [ML MODEL] Model saved with {len(self.known_ids)} identities. ---")

    # ------------------------------------------------------------
    # ADD NEW OR REINFORCE EXISTING PERSON
    # ------------------------------------------------------------
    def update_person_encoding(self, idx, new_encoding):
        """Add new encoding to an existing user & keep encoding count limited."""
        self.known_encodings[idx].append(new_encoding)

        # Limit encoding history to last 12 encodings
        if len(self.known_encodings[idx]) > 12:
            self.known_encodings[idx] = self.known_encodings[idx][-12:]

        self.save_model()

    def learn_face(self, new_encoding):
        """Learn or reinforce a face using tolerant matching logic."""
        if not self.known_encodings:
            new_id = f"person_{len(self.known_ids) + 1:04d}"
            self.known_encodings.append([new_encoding])
            self.known_ids.append(new_id)
            print(f"--- [ML MODEL] Learned first face → {new_id} ---")
            self.save_model()
            return new_id

        # Compare new encoding against mean encoding of each identity
        avg_encodings = [np.mean(encodings, axis=0) for encodings in self.known_encodings]
        distances = face_recognition.face_distance(avg_encodings, new_encoding)
        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        # Dynamic tolerance: More relaxed for group photos
        STRICT_TOLERANCE = 0.63
        RELAXED_TOLERANCE = 0.72  # supports glasses, tilt, group scene distortions

        if best_distance <= STRICT_TOLERANCE:
            # Clear match, strengthen profile
            self.update_person_encoding(best_match_index, new_encoding)
            return self.known_ids[best_match_index]
        elif best_distance <= RELAXED_TOLERANCE:
            # Accept match but weaker confidence
            self.update_person_encoding(best_match_index, new_encoding)
            print(f"--- [ML MODEL] Weak match accepted ({best_distance:.2f}) | Reinforced {self.known_ids[best_match_index]} ---")
            return self.known_ids[best_match_index]
        else:
            # New person discovered
            new_id = f"person_{len(self.known_ids) + 1:04d}"
            self.known_encodings.append([new_encoding])
            self.known_ids.append(new_id)
            print(f"--- [ML MODEL] Learned NEW identity {new_id} | distance={best_distance:.2f} ---")
            self.save_model()
            return new_id

    # ------------------------------------------------------------
    # RECOGNITION
    # ------------------------------------------------------------
    def recognize_face(self, scanned_encoding):
        """Recognize the closest identity if confident enough."""
        if not self.known_encodings:
            return None

        avg_encodings = [np.mean(encodings, axis=0) for encodings in self.known_encodings]
        distances = face_recognition.face_distance(avg_encodings, scanned_encoding)
        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        STRICT_TOLERANCE = 0.63
        RELAXED_TOLERANCE = 0.72

        if best_distance <= STRICT_TOLERANCE:
            print(f"--- [ML MODEL] STRONG match {self.known_ids[best_match_index]} ({best_distance:.2f}) ---")
            return self.known_ids[best_match_index]

        if best_distance <= RELAXED_TOLERANCE:
            print(f"--- [ML MODEL] WEAK match accepted {self.known_ids[best_match_index]} ({best_distance:.2f}) ---")
            return self.known_ids[best_match_index]

        print(f"--- [ML MODEL] NO MATCH (best={best_distance:.2f}) ---")
        return None
