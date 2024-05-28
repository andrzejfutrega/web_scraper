from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import pymongo
from datetime import date
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)
offers = None

client = pymongo.MongoClient("mongodb://mongodb:27017/")
db = client["projekt"]
signals_collection = db["scraping_signals"]

def wait_for_completion(signal_id, event):
    global offers
    while True:
        signal = signals_collection.find_one({"_id": signal_id, "status": "completed"})
        if signal:
            keyword = signal["keyword"]
            location = signal["location"]
            date = signal["date"]
            coll = db[f"search:{keyword}, {location}, {date}"]
            offers = list(coll.find())
            
            signals_collection.delete_one({"_id": signal_id})
            event.set() 
            break
        time.sleep(1)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']
        location = request.form['location']
        
        
        signal_id = signals_collection.insert_one({"keyword": keyword, "location": location, "date": str(date.today()), "status": "pending"}).inserted_id
        
       
        event = threading.Event()
        
        
        threading.Thread(target=wait_for_completion, args=(signal_id, event)).start()
        
        
        event.wait()
        
        return redirect(url_for('success', signal_id=signal_id))

    return render_template('index.html')

@app.route('/success/<signal_id>')
def success(signal_id):
    return render_template('success.html', signal_id=signal_id, offers = offers)

@app.route('/search_history')
def search_history():
    search_info = []
    
    search_collections = [coll for coll in db.list_collection_names() if coll.startswith("search")]
    for coll_name in search_collections:
        
        parts = coll_name.split(',')
        
        keyword = parts[0].split(':')[1].strip()
        location = parts[1].strip()
        date = parts[2].strip()
        
        coll = db[coll_name]
        num_offers = coll.count_documents({})
        search_info.append({"keyword": keyword, "location": location, "date": date, "offers": num_offers})

    return render_template('search_history.html', search_info=search_info)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
