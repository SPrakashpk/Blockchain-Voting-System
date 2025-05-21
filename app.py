from flask import Flask, render_template, request, redirect, url_for, flash, session
from web3 import Web3
import face_recognition
import os
import sqlite3
import json
import cv2

app = Flask(__name__)
app.secret_key = 'secret_key'
DATABASE = 'voting.db'

# ---------------------
# Blockchain connection
# ---------------------
GANACHE_URL = "http://127.0.0.1:7545"
PRIVATE_KEY = "0xe2f9da663f6d03534c85752ef470ea38a2564f7b59e7ea2cd5e165753b262c65"
ACCOUNT = "0xfc207B92b9e01adf4E89cb3ec6d40E4CE190326e"

w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

with open("contract_info.json", "r") as f:
    contract_info = json.load(f)

abi = contract_info["abi"]
address = contract_info["address"]
contract = w3.eth.contract(address=address, abi=abi)

# ---------------------
# SQLite DB setup
# ---------------------
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voters (
                voterid TEXT PRIMARY KEY,
                password TEXT
            )
        ''')

# ---------------------
# Routes
# ---------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('voterid', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            flash("Admin login successful!", "success")
            return redirect(url_for('result'))
        else:
            flash("Invalid admin credentials!", "danger")
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        voterid = request.form['voterid']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM voters WHERE voterid = ?", (voterid,))
            if cur.fetchone():
                flash("Voter ID already exists!", "danger")
                return redirect(url_for('user_register'))
            cur.execute("INSERT INTO voters (voterid, password) VALUES (?, ?)", (voterid, password))
            conn.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('user_login'))
    return render_template('user_register.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        voterid = request.form['voterid']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM voters WHERE voterid = ? AND password = ?", (voterid, password))
            if cur.fetchone():
                session['voterid'] = voterid
                flash("Login successful!", "success")
                return redirect(url_for('vote'))
            else:
                flash("Invalid credentials!", "danger")
    return render_template('user_login.html')

@app.route('/user')
def user_face_recognition():
    if match_face_with_dataset():
        flash("Face matched with dataset successfully!", "success")
        return redirect(url_for('user_register'))
    else:
        flash("Face not recognized!", "danger")
        return redirect(url_for('index'))

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    candidates = contract.functions.getCandidates().call()
    voterid = session.get('voterid')

    if not voterid:
        flash("You must log in first.", "warning")
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        candidate_index = request.form.get('candidate_index')
        if candidate_index is None:
            flash("Please select a candidate!", "danger")
            return render_template('vote.html', candidates=candidates)

        if contract.functions.hasVotedCheck(voterid).call():
            flash("You have already voted!", "danger")
            return render_template('vote.html', candidates=candidates)

        try:
            nonce = w3.eth.get_transaction_count(ACCOUNT)
            tx = contract.functions.vote(voterid, int(candidate_index)).build_transaction({
                'from': ACCOUNT,
                'gas': 2000000,
                'gasPrice': w3.to_wei('1', 'gwei'),
                'nonce': nonce
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash)
            flash("Vote cast successfully!", "success")
        except Exception as e:
            flash(f"Error casting vote: {str(e)}", "danger")

    return render_template('vote.html', candidates=candidates)

@app.route('/result')
def result():
    candidates = contract.functions.getCandidates().call()
    results_data = []
    for i, name in enumerate(candidates):
        count = contract.functions.getVoteCount(i).call()
        results_data.append((name, count))
    return render_template('result.html', results=results_data)

# ---------------------
# Face Recognition
# ---------------------
def match_face_with_dataset():
    known_encodings = []
    known_names = []
    dataset_dir = 'dataset'

    for filename in os.listdir(dataset_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(dataset_dir, filename)
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])

    cap = cv2.VideoCapture(0)
    face_matched = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        current_faces = face_recognition.face_encodings(rgb_frame)

        for face_encoding in current_faces:
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            if len(distances) == 0:
                continue
            best_match_index = distances.argmin()
            if distances[best_match_index] < 0.45:
                face_matched = True
                break

        cv2.imshow('Face Recognition - Press Q to Quit', frame)
        if face_matched or cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return face_matched

# ---------------------
# Main
# ---------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
