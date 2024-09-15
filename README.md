# All in One Hospital Agent

This project serves as an integrated platform for managing hospital activities, including appointment booking, doctor management, and administrative control.

## How to Run Locally

```bash
git clone <repository-url>
cd <repository-directory>

pip install -r requirements.txt
### connect to local mysql server.
python3 database.py
streamlit run Welcome.py

set up Mongodb server:
mac: brew services start mongodb-community
windows:
net start MongoDB
cd C:\Program Files\MongoDB\Server\{version}\bin
mongod --dbpath "C:\data\db"


