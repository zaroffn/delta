import json
import os
import uuid
import datetime as dt
from typing import Dict, List, Any

class PortfolioManager:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.options = []  # List of option positions
        self.underlying = []  # List of underlying positions
        self.settings = {
            "contracts_per_option": 100,  # Standard options contract size
            "currency": "USD",
            "transaction_fee": 0.75,  # Fee per transaction
        }
        
        # Load data if it exists
        self._load_data()
    
    def _load_data(self) -> None:
        """Load portfolio data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.options = data.get('options', [])
                self.underlying = data.get('underlying', [])
                self.settings = data.get('settings', self.settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading data: {e}")
    
    def _save_data(self) -> None:
        """Save portfolio data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'options': self.options,
                    'underlying': self.underlying,
                    'settings': self.settings
                }, f, indent=4)
        except IOError as e:
            print(f"Error saving data: {e}")
    
    def add_option(self, option_data: Dict) -> None:
        """Add a new option position to the portfolio"""
        # Generate a unique ID for the option
        option_data['id'] = str(uuid.uuid4())
        option_data['date_added'] = dt.datetime.now().isoformat()
        
        # Calculate net delta contribution
        delta = float(option_data['delta'])
        quantity = int(option_data['quantity'])
        
        # For short positions, reverse the delta
        if option_data['position_type'] == 'short':
            delta = -delta
        
        # Net delta = delta * quantity * contracts_per_option
        option_data['net_delta'] = delta * quantity * self.settings['contracts_per_option']
        
        self.options.append(option_data)
        self._save_data()
    
    def remove_option(self, option_id: str) -> None:
        """Remove an option position from the portfolio"""
        self.options = [opt for opt in self.options if opt['id'] != option_id]
        self._save_data()
    
    def add_underlying(self, position_data: Dict) -> None:
        """Add an underlying position to the portfolio"""
        # Generate a unique ID for the position
        position_data['id'] = str(uuid.uuid4())
        position_data['date_added'] = dt.datetime.now().isoformat()
        
        # Calculate net delta contribution (1 for long, -1 for short)
        quantity = int(position_data['quantity'])
        delta = 1 if position_data['position_type'] == 'long' else -1
        position_data['net_delta'] = delta * quantity
        
        self.underlying.append(position_data)
        self._save_data()
    
    def remove_underlying(self, position_id: str) -> None:
        """Remove an underlying position from the portfolio"""
        self.underlying = [pos for pos in self.underlying if pos['id'] != position_id]
        self._save_data()
    
    def get_options(self) -> List[Dict]:
        """Get all option positions"""
        return self.options
    
    def get_underlying(self) -> List[Dict]:
        """Get all underlying positions"""
        return self.underlying
    
    def get_total_delta(self) -> float:
        """Calculate the total delta of the portfolio"""
        option_delta = sum(opt.get('net_delta', 0) for opt in self.options)
        underlying_delta = sum(pos.get('net_delta', 0) for pos in self.underlying)
        return option_delta + underlying_delta
    
    def get_summary(self) -> Dict:
        """Get a summary of the portfolio"""
        # Calculate total delta
        total_delta = self.get_total_delta()
        
        # Calculate option positions value
        option_value = sum(
            float(opt['price']) * int(opt['quantity']) * self.settings['contracts_per_option']
            for opt in self.options
        )
        
        # Calculate underlying positions value
        underlying_value = sum(
            float(pos['price']) * int(pos['quantity'])
            for pos in self.underlying
        )
        
        # Count positions
        option_count = len(self.options)
        underlying_count = len(self.underlying)
        
        return {
            "total_delta": total_delta,
            "is_delta_neutral": abs(total_delta) < 1.0,  # Consider "close enough" to delta neutral
            "option_value": option_value,
            "underlying_value": underlying_value,
            "total_value": option_value + underlying_value,
            "option_count": option_count,
            "underlying_count": underlying_count
        }
    
    def get_hedge_recommendation(self) -> Dict:
        """Calculate the recommended hedge to achieve delta neutrality"""
        total_delta = self.get_total_delta()
        
        # If already delta neutral or close, no action needed
        if abs(total_delta) < 1.0:
            return {
                "action": "none",
                "message": "Portfolio is already delta neutral",
                "current_delta": total_delta
            }
        
        # If portfolio has positive delta, we need to short the underlying
        if total_delta > 0:
            return {
                "action": "sell",
                "quantity": round(total_delta),
                "message": f"Sell {round(total_delta)} shares of the underlying to achieve delta neutrality",
                "current_delta": total_delta
            }
        else:
            # If portfolio has negative delta, we need to buy the underlying
            return {
                "action": "buy",
                "quantity": round(abs(total_delta)),
                "message": f"Buy {round(abs(total_delta))} shares of the underlying to achieve delta neutrality",
                "current_delta": total_delta
            }
    
    def get_settings(self) -> Dict:
        """Get the current settings"""
        return self.settings
    
    def update_settings(self, new_settings: Dict) -> None:
        """Update settings"""
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value
        
        # Recalculate deltas if contract size changed
        if 'contracts_per_option' in new_settings:
            self._recalculate_option_deltas()
        
        self._save_data()
    
    def _recalculate_option_deltas(self) -> None:
        """Recalculate net delta for all options based on current settings"""
        for option in self.options:
            delta = float(option['delta'])
            quantity = int(option['quantity'])
            
            # For short positions, reverse the delta
            if option['position_type'] == 'short':
                delta = -delta
            
            # Net delta = delta * quantity * contracts_per_option
            option['net_delta'] = delta * quantity * self.settings['contracts_per_option']
