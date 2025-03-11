from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import json
import os
import datetime as dt
from dataclasses import dataclass, asdict
from portfolio_manager import PortfolioManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'delta-neutral-dashboard-secret-key'

# Data storage path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, 'portfolio_data.json')

# Initialize the portfolio manager
portfolio_manager = PortfolioManager(DATA_FILE)

@app.route('/')
def index():
    """Render dashboard homepage"""
    summary = portfolio_manager.get_summary()
    return render_template('index.html', summary=summary)

@app.route('/positions')
def positions():
    """Show all positions page"""
    return render_template('positions.html', 
                          options=portfolio_manager.options,
                          underlying=portfolio_manager.underlying)

@app.route('/settings')
def settings():
    """Settings page"""
    settings = portfolio_manager.get_settings()
    return render_template('settings.html', settings=settings)

@app.route('/api/summary')
def api_summary():
    """API endpoint for portfolio summary"""
    return jsonify(portfolio_manager.get_summary())

@app.route('/api/options', methods=['GET', 'POST', 'DELETE'])
def api_options():
    """API endpoint for options data"""
    if request.method == 'GET':
        return jsonify(portfolio_manager.get_options())
    
    elif request.method == 'POST':
        try:
            data = request.json
            portfolio_manager.add_option(data)
            return jsonify({"status": "success", "message": "Option added successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    elif request.method == 'DELETE':
        try:
            option_id = request.json.get('id')
            portfolio_manager.remove_option(option_id)
            return jsonify({"status": "success", "message": "Option removed successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

@app.route('/api/underlying', methods=['GET', 'POST', 'DELETE'])
def api_underlying():
    """API endpoint for underlying positions"""
    if request.method == 'GET':
        return jsonify(portfolio_manager.get_underlying())
    
    elif request.method == 'POST':
        try:
            data = request.json
            portfolio_manager.add_underlying(data)
            return jsonify({"status": "success", "message": "Position added successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    elif request.method == 'DELETE':
        try:
            position_id = request.json.get('id')
            portfolio_manager.remove_underlying(position_id)
            return jsonify({"status": "success", "message": "Position removed successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

@app.route('/api/hedge')
def api_hedge_recommendation():
    """API endpoint for hedge recommendations"""
    return jsonify(portfolio_manager.get_hedge_recommendation())

@app.route('/api/settings', methods=['POST'])
def api_settings():
    """API endpoint for updating settings"""
    try:
        data = request.json
        portfolio_manager.update_settings(data)
        return jsonify({"status": "success", "message": "Settings updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
