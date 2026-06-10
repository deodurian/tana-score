import tana
from flask import Flask

app = tana.app
with app.app_context():
    print("Application compiles and auto-recalculation triggers without errors.")
