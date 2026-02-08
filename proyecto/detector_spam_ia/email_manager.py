import random
import joblib

class EmailManager:

    def __init__(self, model_path="modelo_spam.pkl"):
        self.model = joblib.load(model_path)

        self.inbox_folder = []
        self.spam_folder = []

        self.incoming_messages = []

    def ensure_connection(self, email_user, email_pass):
        """Ensures IMAP connection is active, reconnecting only if needed"""
        import imaplib
        
        # Check if we have a connection object
        if hasattr(self, 'mail') and self.mail:
            try:
                # Send NOOP to check connection status
                status, response = self.mail.noop()
                if status == 'OK':
                    return True, "Connected"
            except:
                # Connection dead, proceed to reconnect
                pass
        
        # If we reach here, we need to connect
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(email_user, email_pass)
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)

    def fetch_real_emails(self):
        """Fetches unseen emails from Inbox returning structured dicts"""
        import imaplib
        import email
        from email.header import decode_header

        if not hasattr(self, 'mail'):
            return []

        try:
            self.mail.select("inbox")
            # Fetch last 5 messages
            status, messages = self.mail.search(None, "ALL")
            
            if not messages or not messages[0]:
                return []

            email_ids = messages[0].split()
            latest_email_ids = email_ids[-10:] # Get last 10 to ensure we catch recent ones

            new_messages = []

            # Iterate strictly chronologically (Oldest -> Newest in this batch)
            # This ensures that when we append to our main list, it stays chronological.
            for e_id in latest_email_ids:
                # Fetch headers and body
                res, msg_data = self.mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode subject
                        try:
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                        except:
                            subject = "No Subject"
                        
                        # Decode sender
                        try:
                            sender, encoding = decode_header(msg.get("From"))[0]
                            if isinstance(sender, bytes):
                                sender = sender.decode(encoding if encoding else "utf-8")
                        except:
                            sender = "Unknown"
                        
                        # Unique ID logic
                        raw_id = msg.get("Message-ID", "")
                        if not raw_id:
                            # Fallback: Hash specific fields to create a consistent ID
                            # Using Date, Sender, Subject as unique fingerprint
                            fingerprint = f"{msg.get('Date')}-{sender}-{subject}"
                            import hashlib
                            msg_id = hashlib.md5(fingerprint.encode('utf-8', errors='ignore')).hexdigest()
                        else:
                            # Clean the ID to be safe for UI keys (remove brackets, spaces)
                            msg_id = raw_id.strip().replace('<', '').replace('>', '')

                        # Get body (Robust HTML support)
                        body = ""
                        html_body = ""
                        
                        if msg.is_multipart():
                            for part in msg.walk():
                                c_type = part.get_content_type()
                                c_disp = str(part.get("Content-Disposition"))

                                if "attachment" in c_disp:
                                    continue

                                try:
                                    part_payload = part.get_payload(decode=True).decode(errors="ignore")
                                except:
                                    part_payload = ""

                                if c_type == "text/plain":
                                    body += part_payload
                                elif c_type == "text/html":
                                    html_body += part_payload
                        else:
                            # Not multipart
                            try:
                                payload = msg.get_payload(decode=True).decode(errors="ignore")
                                if msg.get_content_type() == "text/html":
                                    html_body = payload
                                else:
                                    body = payload
                            except:
                                pass

                        # Fallback to HTML if body empty
                        if not body.strip() and html_body:
                            # Strip tags specifically for analysis (dirty simple way)
                            import re
                            clean_html = re.sub('<[^<]+?>', ' ', html_body)
                            body = clean_html

                        email_obj = {
                            "id": msg_id,
                            "sender": sender,
                            "subject": subject,
                            "body": body[:200].replace('\n', ' '), # Store snippet clean
                            "full_body": body
                        }
                        
                        new_messages.append(email_obj)
            
            return new_messages

        except Exception as e:
            print(f"Error fetching: {e}")
            return []

    def mock_incoming_message(self):
        import uuid
        normal_msgs = [
            {"sender": "Boss", "subject": "Meeting pending", "body": "Don't forget the meeting tomorrow at 10am."},
            {"sender": "Hr Dept", "subject": "Report needed", "body": "Can you send me the monthly report please?"},
            {"sender": "Google Calendar", "subject": "Reminder", "body": "Reminder about your class today at 3pm."},
            {"sender": "Friend", "subject": "Weekend?", "body": "Let's work on the project later, maybe grab a beer?"}
        ]

        spam_msgs = [
            {"sender": "Lottery", "subject": "YOU WON!", "body": "You won a lottery claim now. Click here to claim your prize."},
            {"sender": "Cheap Meds", "subject": "Free money", "body": "Free money click here to get your pharmacy discount."},
            {"sender": "Nigerian Prince", "subject": "Investment", "body": "Congratulations you have been selected for this investment."},
            {"sender": "Winner", "subject": "Urgent prize", "body": "Urgent prize waiting for you. Verify your account."}
        ]

        is_spam = random.choice([0, 1])

        if is_spam:
            template = random.choice(spam_msgs)
        else:
            template = random.choice(normal_msgs)
        
        msg = template.copy()
        msg["id"] = str(uuid.uuid4()) # Unique ID for mock
        
        self.incoming_messages.append(msg)

    def heuristic_spam_check(self, text):
        """Checks for obvious spam keywords in Spanish/English"""
        text = text.lower()
        keywords = [
            "gana", "ganar", "premio", "felicidades", "urgente", 
            "clic aquí", "click here", "loteria", "casino", "apuesta", 
            "ecuabet", "bet", "bono", "regalo", "gratis", "free", 
            "oferta", "descuento", "banco", "verify", "verificar", 
            "cuenta bloqueada", "acción requerida", "ganaste", 
            "transferencia", "herencia", "millones", "dólares"
        ]
        
        for word in keywords:
            if word in text:
                return True
        return False

    def load_database_context(self):
        """Loads spam.csv to allow finding similar past spam messages."""
        try:
            import pandas as pd
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Load data for context comparison
            self.df = pd.read_csv("spam.csv", encoding="latin-1")[["v1", "v2"]]
            self.df.columns = ["label", "message"]
            self.spam_df = self.df[self.df["label"] == "spam"].reset_index(drop=True)
            
            # We need the vectorizer from the pipeline to transform new msgs
            self.vectorizer = self.model.named_steps["tfidf"]
            # Pre-calculate vectors for all known spam to speed up search
            self.spam_vectors = self.vectorizer.transform(self.spam_df["message"])
            
            self.has_context = True
        except Exception as e:
            print(f"Error loading context DB: {e}")
            self.has_context = False

    def find_similar_spam(self, text):
        """Finds the most similar message in the known spam database."""
        if not hasattr(self, "has_context") or not self.has_context:
            self.load_database_context()
            
        if not self.has_context:
            return None, 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            # Vectorize input
            input_vec = self.vectorizer.transform([text])
            # Compare with all spam
            similarities = cosine_similarity(input_vec, self.spam_vectors).flatten()
            # Find best match
            best_idx = similarities.argmax()
            best_score = similarities[best_idx]
            
            if best_score > 0.1: # Threshold to say "it's similar"
                return self.spam_df.iloc[best_idx]["message"], best_score
            else:
                return None, 0.0
        except:
            return None, 0.0

    def process_incoming_messages(self):
        """Classifies incoming messages using Hybrid (Heuristic + AI + DB Context) approach."""
        if not self.incoming_messages:
            return

        for msg in self.incoming_messages:
            # Dedup by ID
            is_duplicate = False
            for m in self.inbox_folder + self.spam_folder:
                if m.get('id') and msg.get('id'):
                    if m['id'] == msg['id']:
                        is_duplicate = True
                        break
            
            if is_duplicate:
                continue

            # 1. Prepare text
            text_to_analyze = f"{msg['subject']} {msg['body']}"
            
            # Analysis Metadata
            reason = []
            score = 0.0
            is_spam = False
            
            # 2. Heuristic Check
            if self.heuristic_spam_check(text_to_analyze):
                is_spam = True
                score = 1.0
                reason.append("Palabra clave sospechosa detectada (Ecuabet, Gana, etc.)")

            # 3. AI Model Check (Probability)
            try:
                # Get probability of being spam (class 1)
                probs = self.model.predict_proba([text_to_analyze])[0]
                ai_spam_score = probs[1] # Probability of spam
                
                # If heuristic didn't catch it, trust the model score
                if not is_spam:
                    score = ai_spam_score
                    if score > 0.5: # User adjustable threshold technically
                        is_spam = True
                        reason.append(f"IA detecta patrones de spam ({int(score*100)}% confianza)")
                else:
                    reason.append(f"IA confirma sospecha ({int(ai_spam_score*100)}%)")
                    
            except:
                # Model failed?
                pass

            # 4. Database Context (Similarity)
            similar_msg, sim_score = self.find_similar_spam(text_to_analyze)
            if similar_msg:
                reason.append(f"Similar a spam conocido en BD ({int(sim_score*100)}% similitud)")
                # If very similar, boost score/decision
                if sim_score > 0.3 and not is_spam:
                    is_spam = True
                    score = max(score, 0.8) # Force high confidence

            # Attach intelligence to message
            msg["spam_score"] = score
            msg["spam_reason"] = " | ".join(reason) if reason else "Parece legitimo"
            msg["similar_spam"] = similar_msg if similar_msg else "Ninguno"

            if is_spam:
                self.spam_folder.append(msg)
            else:
                self.inbox_folder.append(msg)

        self.incoming_messages.clear()
